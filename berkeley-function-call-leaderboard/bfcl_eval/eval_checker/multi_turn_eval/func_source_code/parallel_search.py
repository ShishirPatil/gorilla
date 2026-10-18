"""Anonymous Parallel search over the MCP Streamable HTTP transport."""

import json
from datetime import timedelta

import anyio
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import Implementation

MCP_URL = "https://search.parallel.ai/mcp"
USER_AGENT = "bfcl-eval (https://github.com/ShishirPatil/gorilla)"
REQUEST_TIMEOUT = 30


async def _search(keywords: str, session_id: str) -> dict:
    # Bound the whole exchange, including initialization and transport cleanup.
    with anyio.fail_after(REQUEST_TIMEOUT):
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT
        ) as http_client:
            async with streamable_http_client(MCP_URL, http_client=http_client) as (
                read,
                write,
                _,
            ):
                async with ClientSession(
                    read,
                    write,
                    read_timeout_seconds=timedelta(seconds=REQUEST_TIMEOUT),
                    client_info=Implementation(name="bfcl-eval", version="1"),
                ) as session:
                    await session.initialize()
                    response = await session.call_tool(
                        "web_search",
                        {
                            "objective": keywords,
                            "search_queries": [keywords],
                            "session_id": session_id,
                        },
                    )

    text = "\n".join(block.text for block in response.content if block.type == "text")
    if response.isError:
        raise ValueError(text or "Parallel search returned a tool error.")
    payload = response.structuredContent
    if payload is None:
        payload = json.loads(text)
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("Parallel search returned an invalid results payload.")
    return payload


def _error_message(error: Exception) -> str:
    # AnyIO transports may wrap the underlying HTTP/timeout error in task groups.
    if isinstance(error, (TimeoutError, httpx.TimeoutException)):
        return "Parallel search timed out."
    children = getattr(error, "exceptions", ())
    if children:
        return "; ".join(_error_message(child) for child in children)
    return str(error)


def search(keywords: str, max_results: int | None, show_snippet: bool, session_id: str):
    """Adapt MCP results to BFCL's title/href/body tool contract."""
    try:
        if max_results is not None and (
            isinstance(max_results, bool)
            or not isinstance(max_results, int)
            or max_results < 0
        ):
            raise ValueError("max_results must be a nonnegative integer or None.")
        if max_results == 0:
            return []
        payload = anyio.run(_search, keywords, session_id)
        results = []
        for item in payload["results"][:max_results]:
            url = item["url"]
            if not isinstance(url, str) or not url.startswith(("https://", "http://")):
                raise ValueError("Parallel search returned an invalid result URL.")
            result = {"title": item.get("title") or url, "href": url}
            if show_snippet:
                result["body"] = "\n".join(item["excerpts"])
            results.append(result)
        return results
    except Exception as error:
        # Cancellation/KeyboardInterrupt are BaseExceptions and must propagate.
        return {"error": _error_message(error)}
