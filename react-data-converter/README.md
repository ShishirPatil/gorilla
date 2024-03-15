# Gorilla Zoo Data Converter

## Overview

This subdirectory provides a web application for fetching API calls from a API documentation urls into a specified format, to easily generate training points to train a finedtuned LLM model to perform API calls.

## Getting Started

### Installation

1. **Clone the repository**

   Start by cloning the project repository to your local machine:


2. **Install the required packages**


   CD into the server directory and install all the necessary Python packages using pip:
   ```
   pip install -r requirements.txt
   ```

### Configuration

3. **Environment Variables**

   Create a `.env` file in the root directory of the project and define the following variables:

   ```
    OPENAI_API_KEY=...
    GITHUB_TOKEN=...
    GITHUB_CLIENT_ID=...
    GITHUB_CLIENT_SECRET=...
   ```

### Running the Application

1. **Start the Flask server**

   With the environment configured, you can start the application by running:

   ```
   python3 server.py
   ```

2. **Accessing the Web Interface**
    cd into the client folder and start the Next.js development server by running:

    ```
    npm run dev
    ```
    Open your web browser and navigate to `http://localhost:3000/` to access the Gorilla Zoo Data Converter.