import os

import html2text
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from typing import Optional
import random
from urllib.parse import urlparse

ERROR_TEMPLATES = [
    "503 Server Error: Service Unavailable for url: {url}",
    "429 Client Error: Too Many Requests for url: {url}",
    "403 Client Error: Forbidden for url: {url}",
    (
        "HTTPSConnectionPool(host='{host}', port=443): Max retries exceeded with url: {path} "
        "(Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x{id1:x}>, "
        "'Connection to {host} timed out. (connect timeout=5)'))"
    ),
    "HTTPSConnectionPool(host='{host}', port=443): Read timed out. (read timeout=5)",
    (
        "Max retries exceeded with url: {path} "
        "(Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x{id2:x}>: "
        "Failed to establish a new connection: [Errno -2] Name or service not known'))"
    ),
]


class WebSearchAPI:
    def __init__(self):
        self._api_description = "This tool belongs to the Web Search API category. It provides functions to search the web and browse search results."
        self.show_snippet = True
        # Note: The following two random generators are used to simulate random errors, but that feature is not currently used
        # This one used to determine if we should simulate a random error
        # Outcome (True means simulate error): [True, False, True, True, False, True, True, True, False, False, True, True, False, True, False, False, False, False, False, True]
        self._random = random.Random(337)
        # This one is used to determine the content of the error message
        self._rng = random.Random(1053)

    def _load_scenario(self, initial_config: dict, long_context: bool = False):
        # We don't care about the long_context parameter here
        # It's there to match the signature of functions in the multi-turn evaluation code
        self.show_snippet = initial_config["show_snippet"]

    def search_engine_query(
        self,
        keywords: str,
        max_results: Optional[int] = 10,
        region: Optional[str] = "wt-wt",
    ) -> list:
        """
        This function queries the search engine for the provided keywords and region.

        Args:
            keywords (str): The keywords to search for.
            max_results (int, optional): The maximum number of search results to return. Defaults to 10.
            region (str, optional): The region to search in. Defaults to "wt-wt". Possible values include:
                - xa-ar for Arabia
                - xa-en for Arabia (en)
                - ar-es for Argentina
                - au-en for Australia
                - at-de for Austria
                - be-fr for Belgium (fr)
                - be-nl for Belgium (nl)
                - br-pt for Brazil
                - bg-bg for Bulgaria
                - ca-en for Canada
                - ca-fr for Canada (fr)
                - ct-ca for Catalan
                - cl-es for Chile
                - cn-zh for China
                - co-es for Colombia
                - hr-hr for Croatia
                - cz-cs for Czech Republic
                - dk-da for Denmark
                - ee-et for Estonia
                - fi-fi for Finland
                - fr-fr for France
                - de-de for Germany
                - gr-el for Greece
                - hk-tzh for Hong Kong
                - hu-hu for Hungary
                - in-en for India
                - id-id for Indonesia
                - id-en for Indonesia (en)
                - ie-en for Ireland
                - il-he for Israel
                - it-it for Italy
                - jp-jp for Japan
                - kr-kr for Korea
                - lv-lv for Latvia
                - lt-lt for Lithuania
                - xl-es for Latin America
                - my-ms for Malaysia
                - my-en for Malaysia (en)
                - mx-es for Mexico
                - nl-nl for Netherlands
                - nz-en for New Zealand
                - no-no for Norway
                - pe-es for Peru
                - ph-en for Philippines
                - ph-tl for Philippines (tl)
                - pl-pl for Poland
                - pt-pt for Portugal
                - ro-ro for Romania
                - ru-ru for Russia
                - sg-en for Singapore
                - sk-sk for Slovak Republic
                - sl-sl for Slovenia
                - za-en for South Africa
                - es-es for Spain
                - se-sv for Sweden
                - ch-de for Switzerland (de)
                - ch-fr for Switzerland (fr)
                - ch-it for Switzerland (it)
                - tw-tzh for Taiwan
                - th-th for Thailand
                - tr-tr for Turkey
                - ua-uk for Ukraine
                - uk-en for United Kingdom
                - us-en for United States
                - ue-es for United States (es)
                - ve-es for Venezuela
                - vn-vi for Vietnam
                - wt-wt for No region

        Returns:
            list: A list of search result dictionaries, each containing information such as:
            - 'title' (str): The title of the search result.
            - 'href' (str): The URL of the search result.
            - 'body' (str): A brief description or snippet from the search result.
        """

        try:
            params = {
                "engine": "duckduckgo",
                "q": keywords,
                "kl": region,
                "api_key": os.getenv("SERPAPI_API_KEY"),
            }

            search = GoogleSearch(params)
            search_results = search.get_dict()
            if "error" in search_results:
                return search_results

            search_results = search_results["organic_results"]

            # Convert the search results to the desired format
            results = []
            for result in search_results[:max_results]:
                if self.show_snippet:
                    results.append(
                        {
                            "title": result["title"],
                            "href": result["link"],
                            "body": result["snippet"],
                        }
                    )
                else:
                    results.append(
                        {
                            "title": result["title"],
                            "href": result["link"],
                        }
                    )

            return results

        except Exception as e:
            return {"error": str(e)}

        # Note: Un-comment the following section to use the DuckDuckGo API
        # This API is free, but is rate limited.
        # Need to first `pip install duckduckgo_search`

        # from duckduckgo_search import DDGS
        # try:
        #     time.sleep(1)
        #     return DDGS().text(keywords=keywords, region=region, max_results=max_results)
        # except Exception as e:
        #     return {"error": str(e)}

    def fetch_url_content(self, url: str, mode: str = "raw") -> str:
        """
        This function retrieves content from the provided URL and processes it based on the selected mode.

        Args:
            url (str): The URL to fetch content from. Must start with 'http://' or 'https://'.
            mode (str, optional): The mode to process the fetched content. Defaults to "raw".
                Supported modes are:
                    - "raw": Returns the raw HTML content.
                    - "markdown": Converts raw HTML content to Markdown format for better readability, using html2text.
                    - "truncate": Extracts and cleans text by removing scripts, styles, and extraneous whitespace.
        """
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {url}")

        try:
            # A header that mimics a browser request. This helps avoid 403 Forbidden errors.
            # TODO: Is this the best way to do this?
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/112.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Referer": "https://www.google.com/",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document",
            }
            response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
            response.raise_for_status()

            # Note: Un-comment this when we want to simulate a random error
            # Flip a coin to simulate a random error
            # if self._random.random() < 0.95:
            #     return {"error": self._fake_requests_get_error_msg(url)}

            # Process the response based on the mode
            if mode == "raw":
                return {"content": response.text}

            elif mode == "markdown":
                converter = html2text.HTML2Text()
                markdown = converter.handle(response.text)
                return {"content": markdown}

            elif mode == "truncate":
                soup = BeautifulSoup(response.text, "html.parser")

                # Remove scripts and styles
                for script_or_style in soup(["script", "style"]):
                    script_or_style.extract()

                # Extract and clean text
                text = soup.get_text(separator="\n", strip=True)
                return {"content": text}
            else:
                raise ValueError(f"Unsupported mode: {mode}")

        except Exception as e:
            return {"error": f"An error occurred while fetching {url}: {str(e)}"}

    def _fake_requests_get_error_msg(self, url: str) -> str:
        """
        Return a realistic‑looking requests/urllib3 error message.
        """
        parsed = urlparse(url)

        context = {
            "url": url,
            "host": parsed.hostname or "unknown",
            "path": parsed.path or "/",
            "id1": self._rng.randrange(0x10000000, 0xFFFFFFFF),
            "id2": self._rng.randrange(0x10000000, 0xFFFFFFFF),
        }

        template = self._rng.choice(ERROR_TEMPLATES)

        return template.format(**context)
