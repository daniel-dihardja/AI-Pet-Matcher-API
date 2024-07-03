import os
import pymongo
import certifi
import json
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


@tool
def get_pets(pet_type: str) -> str:
    """Get all pets of a certain type. valid values for pet_type are 'Hund', 'Katze'"""
    print("pet_type: ", pet_type)

    coll = get_collection()
    query = {"pet_type": pet_type}
    try:
        results = coll.find(query)
        results_list = list(results)
        return json.dumps(results_list, default=str)
    except Exception as e:
        return str(e)


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
