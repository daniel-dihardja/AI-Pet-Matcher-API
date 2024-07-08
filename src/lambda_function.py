import json
from . import chain  # Assuming chain.py is in the same directory as lambda_function.py


def lambda_handler(event, context):
    # Debugging: Log the event to understand its structure
    print("Received event:", json.dumps(event))

    # Extract the body from the event
    body = event.get("body", "{}")

    # Debugging: Log the body to understand its structure
    print("Extracted body:", body)

    # If body is a JSON string, load it as a dictionary
    if isinstance(body, str):
        body = json.loads(body)

    # Extract the inner body and message
    inner_body = body.get("body")
    if isinstance(inner_body, str):
        inner_body = json.loads(inner_body)

    # Debugging: Log the inner body to understand its structure
    print("Parsed inner body:", inner_body)

    # Extract the message from the inner body
    message = inner_body.get("message")

    # Check if the message is provided
    if not message:
        return {"statusCode": 400, "body": json.dumps({"error": "No message provided"})}

    try:
        # Call the get_pets_for function from the chain module
        res = chain.get_pets_for(message)
        return {"statusCode": 200, "body": json.dumps({"response": res})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
