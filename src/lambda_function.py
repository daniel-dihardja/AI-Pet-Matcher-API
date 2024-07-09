import json
from . import chain


def lambda_handler(event, context):
    # Debugging: Log the event to understand its structure
    print("Received event:", json.dumps(event))

    try:
        # Parse the body as JSON
        body = json.loads(event.get("body", "{}"))

        # Extract the message from the parsed body
        message = body.get("message")

        # Debugging: Log the extracted message
        print("Extracted message:", message)

        # Check if the message is provided
        if not message:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No message provided"}),
            }

        # Call the get_pets_for function from the chain module
        res = chain.get_pets_for(message)
        print("Response:", res)
        return {"statusCode": 200, "body": json.dumps({"response": res})}
    except Exception as e:
        print("General error:", str(e))
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
