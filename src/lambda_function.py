import json
import src.chain as chain


def lambda_handler(event, context):
    # Extract the message from the event
    body = event.get("body", "{}")
    if isinstance(body, dict):
        message = body.get("message")
    else:
        body = json.loads(body)
        message = body.get("message")

    # Check if the message is provided
    if not message:
        return {"statusCode": 400, "body": json.dumps({"error": "No message provided"})}

    try:
        # Call the get_pets_for function from the chain module
        res = chain.get_pets_for(message)
        return {"statusCode": 200, "body": json.dumps({"response": res})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
