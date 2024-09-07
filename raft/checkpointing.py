from dataclasses import dataclass
from pathlib import Path
from typing import List
from datasets import Dataset, concatenate_datasets
import logging
import shutil

logger = logging.getLogger("raft")

@dataclass
class Checkpoint:
    path: Path
    num: int

    def load(self) -> Dataset:
        return Dataset.load_from_disk(self.path)

    def __lt__(self, other: 'Checkpoint') -> bool:
        return self.num < other.num

    def __eq__(self, other: 'Checkpoint') -> bool:
        return self.num == other.num

    def __hash__(self) -> int:
        return hash(self.num)

class Checkpointing:

    def __init__(self, checkpoints_dir: Path) -> None:
        self.checkpoints_dir = checkpoints_dir

    def missing_checkpoints(self, num) -> List[int]:
        return [n for n in range(0, num) if not (self.checkpoints_dir / f"checkpoint-{n}").exists()]

    def save_checkpoint(self, ds: Dataset, num: int):
        checkpoint_path = self.checkpoints_dir / ("checkpoint-" + str(num))
        ds.save_to_disk(checkpoint_path)

    def load_checkpoint(self, num: int):
        checkpoint_path = self.checkpoints_dir / ("checkpoint-" + str(num))
        if checkpoint_path.exists():
            return Dataset.load_from_disk(checkpoint_path)
        return None

    def get_checkpoints(self) -> List[Checkpoint]:
        checkpoints = []
        if not self.checkpoints_dir.exists():
            return checkpoints
        for dir_path in self.checkpoints_dir.iterdir():
            if dir_path.is_dir() and dir_path.name.startswith("checkpoint-"):
                num = int(dir_path.name.split("-")[1])
                checkpoints.append(Checkpoint(dir_path, num))
        return checkpoints

    def has_checkpoints(self) -> bool:
        return len(self.get_checkpoints()) > 0

    def collect_checkpoints(self) -> Dataset:
        ds_list = list([checkpoint.load() for checkpoint in self.get_checkpoints()])
        ds = concatenate_datasets(ds_list)
        return ds

    def delete_checkpoints(self):
        shutil.rmtree(self.checkpoints_dir)

def checkpointed(checkpointing: Checkpointing):
    def wrapped(func):
        def wrapper(chunk_id, *args, **kwargs):
            ds = checkpointing.load_checkpoint(chunk_id)
            if ds:
                return ds
            ds = func(chunk_id=chunk_id, *args, **kwargs)
            if ds.num_rows > 0:
                checkpointing.save_checkpoint(ds, chunk_id)
            return ds
        return wrapper
    return wrapped
