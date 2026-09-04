from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CLI_HELP_WITHOUT_SOUNDFILE = """
import importlib.abc
import runpy
import sys


class BlockSoundfileImport(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == "soundfile":
            raise ModuleNotFoundError("No module named 'soundfile'", name=fullname)
        return None


sys.meta_path.insert(0, BlockSoundfileImport())
sys.argv = ["bfcl", "--help"]
try:
    runpy.run_module("bfcl_eval.__main__", run_name="__main__", alter_sys=True)
except SystemExit as exc:
    if exc.code not in (None, 0):
        raise

if "qwen_agent" in sys.modules:
    raise AssertionError("bfcl --help imported qwen_agent")
"""


class CliImportTests(unittest.TestCase):
    def test_help_does_not_import_qwen_agent_or_require_audio_dependencies(
        self,
    ) -> None:
        result = subprocess.run(
            [sys.executable, "-c", CLI_HELP_WITHOUT_SOUNDFILE],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
