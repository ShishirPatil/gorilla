import csv
from collections import namedtuple
from datetime import datetime
from typing import List

import typer
from bfcl._llm_response_generation import main as generation_main
from bfcl.constant import DOTENV_PATH, RESULT_PATH, SCORE_PATH, TEST_COLLECTION_MAPPING
from bfcl.eval_checker import eval_runner
from bfcl.model_handler.handler_map import HANDLER_MAP
from dotenv import load_dotenv
from tabulate import tabulate


class ExecutionOrderGroup(typer.core.TyperGroup):
    def list_commands(self, ctx):
        return [
            "models",
            "test-categories",
            "generate",
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
        [
            (category, "\n".join(test for test in tests))
            for category, tests in TEST_COLLECTION_MAPPING.items()
        ],
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
        [[model] for model in HANDLER_MAP.keys()],
        tablefmt="plain",
        colalign=("left",),
    )
    print(table)


@cli.command()
def generate(
    model: List[str] = typer.Option(
        ["gorilla-openfunctions-v2"], help="A list of model names to evaluate."
    ),
    test_category: List[str] = typer.Option(
        ["all"], help="A list of test categories to run the evaluation on."
    ),
    temperature: float = typer.Option(
        0.001, help="The temperature parameter for the model."
    ),
    include_input_log: bool = typer.Option(
        False,
        "--include-input-log",
        help="Include the fully-transformed input to the model inference endpoint in the inference log; only relevant for debugging input integrity and format.",
    ),
    include_state_log: bool = typer.Option(
        False,
        "--include-state-log",
        help="Include info about the state of each API system after each turn in the inference log; only relevant for multi-turn categories.",
    ),
    num_gpus: int = typer.Option(1, help="The number of GPUs to use."),
    num_threads: int = typer.Option(1, help="The number of threads to use."),
    gpu_memory_utilization: float = typer.Option(
        0.9, help="The GPU memory utilization."
    ),
    backend: str = typer.Option(
        "vllm", help="The backend to use for the model."
    ),
):
    """
    Generate the LLM response for one or more models on a test-category (same as openfunctions_evaluation.py).
    """
    generationArgs = namedtuple(
        "generationArgs",
        [
            "model",
            "test_category",
            "temperature",
            "include_input_log",
            "include_state_log",
            "num_gpus",
            "num_threads",
            "gpu_memory_utilization",
            "backend",
        ],
    )

    load_dotenv(dotenv_path=DOTENV_PATH, verbose=True, override=True)  # Load the .env file
    generation_main(
        generationArgs(
            model=model,
            test_category=test_category,
            temperature=temperature,
            include_input_log=include_input_log,
            include_state_log=include_state_log,
            num_gpus=num_gpus,
            num_threads=num_threads,
            gpu_memory_utilization=gpu_memory_utilization,
            backend=backend,
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
        if name not in HANDLER_MAP:
            candidate = name.replace("_", "/")
            if candidate in HANDLER_MAP:
                return candidate
            print(f"Unknown model name: {name}")
        return name

    result_dir = RESULT_PATH

    results_data = []
    for dir in result_dir.iterdir():
        # Check if it is a directory and not a file
        if not dir.is_dir():
            continue

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
    model: List[str] = typer.Option(None, help="A list of model names to evaluate."),
    test_category: List[str] = typer.Option(
        None, help="A list of test categories to run the evaluation on."
    ),
    api_sanity_check: bool = typer.Option(
        False,
        "--api-sanity-check",
        "-c",
        help="Perform the REST API status sanity check before running the evaluation.",
    ),
):
    """
    Evaluate results from run of one or more models on a test-category (same as eval_runner.py).
    """

    load_dotenv(dotenv_path=DOTENV_PATH, verbose=True, override=True)  # Load the .env file
    eval_runner.main(model, test_category, api_sanity_check)


@cli.command()
def scores():
    """
    Display the leaderboard.
    """

    def truncate(text, length=22):
        return (text[:length] + "...") if len(text) > length else text

    # files = ["./score/data_non_live.csv", "./score/data_live.csv", "./score/data_overall.csv"]
    file = SCORE_PATH / "data_overall.csv"

    selected_columns = [
        "Rank",
        "Model",
        "Overall Acc",
        "Non-Live AST Acc",
        "Non-Live Exec Acc",
        "Live Acc",
        "Multi Turn Acc",
        "Relevance Detection",
        "Irrelevance Detection",
    ]

    if file.exists():
        with open(file, newline="") as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # Read the header row
            column_indices = [headers.index(col) for col in selected_columns]
            data = [
                [row[i] for i in column_indices] for row in reader
            ]  # Read the rest of the data
            selected_columns = selected_columns[:-2] + ["Relevance", "Irrelevance"]  # Shorten the column names
            print(tabulate(data, headers=selected_columns, tablefmt="grid"))
    else:
        print(f"\nFile {file} not found.\n")


if __name__ == "__main__":
    cli()
