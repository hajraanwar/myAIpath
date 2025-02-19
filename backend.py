from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.agents import initialize_agent, Tool
from langchain.tools import BaseTool
from langchain.schema import SystemMessage
from langchain.prompts import MessagesPlaceholder
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor
from PyPDF2 import PdfReader
from langchain.chat_models import ChatOpenAI
import json
import re
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import pymongo
import pinecone
from fastapi.middleware.cors import CORSMiddleware
from langchain.memory import ConversationBufferMemory
from langchain_community.embeddings import OpenAIEmbeddings
import openai
import uuid
import os
from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from pymongo import MongoClient
from bson import ObjectId




# Initialize FastAPI
app = FastAPI()

# Configure CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI API setup
OPENAI_API_KEY="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"
PINECONE_API_KEY = "pcsk_3PLUCL_9mSkjTp58gdepdXs7b3PKvyBtsk3GGVVkp4tpLCcoY6Te9E14CqhmzWCzEh8thB"  # Your original Pinecone API key

# Set up API keys for OpenAI and Pinecone
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
os.environ['PINECONE_API_KEY'] = PINECONE_API_KEY


# MongoDB setup
client = MongoClient("mongodb+srv://test:iGB9cjqxOKy9a2hb@atomcamp-test.mofqx.mongodb.net/chatbot?retryWrites=true&w=majority&tls=true")
db = client["Atomcamp"]
collection = db["myAIPath"]

# Helper to encode ObjectId for JSON responses
def encode_mongo_obj(data):
    if "_id" in data:
        data["_id"] = str(data["_id"])
    return data

# Function to extract data from CV using OpenAI
async def extract_from_cv_with_llm(cv_content: str):
    try:
        prompt = f"""Extract these details from the provided CV as a JSON object:
        {{
        "Full Name": "",
        "Email Address": "",
        "Highest level of education": "",
        "Field of study": "",
        "Current job title": "",
        "Industry experience": "",
        "Strengths": "",
        "Weaknesses": "Provide technical weaknesses based on the CV content. Focus on gaps in technical skills, certifications, or project experience.",
        "Existing projects": "",
        "experience_with_online_learning": "",
        "List of technical skills": []
        }}
        CV Content:
        {cv_content}
        """

        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # Ensure the model name is correct
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )

        # Extract the content from the response
        response_text = response.choices[0].message.content  # Access the content correctly
                
        # Validate and extract JSON using regex
        json_match = re.search(r"{.*}", response_text, re.DOTALL)
        if not json_match:
            raise ValueError("Response does not contain a valid JSON object.")

        # Parse JSON data
        json_data = json.loads(json_match.group(0))
        return json_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting data from CV: {str(e)}")

@app.post("/submit/")
async def submit_questionnaire(
    name: str = Form(...),
    email: str = Form(...),
    current_education: str = Form(...),
    employed: bool = Form(...),
    job_title: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    career_aspiration: str = Form(...),
    reason_for_learning_ai: str = Form(...),
    preferred_industry: str = Form(...),
    shift_to_ai: bool = Form(...),
    current_career_problem: Optional[str] = Form(None),
    implementation_details: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    Save questionnaire responses and optionally process a CV file.
    """
    data = {
        "name": name,
        "email": email,
        "current_education": current_education,
        "employed": employed,
        "job_title": job_title,
        "industry": industry,
        "career_aspiration": career_aspiration,
        "reason_for_learning_ai": reason_for_learning_ai,
        "preferred_industry": preferred_industry,
        "shift_to_ai": shift_to_ai,
        "current_career_problem": current_career_problem,
        "implementation_details": implementation_details,
    }

    if file:
        
             # Read and decode CV content
        try:
            cv_content_raw = await file.read()
            if file.filename.endswith(".pdf"):
                # Extract text from PDF
                with open("temp.pdf", "wb") as temp_pdf:
                    temp_pdf.write(cv_content_raw)
                pdf_reader = PdfReader("temp.pdf", encoding="ISO-8859-1")
                cv_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
            else:
                # Assume it's a plain text file
                cv_content = cv_content_raw.decode("utf-8")
                print(cv_content)
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Uploaded CV must be a valid UTF-8 text file or PDF.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading CV: {str(e)}")

        #     # Debugging file properties
        #     print(f"Filename: {file.filename}, Content Type: {file.content_type}")

        #     # Validate the file
        #     if not file.filename or not file.filename.endswith(".pdf"):
        #         raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

        #     if not file.content_type or file.content_type != "application/pdf":
        #         raise HTTPException(status_code=400, detail="Invalid content type. Only PDF files are allowed.")

        #     # Process the PDF file
        #     with open("temp.pdf", "wb") as temp_pdf:
        #         temp_pdf.write(await file.read())
        #     pdf_reader = PdfReader("temp.pdf")
        #     cv_content = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
        #     cv_content = cv_content.decode("utf-8")
        #     # Log successful processing
        #     print("File processed successfully!")

        # except Exception as e:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"Error processing uploaded PDF file: {str(e)}"
        #     )
    else:
        raise HTTPException(status_code=400, detail="No file was uploaded.")

    # if file:
    #     try:
    #         # Read file content
    #         cv_content_raw = await file.read()

    #         # Debug file details
    #         print(f"Filename: {file.filename}, Content Type: {file.content_type}")

    #         # Check for valid file types
    #         if file.content_type not in ["application/pdf", "text/plain"]:
    #             raise HTTPException(status_code=400, detail="Only PDF or plain text files are allowed.")

    #         if file.filename.endswith(".pdf"):
    #             # Save and read PDF content
    #             with open("temp.pdf", "wb") as temp_pdf:
    #                 temp_pdf.write(cv_content_raw)
    #             pdf_reader = PdfReader("temp.pdf")
    #             cv_content = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
    #         else:
    #             # Decode plain text file
    #             cv_content = cv_content_raw.decode("utf-8")

    #     except UnicodeDecodeError:
    #         raise HTTPException(status_code=400, detail="Uploaded CV must be a valid UTF-8 text file or PDF.")
    #     except Exception as e:
    #         raise HTTPException(status_code=400, detail=f"Error processing uploaded file: {str(e)}")


        # Extract structured data from CV using OpenAI
        try:
            extracted_info = await extract_from_cv_with_llm(cv_content)
            data["cv_extracted_info"] = extracted_info
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting data from CV: {str(e)}")

    # Save data to MongoDB
    try:
        result = collection.insert_one(data)
        data["_id"] = str(result.inserted_id)
        return {"message": "Submission successful!", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database insertion failed: {str(e)}")
