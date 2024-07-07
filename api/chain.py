import os
import pymongo
import certifi
import json
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv(override=True)


def get_llm():
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL"),
        api_key=os.getenv(
            "OPENAI_API_KEY",
        ),
        temperature=0,
    )
    return llm


def get_collection():
    client = pymongo.MongoClient(
        os.environ["ATLAS_MONGODB_URI"], tlsCAFile=certifi.where()
    )
    db = client[os.getenv("DB_NAME")]
    return db[os.getenv("COLLECTION_NAME")]


def get_openai_client():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return client


def get_gpt_embeddings(messages):
    client = get_openai_client()
    response = client.embeddings.create(model="text-embedding-ada-002", input=messages)
    return response.data[0].embedding


@tool
def get_pets(pet_type: str, message: str) -> str:
    """Get all pets of a certain type. valid values for pet_type are 'Hund', 'Katze'"""

    message_embed = get_gpt_embeddings(message)

    try:
        pets = vector_search(message_embed, pet_type)
        return json.dumps(pets, default=str)
    except Exception as e:
        return str(e)


def vector_search(query_vector, filter):
    coll = get_collection()
    pipeline = [
        {
            "$vectorSearch": {
                "index": "pet_vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 150,
                "limit": 5,
            }
        },
        {"$match": {"pet_type": filter}},  # Add your filter criteria here
        {
            "$project": {
                "_id": 0,
                "score": {"$meta": "vectorSearchScore"},
                "name": 1,
                "description": 1,
                "number": 1,
                "neutered": 1,
            }
        },
    ]

    result = coll.aggregate(pipeline)
    return list(result)


def load_template(template_file) -> str:
    with open(template_file, "r") as file:
        system_guide = file.read()
    return system_guide


def format_summary_prompt(pets, user_message):
    output = {"pets": pets, "user_message": user_message}
    return output


def get_pets_for(message):
    """
    Retrieves and summarizes pet information based on the provided message.

    Steps:
    1. Initialize the language model (LLM) and bind the `get_pets` tool.
    2. Load and format the query prompt template.
    3. Create a query chain to generate a prompt, call the LLM with tools, extract arguments, and get pet information.
    4. Load and format the summary prompt template.
    5. Create a summary chain to format the summary prompt and generate a summarized response.
    6. Combine the query and summary chains into one execution chain.
    7. Invoke the chain with the provided message.
    8. Return summarized content, response metadata, and usage metadata.

    Parameters:
    - message (str): The input message used to query and summarize pet information.

    Returns:
    - dict: Summarized content, response metadata, and usage metadata.
    """

    llm = get_llm()
    llm_with_tools = llm.bind_tools([get_pets])
    query_template = load_template("query_prompt_template.txt")
    query_prompt_template = PromptTemplate.from_template(query_template)
    query_chain = (
        query_prompt_template
        | llm_with_tools
        | (lambda x: x.tool_calls[0]["args"])
        | get_pets
    )

    summary_template = load_template("summary_prompt_template.txt")
    summary_prompt_template = PromptTemplate.from_template(summary_template)
    summary_chain = summary_prompt_template | llm

    chain = query_chain | (lambda x: format_summary_prompt(x, message)) | summary_chain

    res = chain.invoke(message)

    return {
        "content": res.content,
        "response_metadata": res.response_metadata,
        "usage_metadata": res.usage_metadata,
    }
