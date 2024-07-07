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
        results = vector_search(message_embed, pet_type)
        return json.dumps(results, default=str)
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
    res = query_chain.invoke(message)
    return res


def get_matching_pets_for(message, pets):
    llm = get_llm()
    summary_template = load_template("summary_prompt_template.txt")
    summary_prompt_template = PromptTemplate.from_template(summary_template)
    summary_chain = summary_prompt_template | llm

    res = summary_chain.invoke({"user_message": message, "pets": pets})
    return {
        "content": res.content,
        "response_metadata": res.response_metadata,
        "usage_metadata": res.usage_metadata,
    }
