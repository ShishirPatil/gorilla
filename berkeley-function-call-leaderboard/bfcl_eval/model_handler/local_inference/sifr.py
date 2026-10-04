"""BFCL handler for Sifr — a calibrated typed-decision engine (0.8B).

The model does not generate tool calls; it scores every candidate option
(length-normalized key log-probabilities, acc_norm convention) and returns
the argmax with calibrated probabilities. When pointed at a Sifr decision
endpoint (REMOTE_OPENAI_BASE_URL), function-calling prompts are answered by
tool selection via the engine + type-based argument extraction, emitted in
the standard `func(a=1, b='x')` text the default decoders parse.

Run: start the decision server, then evaluate with
    REMOTE_OPENAI_BASE_URL=http://127.0.0.1:8100/v1 REMOTE_OPENAI_API_KEY=dummy \
    bfcl generate --model sifr-0.8b-v33 --skip-server-setup ...
"""

from bfcl_eval.model_handler.local_inference.base_oss_handler import OSSHandler


class SifrHandler(OSSHandler):
    """
    Sifr decision engine via an OpenAI-compatible decision endpoint.

    Inherits the standard prompting/decoding path: the base handler posts the
    rendered prompt to the configured OpenAI-compatible endpoint and the
    default `decode_ast`/`decode_execute` parse the returned `func(...)`
    text. The endpoint performs tool selection with calibrated option
    scoring and type-based argument extraction.
    """
