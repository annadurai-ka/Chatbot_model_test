from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

# Import your chatbot function
from chatbot_model import chatbot

# FastAPI app initialization
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the request structure
class ChatRequest(BaseModel):
    asin: str
    question: str

# API endpoint to interact with the chatbot
@app.post("/chat/")
async def chat_endpoint(request: ChatRequest):
    try:
        answer = chatbot(request.asin, request.question)
        return {"asin": request.asin, "question": request.question, "answer": answer}
    except Exception as e:
        logger.error(f"Error processing the request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)

