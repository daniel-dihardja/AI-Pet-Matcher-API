import os
import pymongo
import certifi
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv(override=True)


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


def get_pets_from_message(message):
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL"),
        api_key=os.getenv(
            "OPENAI_API_KEY",
        ),
        temperature=0,
    )
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


def get_matching_pets_from_message(message):
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL"),
        api_key=os.getenv(
            "OPENAI_API_KEY",
        ),
        temperature=0,
    )
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


if __name__ == "__main__":
    email = """
    Sehr geehrtes Tierheim Team,

    mein Name ist Jon Goyason und ich interessiere mich sehr für die Adoption einer Katze aus Ihrem Tierheim. Ich habe Erfahrung mit Katzen und bin bereit, einem neuen Haustier ein liebevolles Zuhause zu bieten.

    Hier ein paar Informationen zu mir:

    Wohnsituation: Ich wohne allein in einer katzenfreundlichen Wohnung mit einem gesicherten Balkon.
    Erfahrung mit Katzen: Ich hatte bereits zwei Katzen, die beide ein hohes Alter erreichten.
    Arbeitszeit: Ich arbeite von zu Hause aus, sodass ich viel Zeit für die Katze habe.
    Andere Haustiere: Ich habe derzeit keine anderen Haustiere.
    Ich würde mich freuen, das Tierheim zu besuchen, um die Katzen kennenzulernen und den Adoptionsprozess zu besprechen. Vielen Dank für Ihre Zeit und Ihre Hilfe.

    Mit freundlichen Grüßen,
    Jon Goyason
    """

    res = get_matching_pets_from_message(email)
    print(res)
