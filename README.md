# AI-Powered CV Analysis and Roadmap Generation

## Overview
This project is a **FastAPI and Flask-based AI-powered system** that processes CVs, extracts relevant skills and experience, and generates a **personalized learning roadmap** based on AI roles such as AI Engineer, AI Data Scientist, AI Manager, and AI Entrepreneur. It integrates OpenAI's LLMs for information extraction and provides a structured plan to enhance AI skills. 

## Features
- **CV Upload and Processing**: Extracts structured details from the CV using OpenAI's API.
- **Role-Based Roadmap Generation**: Creates a customized learning roadmap based on the user's skills, experience, and selected AI career path.
- **MongoDB Database**: Stores user details and extracted insights.
- **Flask-Based Frontend**: A web UI for user interaction and file uploads.
- **Email Integration**: Sends the generated roadmap as a PDF via email.

---

## Tech Stack
- **Backend**: FastAPI
- **Frontend**: Flask, HTML, Bootstrap
- **Database**: MongoDB
- **AI Model**: OpenAI (GPT-4)
- **File Processing**: PyPDF2
- **Vector Database**: Pinecone

---

## Installation & Setup
### Prerequisites
Ensure you have **Python 3.8+** and **pip** installed on your machine.

### 1. Clone the Repository
```bash
 git clone <your-repository-url>
 cd myAIPath  # Navigate to the project directory
```

### 2. Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file and add your API keys:
```env
OPENAI_API_KEY=<your-openai-api-key>
PINECONE_API_KEY=<your-pinecone-api-key>
MONGO_CONNECTION_STRING=<your-mongo-connection-string>
EMAIL_USER=<your-email>
EMAIL_PASSWORD=<your-email-password>
```

### 5. Run the Backend (FastAPI)
```bash
uvicorn main:app --reload
```
This will start the FastAPI server at **http://127.0.0.1:8000**

### 6. Run the Frontend (Flask)
```bash
python frontend.py
```
This will start the Flask web interface at **http://127.0.0.1:5001**

---

## Usage
1. **Upload CV** on the web interface.
2. **Select Role** (AI Manager, AI Engineer, AI Data Scientist, AI Entrepreneur).
3. **Submit** to process and extract insights.
4. **Receive a personalized roadmap** via email.
5. **View roadmap on the web interface.**

---

## API Endpoints
- `POST /upload-cv/`: Uploads and processes a CV.
- `POST /submit-questions/`: Submits a career questionnaire.
- `POST /submit/`: Processes user data and generates a roadmap.

---

