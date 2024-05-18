from pathlib import Path
from typing import List
from datasets import Dataset, concatenate_datasets
import logging

logger = logging.getLogger("raft")

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

    def collect_checkpoints(self) -> List[Dataset]:
        ds_list = []

        for dir_path in self.checkpoints_dir.iterdir():
            if dir_path.is_dir() and dir_path.name.startswith("checkpoint-"):
                for f in dir_path.iterdir():
                    if f.is_file() and f.suffix == ".arrow":
                        ds_list.append(Dataset.from_file(str(f)))
        ds = concatenate_datasets(ds_list)
        return ds
