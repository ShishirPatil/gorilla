"""Regression tests for malformed Falcon tool calls in irrelevance scoring.

Load only the functions under test so this suite needs no inference dependencies.
"""

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


PACKAGE = Path(__file__).resolve().parents[1] / "bfcl_eval"


def _load_nodes(path, names, namespace):
    source = ast.parse(path.read_text())
    nodes = [node for node in source.body if getattr(node, "name", None) in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)


@pytest.fixture
def score_falcon_response():
    namespace = {
        "BaseHandler": object,
        "OSSHandler": object,
        "ReturnFormat": SimpleNamespace(PYTHON="python"),
        "json": json,
        "override": lambda function: function,
    }
    _load_nodes(
        PACKAGE / "model_handler/exceptions.py", {"MalformedToolCallError"}, namespace
    )
    _load_nodes(
        PACKAGE / "utils.py",
        {"is_function_calling_format_output", "is_empty_output"},
        namespace,
    )
    _load_nodes(
        PACKAGE / "model_handler/local_inference/falcon_fc.py",
        {"Falcon3FCHandler"},
        namespace,
    )
    _load_nodes(
        PACKAGE / "eval_checker/eval_runner.py",
        {"_evaluate_single_relevance_entry"},
        namespace,
    )
    handler = namespace["Falcon3FCHandler"].__new__(namespace["Falcon3FCHandler"])

    def score(response, category="irrelevance"):
        return namespace["_evaluate_single_relevance_entry"](
            handler, "case-1", response, {}, "Falcon3-1B-Instruct (FC)", category
        )

    return score


@pytest.mark.parametrize("category", ["irrelevance", "live_irrelevance"])
def test_malformed_tool_call_is_not_a_correct_abstention(score_falcon_response, category):
    response = '<tool_call>\n<tool_call name="math.solve" arguments={"a": 1}/>\n</tool_call>'

    result = score_falcon_response(response, category)

    assert result["valid"] is False


def test_malformed_tool_call_tag_is_not_a_correct_abstention(score_falcon_response):
    response = '<tool_call name="math.solve" arguments={"a": 1}/>'

    assert score_falcon_response(response)["valid"] is False


def test_tool_call_with_invalid_arguments_is_not_a_correct_abstention(
    score_falcon_response,
):
    response = '<tool_call>{"name": "math.solve", "arguments": []}</tool_call>'

    assert score_falcon_response(response)["valid"] is False


def test_prose_abstention_remains_correct(score_falcon_response):
    assert score_falcon_response("I cannot use any of these tools.") == {"valid": True}


def test_empty_tool_call_list_remains_correct(score_falcon_response):
    assert score_falcon_response("<tool_call>[]</tool_call>") == {"valid": True}


def test_valid_tool_call_remains_incorrect_for_irrelevance(score_falcon_response):
    response = '<tool_call>{"name": "math.solve", "arguments": {"a": 1}}</tool_call>'

    assert score_falcon_response(response)["valid"] is False


def test_malformed_tool_call_remains_incorrect_for_relevance(score_falcon_response):
    response = '<tool_call>{"name": "math.solve", "arguments": }</tool_call>'

    assert score_falcon_response(response, "live_relevance")["valid"] is False
