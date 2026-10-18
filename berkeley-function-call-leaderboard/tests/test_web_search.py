"""Run with: python -m unittest discover -s tests -p 'test_web_search.py'."""

import ast
import json
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import Mock, patch

import anyio
import httpx
from dotenv import load_dotenv

from bfcl_eval.eval_checker.multi_turn_eval.func_source_code import parallel_search
from bfcl_eval.eval_checker.multi_turn_eval.func_source_code.web_search import (
    WebSearchAPI,
)
from bfcl_eval.eval_checker.multi_turn_eval.multi_turn_utils import (
    execute_multi_turn_func_call,
)
from bfcl_eval.model_handler.base_handler import BaseHandler


class ScriptedHandler(BaseHandler):
    """Deterministic model responses inside BFCL's real FC inference loop."""

    def __init__(self, calls):
        super().__init__("scripted", 0, "scripted-FC", True)
        self.calls = calls
        self.consumed = []
        self.queries = 0

    def _pre_query_processing_FC(self, data, entry):
        return data

    def _compile_tools(self, data, entry):
        return data

    def add_first_turn_message_FC(self, data, message):
        return data

    def _query_FC(self, data):
        self.queries += 1
        if self.queries == 1:
            return self.calls, 0
        # This is the subsequent model request, after tool results were appended.
        self.consumed.extend(data["tool_results"])
        return [], 0

    def _parse_query_response_FC(self, response):
        return {"model_responses": response, "input_token": 0, "output_token": 0}

    def _add_assistant_message_FC(self, data, response):
        return data

    def decode_execute(self, response, has_tool_call_tag):
        return response

    def _add_execution_results_FC(self, data, results, response):
        data["tool_results"] = results
        return data


class WebSearchTests(unittest.TestCase):
    def setUp(self):
        # No ambient keys, saved .env, provider selection, or HTTP credentials.
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.requests = []
        self.payload = {
            "results": [
                {
                    "title": "BFCL",
                    "url": "https://gorilla.cs.berkeley.edu/",
                    "excerpts": ["Tool calling", "Agentic search"],
                },
                {"title": None, "url": "https://example.org/second", "excerpts": []},
            ]
        }
        self.tool_error = None
        self.text_only = False
        self.client = None
        self.real_client = httpx.AsyncClient

    async def respond(self, request):
        self.requests.append(request)
        message = json.loads(request.content)
        method = message["method"]
        if method.startswith("notifications/"):
            return httpx.Response(202)
        if method == "initialize":
            result = {
                "protocolVersion": message["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "fixture", "version": "1"},
            }
        elif method == "tools/list":
            result = {
                "tools": [{"name": "web_search", "inputSchema": {"type": "object"}}]
            }
        elif method == "tools/call":
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": self.tool_error or json.dumps(self.payload),
                    }
                ],
                "isError": self.tool_error is not None,
            }
            if not self.text_only and self.tool_error is None:
                result["structuredContent"] = self.payload
        else:
            raise AssertionError(method)
        return httpx.Response(
            200, json={"jsonrpc": "2.0", "id": message["id"], "result": result}
        )

    def client_factory(self, **kwargs):
        self.client = self.real_client(
            transport=httpx.MockTransport(self.respond), **kwargs
        )
        return self.client

    def transport(self):
        return patch.object(
            parallel_search.httpx, "AsyncClient", side_effect=self.client_factory
        )

    def dispatch(self, calls=None, show_snippet=True, involved_classes=None):
        return execute_multi_turn_func_call(
            calls
            or [
                'search_engine_query(keywords="BFCL agentic web search", max_results=1)'
            ],
            {"WebSearchAPI": {"show_snippet": show_snippet}},
            ["WebSearchAPI"] if involved_classes is None else involved_classes,
            "test",
            "web_search_base_" + uuid.uuid4().hex,
        )

    def test_unconfigured_dispatch_and_wire_requests(self):
        with self.transport():
            results, instances = self.dispatch()
        result = ast.literal_eval(results[0])
        self.assertEqual(
            result,
            [
                {
                    "title": "BFCL",
                    "href": "https://gorilla.cs.berkeley.edu/",
                    "body": "Tool calling\nAgentic search",
                }
            ],
        )
        methods = []
        for request in self.requests:
            self.assertEqual(str(request.url), parallel_search.MCP_URL)
            self.assertEqual(request.headers["user-agent"], parallel_search.USER_AGENT)
            self.assertNotIn("authorization", request.headers)
            message = json.loads(request.content)
            methods.append(message["method"])
            if message["method"] == "tools/call":
                self.assertEqual(message["params"]["name"], "web_search")
                self.assertEqual(
                    message["params"]["arguments"],
                    {
                        "objective": "BFCL agentic web search",
                        "search_queries": ["BFCL agentic web search"],
                        "session_id": instances["WebSearchAPI"]._parallel_session_id,
                    },
                )
        self.assertIn("initialize", methods)
        self.assertIn("tools/list", methods)
        self.assertIn("tools/call", methods)
        self.assertTrue(self.client.is_closed)

    def test_result_consumption_in_scripted_model_loop(self):
        handler = ScriptedHandler(
            ['search_engine_query(keywords="BFCL agentic web search", max_results=1)']
        )
        entry = {
            "id": "web_search_base_" + uuid.uuid4().hex,
            "initial_config": {"WebSearchAPI": {"show_snippet": True}},
            "involved_classes": ["WebSearchAPI"],
            "question": [[{"role": "user", "content": "Find BFCL."}]],
            "function": [],
        }
        with self.transport():
            _, metadata = handler.inference(entry, False, True)
        self.assertEqual(handler.queries, 2)
        self.assertIn("https://gorilla.cs.berkeley.edu/", handler.consumed[0])
        self.assertIn("Tool calling", handler.consumed[0])
        self.assertIn("inference_log", metadata)

    def test_no_snippet_and_text_response(self):
        self.text_only = True
        with self.transport():
            result, _ = self.dispatch(show_snippet=False)
        self.assertNotIn("body", ast.literal_eval(result[0])[0])

    def test_stable_session_and_none_limit(self):
        api = WebSearchAPI()
        with self.transport():
            result = api.search_engine_query("first query", max_results=None)
            api.search_engine_query("second query")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["title"], result[1]["href"])
        arguments = [
            json.loads(r.content)["params"]["arguments"]
            for r in self.requests
            if json.loads(r.content)["method"] == "tools/call"
        ]
        self.assertEqual(arguments[0]["session_id"], arguments[1]["session_id"])

    def test_explicit_parallel_overrides_serpapi_key(self):
        with patch.dict(
            os.environ,
            {"SERPAPI_API_KEY": "configured", "BFCL_SEARCH_PROVIDER": "parallel"},
        ), self.transport(), patch(
            "bfcl_eval.eval_checker.multi_turn_eval.func_source_code.web_search.GoogleSearch"
        ) as serp:
            self.dispatch()
        serp.assert_not_called()
        self.assertTrue(self.requests)

    def test_saved_dotenv_credentials_and_provider_choice(self):
        with tempfile.TemporaryDirectory() as directory:
            dotenv = Path(directory) / ".env"
            dotenv.write_text("SERPAPI_API_KEY=saved-key\nBFCL_SEARCH_PROVIDER=\n")
            # Match the CLI's existing saved-configuration precedence.
            load_dotenv(dotenv_path=dotenv, override=True)
            with self.transport(), patch(
                "bfcl_eval.eval_checker.multi_turn_eval.func_source_code.web_search.GoogleSearch"
            ) as serp:
                serp.return_value.get_dict.return_value = {"organic_results": []}
                self.dispatch()
                self.assertEqual(serp.call_args.args[0]["api_key"], "saved-key")
            self.assertEqual(self.requests, [])
            dotenv.write_text(
                "SERPAPI_API_KEY=saved-key\nBFCL_SEARCH_PROVIDER=parallel\n"
            )
            load_dotenv(dotenv_path=dotenv, override=True)
            with self.transport():
                self.dispatch()
            self.assertTrue(self.requests)

    def test_configured_serpapi_and_explicit_serpapi(self):
        for selection in ("", "serpapi"):
            with self.subTest(selection=selection), patch.dict(
                os.environ,
                {"SERPAPI_API_KEY": "configured", "BFCL_SEARCH_PROVIDER": selection},
            ), self.transport(), patch(
                "bfcl_eval.eval_checker.multi_turn_eval.func_source_code.web_search.GoogleSearch"
            ) as serp:
                serp.return_value.get_dict.return_value = {
                    "organic_results": [
                        {
                            "title": "Saved provider",
                            "link": "https://example.org/",
                            "snippet": "Saved snippet",
                        }
                    ]
                }
                result = WebSearchAPI().search_engine_query("query", region="us-en")
                self.assertEqual(result[0]["title"], "Saved provider")
                self.assertEqual(serp.call_args.args[0]["api_key"], "configured")
                self.assertEqual(serp.call_args.args[0]["kl"], "us-en")
        self.assertEqual(self.requests, [])

    def test_explicit_errors_never_fall_back(self):
        for provider, expected in (
            ("none", "disabled"),
            ("invalid", "must be"),
            ("serpapi", "SERPAPI_API_KEY is required"),
        ):
            with self.subTest(provider=provider), patch.dict(
                os.environ, {"BFCL_SEARCH_PROVIDER": provider}
            ), self.transport():
                self.assertIn(
                    expected, WebSearchAPI().search_engine_query("query")["error"]
                )
        self.assertEqual(self.requests, [])
        with patch.dict(
            os.environ, {"SERPAPI_API_KEY": "bad-key"}
        ), self.transport(), patch(
            "bfcl_eval.eval_checker.multi_turn_eval.func_source_code.web_search.GoogleSearch",
            side_effect=RuntimeError("401 invalid key"),
        ):
            self.assertIn("401", WebSearchAPI().search_engine_query("query")["error"])
        self.assertEqual(self.requests, [])

    def test_region_and_result_limits(self):
        with self.transport():
            api = WebSearchAPI()
            self.assertIn(
                "region selection",
                api.search_engine_query("query", region="us-en")["error"],
            )
            self.assertEqual(api.search_engine_query("query", max_results=0), [])
            self.assertIn(
                "max_results", api.search_engine_query("query", max_results=-1)["error"]
            )
            self.assertEqual(self.requests, [])
            self.assertEqual(len(api.search_engine_query("query", region=None)), 2)

    def test_tool_errors_and_invalid_payload(self):
        self.tool_error = "Anonymous quota exceeded. Try again later."
        with self.transport():
            result, _ = self.dispatch()
        self.assertIn("quota exceeded", result[0])
        self.assertEqual(
            sum(json.loads(r.content)["method"] == "tools/call" for r in self.requests),
            1,
        )
        self.tool_error = None
        for payload in (
            {},
            {"results": [{"url": "file:///etc/passwd", "excerpts": []}]},
        ):
            self.payload = payload
            with self.subTest(payload=payload), self.transport():
                result, _ = self.dispatch()
                self.assertIn("error", result[0])

    def test_http_timeout_and_transport_cleanup(self):
        async def slow(request):
            await anyio.sleep(10)

        self.respond = slow
        with patch.object(parallel_search, "REQUEST_TIMEOUT", 0.02), self.transport():
            result, _ = self.dispatch()
        self.assertIn("timed out", result[0])
        self.assertTrue(self.client.is_closed)

    def test_http_error_and_cleanup(self):
        async def denied(request):
            return httpx.Response(403, text="denied")

        self.respond = denied
        with self.transport():
            result, _ = self.dispatch()
        self.assertIn("403", result[0])
        self.assertTrue(self.client.is_closed)

    def test_cancellation_propagates_and_closes_transport(self):
        async def exercise():
            started = anyio.Event()

            async def pending(request):
                started.set()
                await anyio.sleep_forever()

            self.respond = pending
            async with anyio.create_task_group() as tasks:
                tasks.start_soon(parallel_search._search, "query", uuid.uuid4().hex)
                await started.wait()
                tasks.cancel_scope.cancel()

        with self.transport():
            anyio.run(exercise)
        self.assertTrue(self.client.is_closed)

    def test_keyboard_interrupt_propagates_through_dispatcher(self):
        with patch.object(
            parallel_search.anyio, "run", side_effect=KeyboardInterrupt
        ), self.assertRaises(KeyboardInterrupt):
            self.dispatch()

    def test_absent_tool_permission_does_not_call_search(self):
        with self.transport():
            result, _ = self.dispatch(involved_classes=[])
        self.assertIn("Error during execution", result[0])
        self.assertEqual(self.requests, [])

    def test_direct_fetch_modes_and_invalid_url_preserved(self):
        response = Mock(text="<html><p>Hello</p><script>hidden</script></html>")
        api = WebSearchAPI()
        with patch(
            "bfcl_eval.eval_checker.multi_turn_eval.func_source_code.web_search.requests.get",
            return_value=response,
        ) as get:
            self.assertEqual(
                api.fetch_url_content("https://example.org/", "raw"),
                {"content": response.text},
            )
            self.assertIn(
                "Hello",
                api.fetch_url_content("https://example.org/", "markdown")["content"],
            )
            self.assertEqual(
                api.fetch_url_content("https://example.org/", "truncate"),
                {"content": "Hello"},
            )
            self.assertEqual(get.call_args.kwargs["timeout"], 20)
        with self.assertRaises(ValueError):
            api.fetch_url_content("file:///etc/passwd")


if __name__ == "__main__":
    unittest.main()
