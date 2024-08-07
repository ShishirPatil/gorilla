from setuptools import setup, find_packages
import codecs

def read_requirements(filename):
    with open(filename, 'r') as f:
        return f.read().splitlines()

with codecs.open("README.md", "r", "utf-8") as f:
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
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "oss_eval": ["vllm==0.5.0"],
    },
    project_urls={
        "Repository": "https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard",
    },
)
