from abc import ABC, abstractmethod
from pathlib import Path

from bfcl_eval.utils import extract_test_category_from_id, is_first_memory_prereq_entry


class MemoryAPI(ABC):
    """
    A class that provides APIs to manage short-term and long-term memory data in a key-value format.
    """

    def __init__(self):
        self.core_memory = {}
        self.archival_memory = {}
        self.snapshot_folder: Path | None = None

    def _load_scenario(self, initial_config: dict, long_context: bool = False):
        # We don't care about the long_context parameter here
        # It's there to match the signature of functions in the multi-turn evaluation code
        model_result_dir: Path = initial_config["model_result_dir"]
        self.test_id: str = initial_config["test_id"]
        self.scenario: str = initial_config["scenario"]
        test_category: str = extract_test_category_from_id(self.test_id)

        # TODO: use helper function to assemble the path
        self.snapshot_folder = model_result_dir / "memory_snapshot" / test_category
        self.snapshot_folder.mkdir(parents=True, exist_ok=True)
        self.latest_snapshot_file = self.snapshot_folder / f"{self.scenario}_final.json"

        if not is_first_memory_prereq_entry(self.test_id):
            assert (
                self.latest_snapshot_file.exists()
            ), f"Not first memory entry, but no snapshot file found in this path: {self.latest_snapshot_file}"

    @abstractmethod
    def _flush_memory_to_local_file(self):
        pass

    @abstractmethod
    def _dump_core_memory_to_context(self) -> str:
        pass