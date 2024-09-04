from typing import List
from collections import namedtuple
import typer
from bfcl._openfunctions_evaluation import main as openfunctions_main
from bfcl.eval_checker import eval_runner
import os

cli = typer.Typer(
    context_settings=dict(help_option_names=["-h", "--help"]),
    no_args_is_help=True,
)


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


if __name__ == "__main__":
    cli()
