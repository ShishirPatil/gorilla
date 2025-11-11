from __future__ import annotations
from typing import Optional, Dict, Any, Iterable
import atexit, logging
import sys, threading
import builtins
from rich.console import Console
from rich.live import Live
from rich.progress import (
    Progress, BarColumn, TextColumn,
    TimeElapsedColumn, TimeRemainingColumn,
    TaskID, SpinnerColumn, MofNCompleteColumn
)
from rich.logging import RichHandler

_TL = threading.local()
_original_stdout = None
_original_stderr = None

_console: Optional[Console] = None
_progress: Optional[Progress] = None
_live: Optional[Live] = None
_tasks: Dict[str, TaskID] = {}

def console() -> Console:
    global _console
    if _console is None:
        _console = Console(highlight=False, soft_wrap=False)
    return _console

def set_description(name: str, description: str):
    tid = _tasks.get(name)
    if tid is None:
        tid = create_task(name, total=None, scope="EVAL", description=description)
    progress().update(tid, description=description)


def progress() -> Progress:
    global _progress
    if _progress is None:
        _progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.fields[scope]}[/]"),
            TextColumn("{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            expand=True,
            transient=False, 
        )
    return _progress

def _ensure_live():
    global _live
    if _live is None:
        _live = Live(progress(), console=console(), refresh_per_second=18)
        _live.start()

def init_logging(level=logging.INFO):
    logging.basicConfig(
        level=level, format="%(message)s",
        handlers=[RichHandler(console=console(), markup=True, show_time=True, show_path=False)]
    )

def start():
    _ensure_live()

def stop():
    global _live
    if _live is not None:
        _live.stop()
        _live = None

atexit.register(stop)

def log(*args: Any, **kwargs: Any):
    console().log(*args, **kwargs)

def create_task(name: str, total: int | None = None, *, scope: str = "TASK", description: str = "") -> TaskID:
    _ensure_live()
    if name in _tasks:
        return _tasks[name]
    tid = progress().add_task(description or name, total=total, scope=scope)
    _tasks[name] = tid
    return tid

def update_total(name: str, total: int):
    tid = _tasks[name]
    progress().update(tid, total=total)

def advance(name: str, n: int = 1):
    tid = _tasks[name]
    progress().advance(tid, n)

def finish(name: str):
    tid = _tasks.get(name)
    if tid is None: return
    task = progress().tasks[tid]
    if task.total is not None:
        progress().update(tid, completed=task.total)
    else:
        progress().remove_task(tid)

def track_iter(name: str, it: Iterable, *, scope: str = "TASK", total: int | None = None, description: str = ""):
    tid = create_task(name, total=total, scope=scope, description=description)
    for x in it:
        yield x
        progress().advance(tid, 1)

import sys

class _StreamProxy:
    def __init__(self, which="stdout"):
        self.which = which

    def write(self, s):
        if not s or s == "\n":
            return
        if getattr(_TL, "in_write", False):
            target = _original_stdout if self.which == "stdout" else _original_stderr
            if target:
                target.write(s)
                target.flush()
            return

        _TL.in_write = True
        try:
            console().print(s, end="")
        finally:
            _TL.in_write = False

    def flush(self):
        target = _original_stdout if self.which == "stdout" else _original_stderr
        if target:
            try:
                target.flush()
            except Exception:
                pass

def hijack_std_streams(enable: bool = True):
    global _original_stdout, _original_stderr
    if enable:
        if _original_stdout is None:
            _original_stdout = sys.stdout
        if _original_stderr is None:
            _original_stderr = sys.stderr
        sys.stdout = _StreamProxy("stdout")  
        sys.stderr = _StreamProxy("stderr") 
    else:
        if _original_stdout is not None:
            sys.stdout = _original_stdout
        if _original_stderr is not None:
            sys.stderr = _original_stderr

_original_print = builtins.print

def _rich_print(*args, **kwargs):
    sep  = kwargs.pop("sep", " ")
    end  = kwargs.pop("end", "\n")
    file = kwargs.pop("file", None)
    flush= kwargs.pop("flush", False)

    import sys as _sys
    if file not in (None, _sys.stdout, _sys.stderr):
        return _original_print(*args, sep=sep, end=end, file=file, flush=flush, **kwargs)

    text = sep.join(str(a) for a in args) + end
    console().print(text, end="")
    if flush:
        try:
            console().file.flush()
        except Exception:
            pass

def hijack_print(enable: bool = True):
    global _original_print
    if enable:
        builtins.print = _rich_print  
    else:
        builtins.print = _original_print  
