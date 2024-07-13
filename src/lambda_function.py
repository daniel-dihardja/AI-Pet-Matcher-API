import json
from . import chain


def lambda_handler(event, context):
    # Debugging: Log the event to understand its structure
    print("Received event:", json.dumps(event))

    try:
        # Check if the event has a body (deployed environment)
        if "body" in event:
            body = json.loads(event.get("body", "{}"))
        else:
            # Local development environment
            body = event

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
    except json.JSONDecodeError as e:
        print("JSON decode error:", str(e))
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON format"})}
    except Exception as e:
        print("General error:", str(e))
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
