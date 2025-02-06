import os
import requests
import html2text

from urllib.parse import urlencode
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain.chains import create_extraction_chain_pydantic
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union

load_dotenv()
openai_key = os.environ.get("OPENAI_API_KEY")
llm = ChatOpenAI(temperature=0, openai_api_key=openai_key)


def prompt_api():
    return """Read the following API documentation HTML to text content about {api_name} API and fill out the relvenant information for each api call. Make sure to write the api_call field in python code. 
    Here is an example. 

    Example Output.:

    [ 
  {{
    "api_name": "Torch Hub Model snakers4-silero",
    "api_call": "torch.hub.load(repo_or_dir=['snakers4/silero-models'], model=['silero_stt'], *args, source, trust_repo, force_reload, verbose, skip_validation, **kwargs)", 
    "api_version": 2.0, 
    "api_arguments": {{
      "repo_or_dir": "snakers4/silero-models", 
      "model": "silero_stt", 
      "language": ["en", "de", "es"]
    }},
    "functionality": "Speech to Text",
    "env_requirements": ["torchaudio", "torch", "omegaconf", "soundfile"],
    "example_code": "import torch \n \
                    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True) \n \
                    imgs = ['https://ultralytics.com/images/zidane.jpg'] \n \
                    results = model(imgs)",
    "meta_data": {{
      "description": "Silero Speech-To-Text models provide enterprise grade STT in a compact form-factor for several commonly spoken languages. The models are robust to a variety of dialects, codecs, domains, noises, and lower sampling rates. They consume a normalized audio in the form of samples and output frames with token probabilities. A decoder utility is provided for simplicity.", 
      "performance": {{"dataset": "imagenet", "accuracy": "80.4\%"}}
    }},
    "questions": [
      "I am a doctor and I want to dictate what my patient is saying and put it into a text doc in my computer.",
      "My students in math class is having trouble following up my content. He needs an API to write down what I am saying for reviewing.",
    ],
  }},
  ...
]
"""


class Option1Format(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    api_name: str = Field(description="Name of API")
    api_call: str = Field(description="Example of how to call the API in Python, including function name and arguments")
    api_version: Optional[str] = Field(description="Version of API, if applicable")
    api_arguments: List[List[str]] = Field(description="JSON of all the restricted keywords in the arguments list")
    functionality: str = Field(description="Brief description of what the API function does (maximum 20 words)")
    env_requirements: Optional[List[str]] = Field(description="List of dependencies required in the environment")
    example_code: Optional[str] = Field(description="Python code snippet demonstrating how to use the API")
    meta_data: Optional[List[List[Any]]] = Field(description="Additional metadata in JSON format about the API")
    Questions: Optional[List[str]] = Field(
        description="A question describing a real-life scenario that uses this API. Please don't include specific API name.")


class ErrorFetchingContent(Exception):
    pass

class HTTPError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__(f"HTTP Error with status code: {status_code}")

def load_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the status is 4xx, 5xx
        return response.text
    except requests.HTTPError as http_err:
        raise HTTPError(response.status_code) from http_err
    except requests.RequestException as req_err:
        raise ErrorFetchingContent(f"Error fetching {url}: {req_err}")
    except Exception as e:
        raise Exception(f"Unexpected Error: {str(e)}")



def clean_soup(soup):
    exclude_classes = [
        "navbar", "nav", "navigation", "menu", "header", "footer",
        "sidebar", "advert", "advertisement", "banner", "breadcrumbs",
        "cookie-consent", "modal", "popup", "feedback", "social",
        "social-links", "social-media", "share-buttons", "login",
        "signup", "search-box", "search-bar", "pager", "pagination",
        "related-links", "related-articles", "comments", "footer-links",
        "footer-nav", "legal", "disclaimer", "copyright", "toc", "table-of-contents"
    ]

    exclude_ids = [
        "navigation", "navbar", "nav", "navigation", "menu", "header", "footer",
        "sidebar", "advert", "advertisement", "banner", "breadcrumbs",
        "cookie-consent", "modal", "popup", "feedback", "social",
        "social-links", "social-media", "share-buttons", "login",
        "signup", "search", "pager", "pagination", "related-links",
        "comments", "footer-links", "footer-nav", "legal", "disclaimer",
        "copyright", "toc"
    ]

    exclude_tags = ["header", "footer"]

    # Remove elements with specified classes and IDs
    for class_name in exclude_classes:
        for element in soup.find_all(class_=class_name):
            # print(element)
            element.decompose()

    for id_name in exclude_ids:
        for element in soup.find_all(id=id_name):
            # print(element)
            element.decompose()

    for tag in exclude_tags:
        for element in soup.find_all(tag):
            # print(element)
            element.decompose()

    return soup


def find_main_content(soup):
    common_class_names = ['.main', '.main-content', '.api-documentation', '.content', '.primary-content']
    for class_name in common_class_names:
        main_content = soup.select_one(class_name)
        if main_content:
            return main_content

    print("common_class_names not found, reverting to body or entire soup.")
    return soup.find("body") or soup  # Fallback to the whole body or entire soup if no class matches


def extract_relevant_tags(soup):
    tags_to_include = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'code', 'section', 'pre']
    # Create a new soup object to hold the filtered content
    filtered_soup = BeautifulSoup('', 'html.parser')
    for tag in soup.find_all(tags_to_include):
        filtered_soup.append(tag)
    return filtered_soup


def soup_to_markdown(soup) -> str:
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_emphasis = False
    h.bypass_tables = False  # Enable Markdown formatting for tables
    h.ignore_tables = False  # Process table-related tags
    h.inline_links = False  # Format links and images inline
    h.wrap_links = False  # Wrap links during text wrapping
    h.wrap_list_items = True  # Wrap list items during text wrapping
    h.use_automatic_links = True  # Convert URLs to clickable links
    h.mark_code = True  # Wrap 'pre' blocks with [code]...[/code]
    h.ignore_images = True
    h.ignore_anchors = True  # Ignore anchor tags
    h.single_line_break = True  # Use a single line break instead of two
    h.unicode_snob = True  # Use unicode
    h.escape_snob = False  # Escape all special characters
    h.links_each_paragraph = False  # Put links after every paragraph
    h.skip_internal_links = True  # Skip internal anchor links
    h.protect_links = True  # Protect links from line breaks
    h.images_as_html = False  # Generate HTML tags for images
    h.images_to_alt = True  # Convert images to their alt text
    h.body_width = 0  # No wrapping
    h.wrap_tables = True  # Wrap tables during text wrapping

    html_content = str(soup)
    return h.handle(html_content)


def html_transformer(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    cleaned_soup = clean_soup(soup)
    main_soup = find_main_content(cleaned_soup)
    relevant_soup = extract_relevant_tags(main_soup)
    markdown = soup_to_markdown(relevant_soup)
    return markdown


def extract(content: str, llm):
    p = PromptTemplate(input_variables=["api_name"], template=prompt_api())
    return create_extraction_chain_pydantic(pydantic_schema=Option1Format, llm=llm, prompt=p).run(content)


def process_results(results: Dict[str, Dict[str, Union[Option1Format, List[Option1Format]]]], option_2_json) -> List[Any]:
    def process_item(item):
        # Recursively convert items into JSON
        if isinstance(item, Option1Format):
            return item.dict()
        elif isinstance(item, list):
            return [process_item(sub_item) for sub_item in item]
        else:
            return item

    def sort_dict_by_key_order(dct):
        desired_key_order = [
            "user_name", "api_name", "api_call", "api_version", "api_arguments",
            "functionality", "env_requirements", "example_code", "meta_data", "Questions"
        ]
        sorted_dict = {key: dct.get(key, None) for key in desired_key_order}
        sorted_dict["user_name"] = option_2_json["user_name"]
        return sorted_dict
    
    for url, content in results.items():
        if content["status"] != "error":
            # recursively convert data into a JSON
            json_format: Union[List, Dict] = process_item(content["data"])
            if isinstance(json_format, list):
                sorted_json_format = [sort_dict_by_key_order(d) for d in json_format if isinstance(d, dict)]
            elif isinstance(json_format, dict):
                sorted_json_format = sort_dict_by_key_order(json_format) if isinstance(json_format, dict) else print(f"ERROR SORTING item: {json_format}")
            
            content["data"] = sorted_json_format
        

    return results


def scrape(urls):
    results = {}
    for url in urls:
        try:
            html_content = load_html(url) 
            markdown = html_transformer(html_content)
            extracted_content = extract(markdown, llm)
            results[url] = {"status": "success", "data": extracted_content}
        
        except HTTPError as http_err:
            results[url] = {"status": "error", "data": [f"HTTP Error: {http_err.status_code}"]}
        except ErrorFetchingContent as err:
            results[url] = {"status": "error", "data": [str(err)]}
        except Exception as e:
            results[url] = {"status": "error", "data": [str(e)]}
    return results