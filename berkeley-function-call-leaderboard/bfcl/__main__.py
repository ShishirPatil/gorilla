from typing import List
from collections import namedtuple
import typer
from bfcl._openfunctions_evaluation import main as openfunctions_main
from bfcl.eval_checker import eval_runner
from bfcl.eval_checker.eval_runner_helper import MODEL_METADATA_MAPPING
from bfcl.eval_checker.eval_checker_constant import TEST_COLLECTION_MAPPING
import os
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
import csv


class ExecutionOrderGroup(typer.core.TyperGroup):
    def list_commands(self, ctx):
        return [
            "models",
            "test-categories",
            "run",
            "results",
            "evaluate",
            "scores",
        ]


cli = typer.Typer(
    context_settings=dict(help_option_names=["-h", "--help"]),
    no_args_is_help=True,
    cls=ExecutionOrderGroup,
)


@cli.command()
def test_categories():
    """
    List available test categories.
    """
    table = tabulate(
        [(category, "\n".join(test for test in tests)) for category, tests in TEST_COLLECTION_MAPPING.items()],
        headers=["Test category", "Test names"],
        tablefmt="grid",
    )
    print(table)


@cli.command()
def models():
    """
    List available models.
    """
    table = tabulate(
        [[model] for model in MODEL_METADATA_MAPPING],
        tablefmt="plain",
        colalign=("left",),
    )
    print(table)


@cli.command()
def run(
    model: List[str] = typer.Option(
        ["gorilla-openfunctions-v2"], help="A list of model names to evaluate."
    ),
    test_category: List[str] = typer.Option(
        ["all"], help="A list of test categories to run the evaluation on."
    ),
    api_sanity_check: bool = typer.Option(
        False,
        "--api-sanity-check",
        "-c",
        help="Perform the REST API status sanity check before running the evaluation.",
    ),
    temperature: float = typer.Option(
        0.001, help="The temperature parameter for the model."
    ),
    top_p: float = typer.Option(1.0, help="The top-p parameter for the model."),
    max_tokens: int = typer.Option(
        1200, help="The maximum number of tokens for the model."
    ),
    num_gpus: int = typer.Option(1, help="The number of GPUs to use."),
    timeout: int = typer.Option(60, help="The timeout for the model in seconds."),
    num_threads: int = typer.Option(1, help="The number of threads to use."),
    gpu_memory_utilization: float = typer.Option(
        0.9, help="The GPU memory utilization."
    ),
):
    """
    Run one or more models on a test-category (same as openfunctions_evaluation).
    """
    RunArgs = namedtuple(
        "RunArgs",
        [
            "model",
            "test_category",
            "api_sanity_check",
            "temperature",
            "top_p",
            "max_tokens",
            "num_gpus",
            "timeout",
            "num_threads",
            "gpu_memory_utilization",
        ],
    )

    openfunctions_main(
        RunArgs(
            model=model,
            test_category=test_category,
            api_sanity_check=api_sanity_check,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            num_gpus=num_gpus,
            timeout=timeout,
            num_threads=num_threads,
            gpu_memory_utilization=gpu_memory_utilization,
        )
    )


@cli.command()
def results():
    """
    List the results available for evaluation.
    """

    def display_name(name: str):
        """
        Undo the / -> _ transformation if it happened.

        Args:
            name (str): The name of the model in the result directory.

        Returns:
            str: The original name of the model.
        """
        if name not in MODEL_METADATA_MAPPING:
            candidate = name.replace("_", "/")
            if candidate in MODEL_METADATA_MAPPING:
                return candidate
            print(f"Unknown model name: {name}")
        return name

    result_dir = Path("./result")  # todo: make this configurable
    if not result_dir.exists():
        print("No results available.")
        return

    results_data = []
    for dir in result_dir.iterdir():
        results_data.append(
            (
                display_name(dir.name),
                datetime.fromtimestamp(dir.stat().st_ctime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            )
        )
    print(
        tabulate(
            results_data,
            headers=["Model name", "Creation time"],
            tablefmt="pretty",
        )
    )


@cli.command()
def evaluate(
    model: List[str] = typer.Option(..., help="A list of model names to evaluate."),
    test_category: List[str] = typer.Option(
        ..., help="A list of test categories to run the evaluation on."
    ),
    api_sanity_check: bool = typer.Option(
        False,
        "--api-sanity-check",
        "-c",
        help="Perform the REST API status sanity check before running the evaluation.",
    ),
):
    """
    Evaluate results from run of one or more models on a test-category (same as eval_runner).
    """
    # todo: make these params eval_runner_main
    eval_runner.INPUT_PATH = "./result/"
    eval_runner.PROMPT_PATH = "./data/"
    eval_runner.POSSIBLE_ANSWER_PATH = "./data/possible_answer/"
    eval_runner.OUTPUT_PATH = "./score/"

    # todo: change the eval_runner to not depend on OPENAI_API_KEY
    os.environ["OPENAI_API_KEY"] = "BOGUS"

    eval_runner.main(model, test_category, api_sanity_check)


@cli.command()
def scores():
    """
    Display the leaderboard.
    """
    def truncate(text, length=22):
        return (text[:length] + '...') if len(text) > length else text

    # files = ["./score/data_non_live.csv", "./score/data_live.csv", "./score/data_combined.csv"]
    files = ["./score/data_combined.csv"]  # todo: make ./score configurable
    for file in files:
        if os.path.exists(file):
            with open(file, newline='') as csvfile:
                reader = csv.reader(csvfile)
                headers = [truncate(header) for header in next(reader)]  # Read the header row
                data = [[truncate(cell) for cell in row] for row in reader]  # Read the rest of the data
                print(tabulate(data, headers=headers, tablefmt='grid'))
        else:
            print(f"\nFile {file} not found.\n")

if __name__ == "__main__":
    cli()
