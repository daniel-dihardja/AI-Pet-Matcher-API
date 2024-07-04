import os
import json
from http.server import BaseHTTPRequestHandler
import requests
from concurrent.futures import ThreadPoolExecutor
from . import chain  # Import chain module from the current directory
from dotenv import load_dotenv

load_dotenv(override=True)


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            # Check for API key in headers
            expected_api_key = os.getenv("API_KEY")
            provided_api_key = self.headers.get("x-api-key")

            if provided_api_key != expected_api_key:
                self.send_response(401)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"error": "Unauthorized: Invalid API Key"}
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return

            # Read and parse the request body
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            post_data = json.loads(post_data)

            # Extract the message parameter from the post_data
            message = post_data.get("message", "")

            # Call the get_matching_pets_from_message function from chain module
            pets = chain.get_pets_for(message)

            # Prepare the request data for /api/get_matching_pets
            request_data = {"message": message, "pets": pets}

            # Check if in debug mode
            if os.getenv("DEBUG") == "True":
                # Return the response directly
                self.send_response(200)
                response = {"message": message, "pets": pets}
            else:
                # Use a ThreadPoolExecutor to send the request to /api/get_matching_pets asynchronously
                with ThreadPoolExecutor() as executor:
                    executor.submit(
                        self.notify_get_matching_pets, request_data, provided_api_key
                    )

                self.send_response(200)
                response = {"message": "Processing initiated and request sent"}

        except Exception as e:
            self.send_response(500)
            response = {"error": str(e)}

        # Ensure the response is JSON formatted
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def notify_get_matching_pets(self, request_data, api_key):
        try:
            # Send the POST request to /api/get_matching_pets
            matching_pets_url = os.getenv("WEBHOOK_SUMMARIZE_URL")
            headers = {"x-api-key": api_key}
            requests.post(matching_pets_url, json=request_data, headers=headers)
        except Exception as e:
            # Log the error, but don't block the main function
            print(f"Error sending request to /api/get_matching_pets: {e}")
