"""Unit tests for MiniMax handler and model configuration."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Because the full BFCL dependency chain is heavy (tree-sitter, etc.),
# we test the MiniMax handler at the *source-level* to avoid import issues
# in CI environments that do not have the full set of deps installed.
# ---------------------------------------------------------------------------


# ── Test 1: Handler file parses without errors ──────────────────────────────
def test_minimax_handler_syntax():
    """minimax.py must be valid Python."""
    import ast

    handler_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "model_handler",
        "api_inference",
        "minimax.py",
    )
    with open(handler_path) as f:
        source = f.read()
    tree = ast.parse(source)
    # Verify the class is defined
    class_names = [
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    ]
    assert "MiniMaxHandler" in class_names


# ── Test 2: Handler extends the correct base class ──────────────────────────
def test_minimax_handler_inherits_openai_completions():
    """MiniMaxHandler must inherit from OpenAICompletionsHandler."""
    import ast

    handler_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "model_handler",
        "api_inference",
        "minimax.py",
    )
    with open(handler_path) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "MiniMaxHandler":
            base_names = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_names.append(base.id)
                elif isinstance(base, ast.Attribute):
                    base_names.append(base.attr)
            assert "OpenAICompletionsHandler" in base_names
            break
    else:
        pytest.fail("MiniMaxHandler class not found")


# ── Test 3: Handler sets correct base_url ────────────────────────────────────
def test_minimax_handler_base_url():
    """Handler must set the MiniMax API base URL."""
    handler_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "model_handler",
        "api_inference",
        "minimax.py",
    )
    with open(handler_path) as f:
        source = f.read()
    assert "https://api.minimax.io/v1" in source


# ── Test 4: Handler reads MINIMAX_API_KEY from environment ───────────────────
def test_minimax_handler_reads_api_key_env():
    """Handler must read the MINIMAX_API_KEY environment variable."""
    handler_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "model_handler",
        "api_inference",
        "minimax.py",
    )
    with open(handler_path) as f:
        source = f.read()
    assert "MINIMAX_API_KEY" in source


# ── Test 5: Model config registers FC and Prompt entries ─────────────────────
def test_model_config_has_minimax_entries():
    """model_config.py must contain MiniMax-M2.5-FC and MiniMax-M2.5 entries."""
    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "constants",
        "model_config.py",
    )
    with open(config_path) as f:
        source = f.read()
    assert '"MiniMax-M2.5-FC"' in source
    assert '"MiniMax-M2.5"' in source


# ── Test 6: Model config imports MiniMaxHandler ──────────────────────────────
def test_model_config_imports_minimax_handler():
    """model_config.py must import MiniMaxHandler."""
    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "constants",
        "model_config.py",
    )
    with open(config_path) as f:
        source = f.read()
    assert "from bfcl_eval.model_handler.api_inference.minimax import MiniMaxHandler" in source


# ── Test 7: FC entry has is_fc_model=True ────────────────────────────────────
def test_model_config_fc_entry_is_fc():
    """The FC model config entry must have is_fc_model=True."""
    import ast

    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "constants",
        "model_config.py",
    )
    with open(config_path) as f:
        source = f.read()
    # Check that the FC entry has is_fc_model=True
    # Find the FC entry block
    fc_start = source.find('"MiniMax-M2.5-FC"')
    fc_end = source.find("),", fc_start)
    fc_block = source[fc_start:fc_end]
    assert "is_fc_model=True" in fc_block


# ── Test 8: Prompt entry has is_fc_model=False ───────────────────────────────
def test_model_config_prompt_entry_is_not_fc():
    """The Prompt model config entry must have is_fc_model=False."""
    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "constants",
        "model_config.py",
    )
    with open(config_path) as f:
        source = f.read()
    # Find the Prompt entry (not the FC one)
    # The prompt entry key is just "MiniMax-M2.5" (without -FC)
    prompt_start = source.find('"MiniMax-M2.5":')
    # Make sure we didn't find the FC entry
    if prompt_start == -1:
        pytest.fail("MiniMax-M2.5 prompt entry not found")
    prompt_end = source.find("),", prompt_start)
    prompt_block = source[prompt_start:prompt_end]
    assert "is_fc_model=False" in prompt_block


# ── Test 9: Supported models list includes MiniMax entries ───────────────────
def test_supported_models_includes_minimax():
    """supported_models.py must list MiniMax model IDs."""
    models_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "constants",
        "supported_models.py",
    )
    with open(models_path) as f:
        source = f.read()
    assert '"MiniMax-M2.5-FC"' in source
    assert '"MiniMax-M2.5"' in source


# ── Test 10: SUPPORTED_MODELS.md documents MiniMax ───────────────────────────
def test_supported_models_md_documents_minimax():
    """SUPPORTED_MODELS.md must have MiniMax rows."""
    md_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "SUPPORTED_MODELS.md",
    )
    with open(md_path) as f:
        content = f.read()
    assert "MiniMax-M2.5" in content
    assert "MiniMax-M2.5-FC" in content
    assert "| MiniMax" in content


# ── Test 11: Model config specifies correct org ─────────────────────────────
def test_model_config_org_is_minimax():
    """Model config org field should be 'MiniMax'."""
    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "constants",
        "model_config.py",
    )
    with open(config_path) as f:
        source = f.read()
    fc_start = source.find('"MiniMax-M2.5-FC"')
    fc_end = source.find("),", fc_start)
    fc_block = source[fc_start:fc_end]
    assert 'org="MiniMax"' in fc_block


# ── Test 12: Model config uses MiniMaxHandler ────────────────────────────────
def test_model_config_uses_minimax_handler():
    """Model config entries must reference MiniMaxHandler."""
    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "constants",
        "model_config.py",
    )
    with open(config_path) as f:
        source = f.read()
    fc_start = source.find('"MiniMax-M2.5-FC"')
    fc_end = source.find("),", fc_start)
    fc_block = source[fc_start:fc_end]
    assert "model_handler=MiniMaxHandler" in fc_block


# ── Test 13: Handler __init__ signature matches convention ───────────────────
def test_minimax_handler_init_signature():
    """Handler __init__ must accept the standard BFCL arguments."""
    import ast

    handler_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "model_handler",
        "api_inference",
        "minimax.py",
    )
    with open(handler_path) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "MiniMaxHandler":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    arg_names = [a.arg for a in item.args.args]
                    assert "self" in arg_names
                    assert "model_name" in arg_names
                    assert "temperature" in arg_names
                    assert "registry_name" in arg_names
                    assert "is_fc_model" in arg_names
                    break
            break


# ── Test 14: Model config has pricing info ───────────────────────────────────
def test_model_config_has_pricing():
    """Model config entries should specify input and output pricing."""
    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "bfcl_eval",
        "constants",
        "model_config.py",
    )
    with open(config_path) as f:
        source = f.read()
    fc_start = source.find('"MiniMax-M2.5-FC"')
    fc_end = source.find("),", fc_start)
    fc_block = source[fc_start:fc_end]
    assert "input_price=" in fc_block
    assert "output_price=" in fc_block
