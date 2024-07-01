import os
import json
from http.server import BaseHTTPRequestHandler
import requests  # Ensure requests is installed and added to requirements.txt
from . import chain  # Import chain module from the current directory


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
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
        try:
            response_message = chain.get_matching_pets_from_message(message)
            # Notify the Remix webhook endpoint
            webhook_url = os.getenv("WEBHOOK_URL")
            webhook_response = requests.post(
                webhook_url, json={"message": response_message}
            )

            if webhook_response.status_code == 200:
                self.send_response(200)
                response = {"message": "Processing initiated and webhook notified"}
            else:
                self.send_response(500)
                response = {"error": "Webhook notification failed"}

        except Exception as e:
            self.send_response(500)
            response = {"error": str(e)}

        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))
