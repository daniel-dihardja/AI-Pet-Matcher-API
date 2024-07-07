import os
import json
from http.server import BaseHTTPRequestHandler
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

            # Call the get_pets_for function from chain module
            res = chain.get_pets_for(message)

            # Prepare the response
            self.send_response(200)
            response = {"message": res}

        except Exception as e:
            self.send_response(500)
            response = {"error": str(e)}

        # Ensure the response is JSON formatted
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))
