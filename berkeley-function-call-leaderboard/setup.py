from setuptools import setup, find_packages
import codecs

with codecs.open('README.md', 'r', 'utf-8') as f:
    long_description = f.read()

setup(
    name="bfcl",
    version="0.1.0",
    description="Berkeley Function Calling Leaderboard (BFCL)",
    author="Sky Computing Lab",
    author_email="sky@cs.berkeley.edu",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    license="Apache 2.0",
    packages=find_packages(include=["bfcl*"]),
    install_requires=[
        "requests",
        "tqdm",
        "numpy==1.26.4",
        "pandas",
        "huggingface_hub",
        "pydantic>=2.8.2",
        "python-dotenv>=1.0.1",
        "tree_sitter==0.21.3",
        "tree-sitter-java==0.21.0",
        "tree-sitter-javascript==0.21.4",
        "openai==1.35.13",
    ],
    extras_require={
        "oss_eval": ["vllm==0.5.0"],
        "proprietary_eval": [
            "mistralai==0.4.2",
            "anthropic==0.31.1",
            "cohere==5.5.8",
        ],
        "all": ["bfcl[oss_eval]", "bfcl[proprietary_eval]"],
    },
    project_urls={
        "Repository": "https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard",
    },
)
