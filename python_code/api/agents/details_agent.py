import os
from .utils import get_chatbot_response,get_embedding
import llm_client
from response_cache import cache_by_last_message
from copy import deepcopy

class DetailsAgent():
    def __init__(self, provider=None):
        # dotenv/pinecone are only imported when an agent is actually constructed,
        # not at module import time -- keeps this module importable without either
        # package installed.
        from dotenv import load_dotenv
        load_dotenv()
        from pinecone import Pinecone
        self.client, config = llm_client.get_client(provider=provider)
        self.embedding_client = llm_client.get_embedding_client(provider=provider)
        self.model_name = config["model"]
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
    
    def get_closest_results(self,index_name,input_embeddings,top_k=2):
        index = self.pc.Index(index_name)
        
        results = index.query(
            namespace="ns1",
            vector=input_embeddings,
            top_k=top_k,
            include_values=False,
            include_metadata=True
        )

        return results

    @cache_by_last_message
    def get_response(self,messages):
        # Repeated identical questions ("what are your hours") skip the embedding
        # call, the Pinecone query, and the chat completion entirely -- see
        # response_cache.py. DetailsAgent is stateless Q&A, so caching on the last
        # message alone is safe (unlike OrderTakingAgent, which reads prior turns).
        messages = deepcopy(messages)

        user_message = messages[-1]['content']
        embedding = get_embedding(self.embedding_client,self.model_name,user_message)[0]
        result = self.get_closest_results(self.index_name,embedding)
        source_knowledge = "\n".join([x['metadata']['text'].strip()+'\n' for x in result['matches'] ])

        prompt = f"""
        Using the contexts below, answer the query.

        Contexts:
        {source_knowledge}

        Query: {user_message}
        """

        system_prompt = """ You are a customer support agent for a coffee shop called Merry's way. You should answer every question as if you are waiter and provide the neccessary information to the user regarding their orders """
        messages[-1]['content'] = prompt
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        chatbot_output =get_chatbot_response(self.client,self.model_name,input_messages)
        output = self.postprocess(chatbot_output)
        return output

    def postprocess(self,output):
        output = {
            "role": "assistant",
            "content": output,
            "memory": {"agent":"details_agent"
                      }
        }
        return output

    
