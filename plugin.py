import openai
from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI, HTTPException
import requests
import uvicorn

openai.api_key = "YOUR API KEY"
completion_model = "1.0.0"
api_url = "http://localhost:8000"   

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

class UpsertRequest(BaseModel):
    data: dict
    table_name: str

@app.post("/chat")
async def chat(query: QueryRequest):
    try:
        response = requests.get(f"{api_url}/query?table_name=conversation_history")
        result = response.json()

        conversation_history = ""
        for entry in result:
            conversation_history += entry[0] + "\n" + entry[1] + "\n"

        prompt = conversation_history + query.query
        response = openai.Completion.create(
            engine="davinci",
            prompt=prompt,
            max_tokens=50,
            model=completion_model
        )
        reply = response.choices[0].text.strip()

        # this saves the conversation history
        upsert_data = {
            "data": {
                "user_query": query.query,
                "bot_reply": reply
            },
            "table_name": "conversation_history"
        }

        response = requests.post(f"{api_url}/upsert", json=upsert_data)
        response.raise_for_status()
        
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
