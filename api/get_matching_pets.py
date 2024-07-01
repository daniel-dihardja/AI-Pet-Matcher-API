import os
import json
from http.server import BaseHTTPRequestHandler
from . import chain


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        expected_api_key = os.getenv("API_KEY")
        provided_api_key = self.headers.get("x-api-key")

        if provided_api_key != expected_api_key:
            self.send_response(401)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"error": "Unauthorized: Invalid API Key"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        post_data = json.loads(post_data)

        # Extract the message parameter from the post_data
        message = post_data.get("message", "")

        # Call the get_matching_pets_from_message function from chain module
        try:
            response_message = chain.get_matching_pets_from_message(message)
            response = {"received_message": response_message}
            self.send_response(200)
        except Exception as e:
            response = {"error": str(e)}
            self.send_response(500)

        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))
