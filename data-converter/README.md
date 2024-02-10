# Gorilla Zoo Data Converter

## Overview

This project provides a web application for converting JSON data formats between two specified options. It is designed to assist users in easily transforming their API data from Option 2 format to Option 1 format.

## Getting Started

### Installation

1. **Clone the repository**

   Start by cloning the project repository to your local machine:

2. **Install the required packages**

   Install all the necessary Python packages using pip:

   ```
   pip install -r requirements.txt
   ```

### Configuration

1. **Environment Variables**

   Create a `.env` file in the root directory of the project and define the following variables:

   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GITHUB_TOKEN=your_github_personal_access_token_here
   FORKED_REPO=your_username/forked_repo_name
   MAIN_REPO=original_username/original_repo_name
   ```

2. **Package Requirements**

   The main packages required for this project are listed below. However, they are already included in the `requirements.txt` file for easy installation.

   - Flask
   - python-dotenv
   - requests
   - BeautifulSoup4
   - PyGithub

### Running the Application

1. **Start the Flask application**

   With the environment configured, you can start the application by running:

   ```
   python app.py
   ```

2. **Accessing the Web Interface**

   Open your web browser and navigate to `http://127.0.0.1:5000/` to access the Gorilla Zoo Data Converter.