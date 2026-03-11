"""
Glyphh Ada — Hyperdimensional Computing (HDC) + Function Calling handler.

Architecture:
  Glyphh Ada uses a two-stage pipeline for function calling:

  1. HDC Routing (deterministic, no LLM):
     - Encodes user queries and function signatures into 10,000-dimensional
       hypervectors using bag-of-words + role binding
     - Uses cosine similarity in HD space to route queries to the most
       relevant function(s), narrowing from N candidates to top-3
     - For multi-turn scenarios, a CognitiveLoop tracks conversation state
       (working directory, prior calls) to improve routing accuracy

  2. Argument Extraction (Claude Haiku 4.5):
     - Only the matched function(s) are sent to the LLM for parameter extraction
     - Uses native tool_use (function calling) mode
     - The LLM sees only the filtered candidates, not the full function set

  This hybrid approach means:
    - Routing is deterministic and instant (no LLM cost for function selection)
    - LLM cost is minimal (only arg extraction on pre-filtered functions)
    - The HDC layer can be trained on domain-specific function vocabularies

  Results are generated using Glyphh's own eval pipeline and submitted as
  pre-computed result files. The decode_ast/decode_execute methods handle
  the same output format as ClaudeHandler since the arg extraction stage
  uses Claude's native tool_use format.

  For more information: https://glyphh.ai
"""

from bfcl_eval.model_handler.api_inference.claude import ClaudeHandler


class GlyphhHandler(ClaudeHandler):
    """Glyphh Ada handler — HDC routing + Claude Haiku for arg extraction.

    Extends ClaudeHandler since the argument extraction stage uses Claude's
    native tool_use API. The HDC routing layer runs outside the BFCL handler
    pipeline (in Glyphh's own eval framework), so inference methods are
    inherited as-is from ClaudeHandler.

    The key difference from vanilla Claude:
      - Function selection is done by HDC (cosine similarity in hyperdimensional
        space), not by the LLM
      - The LLM only sees the top-3 HDC-matched functions, reducing context
        and improving accuracy on large function sets
      - Multi-turn state tracking uses HDC pathway encoding, not prompt history
    """

    def __init__(
        self,
        model_name,
        temperature,
        registry_name,
        is_fc_model,
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, registry_name, is_fc_model, **kwargs)

    def _get_max_tokens(self):
        # Glyphh Ada uses Claude Haiku 4.5 for arg extraction
        return 64000
