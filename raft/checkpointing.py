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
        self.checkpoints_state_path = checkpoints_dir / "checkpoint.txt"
        logger.info(f"Using checkpoint file {self.checkpoints_state_path}")

    def load_checkpoint_state(self) -> int:
        if self.checkpoints_state_path.exists():
            with open(self.checkpoints_state_path, "r") as f:
                return int(f.read())
        return 0

    def save_checkpoint_state(self, state):
        with open(self.checkpoints_state_path, 'w') as f:
            f.write(str(state))

    def save_checkpoint(self, ds: Dataset, num: int):
        checkpoint_path = self.checkpoints_dir / ("checkpoint-" + str(num))
        ds.save_to_disk(checkpoint_path)

    def get_checkpoints(self) -> List[Checkpoint]:
        checkpoints = []
        for dir_path in self.checkpoints_dir.iterdir():
            if dir_path.is_dir() and dir_path.name.startswith("checkpoint-"):
                num = int(dir_path.name.split("-")[1])
                checkpoints.append(Checkpoint(dir_path, num))
        return checkpoints

    def collect_checkpoints(self) -> List[Dataset]:
        ds_list = list([checkpoint.load() for checkpoint in self.get_checkpoints()])
        ds = concatenate_datasets(ds_list)
        return ds

    def delete_checkpoints(self):
        shutil.rmtree(self.checkpoints_dir)
