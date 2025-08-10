from pinecone.grpc import PineconeGRPC as Pinecone
import os
from dotenv import load_dotenv

load_dotenv()

def autentication_pinecone():
    
    pc = Pinecone(api_key=os.getenv("api_key_pinecone"))   

    return pc

