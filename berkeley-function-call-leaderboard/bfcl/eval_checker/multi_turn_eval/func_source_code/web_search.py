import html2text
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


class WebSearchAPI:

    @staticmethod
    def duckduckgo_search(keywords: str, region: str = "wt-wt"):
        """
        This function searches DuckDuckGo for the provided keywords and region.

        Args:
            keywords (str): The keywords to search for.
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
            return DDGS().text(keywords=keywords, region=region)
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def fetch(url: str, mode: str = "raw") -> str:
        """
        This function retrieves content from the provided URL and processes it based on the selected mode.

        Args:
            url (str): The URL to fetch content from. Must start with 'http://' or 'https://'.
            mode (str, optional): The mode to process the fetched content. Defaults to "raw".
                Supported modes are:
                    - "raw": Returns the raw HTML content.
                    - "markdown": Converts HTML content to Markdown format, using html2text.
                    - "truncate": Extracts and cleans text by removing scripts, styles, and extraneous whitespace.
        """
        try:
            # Validate URL (basic check)
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid URL: {url}")

            # Fetch the content
            response = requests.get(url)
            response.raise_for_status()

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

        except requests.exceptions.Timeout:
            return {"error": f"Timeout occurred while fetching {url}"}
        except requests.exceptions.ConnectionError:
            return {"error": f"Connection error occurred while fetching {url}"}
        except requests.exceptions.HTTPError as e:
            return {"error": f"HTTP error occurred while fetching {url}: {str(e)}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"An error occurred while fetching {url}: {str(e)}"}
        except ValueError as e:
            return {"error": str(e)}
