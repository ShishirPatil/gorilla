import os
import random
import time
from typing import Optional
from urllib.parse import urlparse

import html2text
import requests
from bs4 import BeautifulSoup

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
        This function queries the search engine for the provided keywords using You.com API.

        Args:
            keywords (str): The keywords to search for.
            max_results (int, optional): The maximum number of search results to return. Defaults to 10.
            region (str, optional): The region to search in. Defaults to "wt-wt" (worldwide).
                Supported regions include: us-en, uk-en, ca-en, au-en, de-de, fr-fr, es-es, 
                it-it, jp-jp, kr-kr, cn-zh, in-en, br-pt, mx-es, ru-ru, nl-nl, and many more.
                The API automatically maps region codes to You.com's format.

        Returns:
            list: A list of search result dictionaries, each containing information such as:
            - 'title' (str): The title of the search result.
            - 'href' (str): The URL of the search result.
            - 'body' (str): A brief description or snippet from the search result.
        """
        backoff = 2  # initial back-off in seconds
        # Replace with the actual API key
        api_key = os.getenv("YDC_API_KEY")
        if not api_key:
            return {"error": "You.com API key not provided. Please set YDC_API_KEY environment variable."}

        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        
        params = {
            "query": keywords,
            "count": max_results
        }
        
        # Add region parameter if specified (supports region filtering)
        if region and region != "wt-wt":
            # Map common region codes to You.com format
            region_mapping = {
                "us-en": "US",
                "uk-en": "GB", 
                "ca-en": "CA",
                "au-en": "AU",
                "de-de": "DE",
                "fr-fr": "FR",
                "es-es": "ES",
                "it-it": "IT",
                "jp-jp": "JP",
                "kr-kr": "KR",
                "cn-zh": "CN",
                "in-en": "IN",
                "br-pt": "BR",
                "mx-es": "MX",
                "ru-ru": "RU",
                "nl-nl": "NL",
                "se-sv": "SE",
                "no-no": "NO",
                "dk-da": "DK",
                "fi-fi": "FI",
                "pl-pl": "PL",
                "tr-tr": "TR",
                "ar-es": "AR",
                "cl-es": "CL",
                "co-es": "CO",
                "pe-es": "PE",
                "ve-es": "VE",
                "za-en": "ZA",
                "eg-en": "EG",
                "ng-en": "NG",
                "ke-en": "KE",
                "th-th": "TH",
                "vn-vi": "VN",
                "id-id": "ID",
                "my-ms": "MY",
                "ph-en": "PH",
                "sg-en": "SG",
                "hk-tzh": "HK",
                "tw-tzh": "TW"
            }
            
            # Use mapped region or try the original region code
            you_region = region_mapping.get(region, region.upper())
            params["region"] = you_region

        # Infinite retry loop with exponential backoff
        while True:
            try:
                response = requests.get(
                    "https://api.ydc-index.io/v1/search",
                    headers=headers,
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 429:
                    wait_time = backoff + random.uniform(0, backoff)
                    error_block = (
                        "*" * 100
                        + f"\n❗️❗️ [WebSearchAPI] Received 429 from You.com API. Rate limit exceeded. Retrying in {wait_time:.1f} seconds…"
                        + "*" * 100
                    )
                    print(error_block)
                    time.sleep(wait_time)
                    backoff = min(backoff * 2, 120)  # cap the back-off
                    continue
                elif response.status_code != 200:
                    error_block = (
                        "*" * 100
                        + f"\n❗️❗️ [WebSearchAPI] Error from You.com API: {response.status_code} - {response.text}. This is not a rate-limit error, so it will not be retried."
                        + "*" * 100
                    )
                    print(error_block)
                    return {"error": f"You.com API error {response.status_code}: {response.text}"}
                
                search_results = response.json()
                break  # Success – no rate-limit error detected
                
            except Exception as e:
                # Check if the exception is a rate limit error
                if "429" in str(e):
                    wait_time = backoff + random.uniform(0, backoff)
                    error_block = (
                        "*" * 100
                        + f"\n❗️❗️ [WebSearchAPI] Received 429 from You.com API (in exception). Rate limit exceeded. Retrying in {wait_time:.1f} seconds…"
                        + "*" * 100
                    )
                    print(error_block)
                    time.sleep(wait_time)
                    backoff = min(backoff * 2, 120)  # cap the back-off
                    continue
                else:
                    error_block = (
                        "*" * 100
                        + f"\n❗️❗️ [WebSearchAPI] Error from You.com API: {str(e)}. This is not a rate-limit error, so it will not be retried."
                        + "*" * 100
                    )
                    print(error_block)
                    return {"error": str(e)}

        if "results" not in search_results:
            return {
                "error": "Failed to retrieve the search results from You.com API. Please try again later."
            }

        # Extract web results from You.com API response
        web_results = search_results.get("results", {}).get("web", [])
        news_results = search_results.get("results", {}).get("news", [])

        # Convert the search results to the desired format
        results = []
        
        # Process web results
        for result in web_results[:max_results]:
            if self.show_snippet:
                results.append(
                    {
                        "title": result.get("title", ""),
                        "href": result.get("url", ""),
                        "body": result.get("description", ""),
                    }
                )
            else:
                results.append(
                    {
                        "title": result.get("title", ""),
                        "href": result.get("url", ""),
                    }
                )
        
        # If we need more results and have news results, add them
        if len(results) < max_results and news_results:
            remaining = max_results - len(results)
            for result in news_results[:remaining]:
                if self.show_snippet:
                    results.append(
                        {
                            "title": result.get("title", ""),
                            "href": result.get("url", ""),
                            "body": result.get("description", ""),
                        }
                    )
                else:
                    results.append(
                        {
                            "title": result.get("title", ""),
                            "href": result.get("url", ""),
                        }
                    )

        return results

    def fetch_url_content(self, url: str, mode: str = "raw", use_you_api: bool = False) -> str:
        """
        This function retrieves content from the provided URL and processes it based on the selected mode.

        Args:
            url (str): The URL to fetch content from. Must start with 'http://' or 'https://'.
            mode (str, optional): The mode to process the fetched content. Defaults to "raw".
                Supported modes are:
                    - "raw": Returns the raw HTML content.
                    - "markdown": Converts raw HTML content to Markdown format for better readability, using html2text.
                    - "truncate": Extracts and cleans text by removing scripts, styles, and extraneous whitespace.
            use_you_api (bool, optional): Whether to use You.com's content API for better content extraction. Defaults to False.
        """
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {url}")

        # Try You.com API first if requested and available
        if use_you_api:
            api_key = os.getenv("YDC_API_KEY")
            if api_key:
                try:
                    headers = {
                        "X-API-Key": api_key,
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "urls": [url],
                        "livecrawl_formats": "html"
                    }
                    
                    response = requests.post(
                        "https://api.ydc-index.io/v1/contents",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 0 and "html" in data[0]:
                            html_content = data[0]["html"]
                            
                            # Process the response based on the mode
                            if mode == "raw":
                                return {"content": html_content}
                            elif mode == "markdown":
                                converter = html2text.HTML2Text()
                                markdown = converter.handle(html_content)
                                return {"content": markdown}
                            elif mode == "truncate":
                                soup = BeautifulSoup(html_content, "html.parser")
                                # Remove scripts and styles
                                for script_or_style in soup(["script", "style"]):
                                    script_or_style.extract()
                                # Extract and clean text
                                text = soup.get_text(separator="\n", strip=True)
                                return {"content": text}
                            else:
                                raise ValueError(f"Unsupported mode: {mode}")
                    else:
                        print(f"You.com API returned {response.status_code}, falling back to direct fetch")
                        
                except Exception as e:
                    print(f"You.com API failed: {str(e)}, falling back to direct fetch")

        # Fallback to direct HTTP request
        try:
            # A header that mimics a browser request. This helps avoid 403 Forbidden errors.
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
