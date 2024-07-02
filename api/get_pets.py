import os
import json
from http.server import BaseHTTPRequestHandler
import requests
from . import chain  # Import chain module from the current directory


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
            pets = chain.get_pets_from_message(message)

            # Check if in development mode
            if os.getenv("MODE") == "development":
                # Return the response directly
                self.send_response(200)
                response = {"message": message, "pets": pets}
            else:
                # Notify the summarize webhook endpoint
                webhook_url = os.getenv("WEBHOOK_SUMMARIZE_URL")
                webhook_response = requests.post(
                    webhook_url, json={"message": message, "pets": pets}
                )

                # Check the response status code from the webhook call
                if webhook_response.status_code == 200:
                    self.send_response(200)
                    response = {"message": "Processing initiated and webhook notified"}
                else:
                    self.send_response(500)
                    response = {
                        "error": f"Webhook notification failed with status code {webhook_response.status_code}"
                    }

        except Exception as e:
            self.send_response(500)
            response = {"error": str(e)}

        # Ensure the response is JSON formatted
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))
