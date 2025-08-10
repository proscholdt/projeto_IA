from services.authenticationService import autentication_pinecone
from pinecone import ServerlessSpec

pc = autentication_pinecone()

def create_index(name: str):
    response = pc.create_index(
        name=name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")

        )
    return response


def list_index():
    response = pc.list_indexes()
    return response.to_dict()


def detail_index(name: str):
    response=pc.describe_index(name=name)
    return response.to_dict()