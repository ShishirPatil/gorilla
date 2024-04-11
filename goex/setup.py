# Copyright 2024 https://github.com/ShishirPatil/gorilla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This is the pypi setup file for Gorilla Execution Engine project

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()


setup(
    name="goex",
    version="0.0.2",
    author="Shishir Patil, Tianjun Zhang, Vivian Fang, Noppapon Chalermchockcharoenkit, Roy Huang, Aaron Hao",
    author_email="shishirpatil@berkeley.edu",
    url="https://github.com/ShishirPatil/gorilla/",
    description="Gorilla Execution Engine CLI",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    py_modules=["cli"],
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'goex=cli:main',
        ],
    },
)
