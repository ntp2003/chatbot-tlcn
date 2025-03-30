from openai import OpenAI
from env import env
import chainlit as cl

_client = OpenAI(api_key=env.OPENAI_API_KEY)
_model = "text-embedding-3-small"

def get_embedding(text,model=_model):
    text = text.replace("\n","")
    return _client.embeddings.create(input = [text], model=model).data[0].embedding # call API to get embedding vector of text

def get_list_embedding(texts,model=_model):
    texts = [text.replace("\n","") for text in texts]
    #return _client.embeddings.create(input = texts, model=model).data # call API to get list of embedding vectors of texts
    return [
        item.embedding
        for item in _client.embedding.create(input=texts,model=model).data # call API to get list of embedding vectors of texts 
    ]