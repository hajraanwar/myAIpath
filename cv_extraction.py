import openai,re
import json, os
from fastapi import HTTPException

OPENAI_API_KEY="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"
# Set up API keys for OpenAI and Pinecone
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY


def extract_from_cv_with_llm(cv_content: str):
    try:
        prompt = f"""Extract the following details from the CV:
        {{
        "Full Name": "",
        "Email Address": "",
        "Education": "Extract all education details, including degrees, diplomas, certifications, field of study, institutions attended, and graduation years if available.",
        "Field of study": "",
        "Current job title": "",
        "Industry experience": "",
        "Strengths": "",
        "Weaknesses": "Provide technical weaknesses based on the CV content. Focus on gaps in technical skills, certifications, or project experience.",
        "Existing projects": "",
        "experience_with_online_learning": "",
        "List of technical skills": "Extract all explicitly mentioned technical skills. If not explicitly mentioned, infer technical skills from job descriptions, projects, and experience in the CV.",
        "Experience Level": "Beginner, Intermediate, or Expert based on CV details",
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


        json_match = re.search(r"{.*}", response_text, re.DOTALL)
        if not json_match:
            raise ValueError("Failed to extract JSON from response.")

        return json.loads(json_match.group(0))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting data: {str(e)}")
