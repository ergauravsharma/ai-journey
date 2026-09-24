import os
from dotenv import load_dotenv
from google import genai
import requests

load_dotenv()

#-----Hosted call:Google AI Studio ----
def call_hosted(prompt:str) -> str:

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    response = client.models.generate_content (
        model = "gemini-3.6-flash",
        contents=prompt,
    )
    return response.text

#--- Local Call: Ollama ---
def call_local(prompt:str) -> str:
    response=requests.post(
        "http://localhost:11434/api/generate",
        json={"model":"llama3.2:1b","prompt":prompt,"stream":False},
    )
    return response.json()["response"]

if __name__ =="__main__":
    prompt = "In one sentence, what is Retrieval-Augmented Generation (RAG)?"
    print("=== Hosted(Google AI Studio) ===")
    print(call_hosted(prompt))
    print("===Local(Ollama) ===")
    print(call_local(prompt))
