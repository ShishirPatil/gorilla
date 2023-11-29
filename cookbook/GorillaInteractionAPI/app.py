"""
Gorilla Flask Server Module

This module defines a Flask server that interacts with the Gorilla Large Language Model (LLM).
It includes endpoints to act and react, leveraging the LLM for text generation and processing.

Endpoints:
- /act: Handles GET requests, initializes the LLM, generates a function call, 
        and sends it to the /react endpoint.
- /react: Handles POST requests, receives and processes the generated function call.

Dependencies:
- Flask: Web framework for building the server.
- Flask-CORS: Extension for handling Cross-Origin Resource Sharing.
- requests: Library for making HTTP requests.
- localgorilla: Module containing the functioncall_act function for LLM interaction.

Usage:
Run the module to start the Flask server. The server listens on 'http://localhost:5000/'.

Note:
Adjust the REACT_ENDPOINT and REQUEST_TIMEOUT_IN_SECONDS variables as needed.
"""
import requests
from flask_cors import CORS
from flask import Flask, jsonify, request

from localgorilla import functioncall_act

app = Flask(__name__)
CORS(app)

REACT_ENDPOINT : str = "http://localhost:5000/react"
REQUEST_TIMEOUT_IN_SECONDS : str = 20

@app.route('/act', methods=['GET'])
def route_act():
    """
    Handle GET requests to the '/act' endpoint.
    
    initializes the LLM, generates a function call, and sends it to the /react endpoint.

    Returns:
        Flask Response: JSON response indicating success or error.
    """
    try:
        function_calls = functioncall_act()
        response = requests.post(REACT_ENDPOINT,
                                 json={"generated_call": function_calls},
                                 timeout=REQUEST_TIMEOUT_IN_SECONDS)

        response.raise_for_status()  # Raises HTTPError for bad responses

        return jsonify(response="Success at acting!", function_calls=function_calls)
    except requests.RequestException as e:
        print(f"Error making request to {REACT_ENDPOINT}: {e}")
        return jsonify(response="Error calling /react endpoint")

@app.route('/react', methods=['POST'])
def route_react():
    """
    Handle POST requests to the '/react' endpoint.
    
    Receives and processes the generated function call.

    Returns:
        Flask Response: JSON response indicating success or error.
    """
    try:
        data = request.get_json()
        function_call = data.get("generated_call")

        print(f"Successful at reacting! Received function call: {function_call}")

        # Add more logic based on the function_call variable

        return jsonify(response="Successful at reacting!")

    except requests.RequestException as e:
        print(f"Unexpected error in route_react: {e}")
        return jsonify(response="Error calling /act endpoint")

if __name__ == '__main__':
    app.run(host="0.0.0.0")
