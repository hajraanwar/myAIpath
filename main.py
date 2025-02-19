import cv_extraction, searchCourses, emailagent
from PyPDF2 import PdfReader
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import requests
import pymongo
from fastapi.middleware.cors import CORSMiddleware
import openai
import uuid
import os, json, re
import smtplib
from email.message import EmailMessage


# Initialize FastAPI
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this list with specific origins if you want to restrict access
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)
OPENAI_API_KEY="OPENAI API KEY"

SERPER_API_KEY = "SERPER API KEY"

# Set up API keys for OpenAI and Pinecone
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Set up MongoDB connection
client = pymongo.MongoClient("MONGODB CONNECTION STRING")
db = client["Atomcamp"]
question_roadmap = db['question_roadmap']
CV_collection = db['cv_roadmap']
roadmap = db['roadmap']

# Endpoint: Handle Uploaded CV
@app.post("/upload-cv/")
async def upload_cv(
    cv: UploadFile = File(...),
    name: str = Form(...),
    email: str = Form(...),
    Role: str = Form(..., description="Select role of AI Manager, AI Engineer, AI Entreprenur and AI DataScientist"),
):
    try:
        # Validate file type
        if not cv.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported. Please upload a valid PDF file."
            )

        cv_content_raw = await cv.read()
        if cv.filename.endswith(".pdf"):
            with open("temp.pdf", "wb") as temp_pdf:
                temp_pdf.write(cv_content_raw)
            pdf_reader = PdfReader("temp.pdf")
            cv_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
        else:
            cv_content = cv_content_raw.decode("utf-8")

        extracted_data = cv_extraction.extract_from_cv_with_llm(cv_content)

        skill_level = extracted_data.get("Experience Level")
        user_data = {
            "name": name,
            "email": email,
            "Role": Role,
            "List of technical skills": extracted_data.get("List of technical skills"),
            "skill_level": skill_level,
            "user_id": str(uuid.uuid4())
        }

        search_results = searchCourses.search_courses(
            role=user_data.get("Role"),
            skills=extracted_data.get("List of technical skills", []),
            skill_gaps=extracted_data.get("Weaknesses", []),
            skill_level=extracted_data.get("Experience Level"))


        prompt_cv = f"""
            You are an advanced AI model assisting users in building personalized career roadmaps for their selected role: {user_data.get('Role')}. The user has uploaded their CV for analysis. Use the extracted information, including their job title, technical skills, education, existing projects, and experience level, to create a detailed, tailored roadmap with actionable next steps.

        Steps to Follow:

        if selected role ({user_data.get('Role')}) is **AI Entrepreneur**: Provide recommendations and Include learning paths and projects focusing for startup scaling, AI product market strategies, venture funding, product management courses, product marketing, team management, and AI business use cases.
        if selected role ({user_data.get('Role')}) is **AI Data Scientist**: Include learning paths and projects focusing on data analytics, Tableau, visualization, and dashboard development.

        Educational Background Analysis
        Identify Education Level: Determine the user's highest level of education and its relevance to fields like computer science, AI, machine learning, data science, or programming.
        Assess Technical Knowledge: Analyze their degrees or certifications to identify technical skills such as programming, statistics, or machine learning. Evaluate whether their educational background suggests familiarity with these areas.

        Experience Analysis
        Field Relevance:
        If the user has extensive experience in AI, machine learning, data science, or computer science, recommend advanced resources to enhance expertise.
        If their experience is unrelated to these fields, provide beginner-friendly resources to build foundational skills.

        Custom Recommendations:
        For users with relevant experience, suggest advanced tools, frameworks, and specialized areas to deepen their knowledge.
        For users without relevant experience, guide them toward foundational resources that introduce key concepts in AI and data science.

Based on {user_data.get('List of technical skills')}, {user_data.get('skill_level')} and
  ({user_data.get('Role')}); recommend roadmap using these instructions:
  1- If selected role ({user_data.get('Role')}) is AI Manager is AI Manager then recommend roadmap based on AI strategy and governance, Team leadership and cross-functional collaboration, AI Regulatory compliance, Budgeting and resource allocation for AI initiatives,Knowledge of AI ethics and explainable AI.


 2- if selected role ({user_data.get('Role')}) is AI Data Scientist then recommend roadmap based on Advanced data analytics and visualization,Predictive modeling and machine learning algorithms,Data engineering and ETL (Extract, Transform, Load) processes and Building AI-powered dashboards and tools for stakeholders. 
 
 3- if selected role ({user_data.get('Role')}) is AI Engineer, then recommend roadmap based on AI system design and model deployment, Backend engineering for scalable AI systems, Proficiency in AI frameworks like TensorFlow, PyTorch, and Hugging Face and Developing and optimizing AI pipelines.

        Analyze Skills:
        Categorize the user's technical skills ({extracted_data.get('List of technical skills')}) into beginner, intermediate, or advanced levels by evaluating the number of skills mentioned in their CV, the extent to which these skills have been practically applied in actual projects, and whether their educational background or degrees include coursework where these skills are typically taught. Provide a clear category (Beginner, Intermediate, or Advanced) along with a brief rationale explaining the classification. Additionally, recommend a learning path tailored to their skill level, ensuring it aligns with Saudi Arabia’s job market demands and focuses on enhancing their expertise or building a strong foundation, depending on their categorization.

        Identify Gaps:
            Highlight any skill gaps or areas for improvement relevant to the user's selected role ({user_data.get('Role')}). Base this analysis on the assessment of their technical skills, education, and experience. Clearly categorize them as beginner, intermediate, or advanced based on the evaluation, and then provide specific skill gaps and actionable recommendations tailored to their current level. Ensure that the recommendations align with the demands of the Saudi Arabian job market and industry standards, helping the user understand what they need to improve and how to bridge those gaps effectively.

            Highlight any skill gaps or areas for improvement relevant to the user's selected role ({user_data.get('Role')}). Be sure to take into account the specific demands of the Saudi Arabian market and industry standards.

            Tailored Learning Paths

            Analyze the CV critically and categorize the individual as Beginner, Intermediate, or Advanced based on their technical skills (e.g., programming, algorithms, machine learning), education, and experience. Your assessment should be very fair and objective—if someone claims to be at a higher level but their CV does not reflect it, provide constructive feedback like: "Your CV suggests you are at this level, but based on my assessment, this is where you stand." Clearly explain the rationale behind your categorization, highlighting their strengths, gaps, and potential.

            Provide a tailored learning path for the assessed level:
            Highlight weaknesses {extracted_data.get("Weaknesses")} and strength {extracted_data.get("Strengths")} of the CV and based on this, recommend specific and constructive improvements; and after analyzing the CV Please Suggest relevant courses from trusted platforms like Coursera, Udemy, khan academy, and Udacity. 
            Strictly display the courses below in the following format: Title, Platform and URL Like this: Python for Data Science, AI & Development on Coursera: [Link](https://www.coursera.org/learn/python-for-applied-data-science-ai)

                {search_results}

            **Include this sdaia link for learning suggestion against each user selected role {user_data.get("Role")} https://sdaia.gov.sa/en/Sectors/academy/Pages/default.aspx  **

            Ensure courses are aligned with the user's existing skills ({extracted_data.get('List of technical skills')}) and selected role ({user_data.get('Role')}),education, and experience. Categorize recommendations based on the user's assessed skill level:

            if user's existing skills ({extracted_data.get('List of technical skills')}) is Beginner level: Suggest foundational courses, such as "Introduction to Python," "Basics of Machine Learning," "Foundations of AI," and "Deep Learning for Beginners." Include hands-on project-based courses to help build practical skills gradually.        
            if user's existing skills ({extracted_data.get('List of technical skills')}) is Intermediate level: Recommend advanced courses and certifications covering topics like "Advanced Machine Learning," "Generative AI," "MLOps," "Cloud Computing with AWS," and "Deploying Machine Learning Models." Include hands-on project courses and emphasize practical applications.
            if user's existing skills ({extracted_data.get('List of technical skills')}) is Expert level: Suggest specialized hands-on courses and certifications focusing on cutting-edge topics such as "Advanced Deep Learning," "AI for Strategic Decision-Making," and "AI Applications in Industry." Recommend courses with real-world projects, high-level certifications, and resources that help them excel further in their career.

            Additionally, recommend certifications in demand within the Saudi Arabian market, particularly those aligned with Vision 2030 initiatives and relevant regulatory certifications like SAMA and NCA. Include certifications from global leaders like AWS, Google, Microsoft, or Stanford.
            Encourage exploring AI research and development resources, such as Google Scholar, Papers with Code, Hugging Face, and leading AI platforms from companies like Google, Microsoft, and Amazon, to stay updated on industry trends and innovations. Ensure all recommendations align with the user's career goals and the Saudi Arabian market demands.


            Additional Recommended Certifications:
            Here are certifications that are in demand in the Saudi Arabian market, such as those aligned with Vision 2030 projects, and certifications specific to Saudi Arabia's regulatory environment (e.g., SAMA and NCA certifications).
            Visiting AI R&D from sources like Google Scholar, Paper With Code, Hugging Face, and other prominent AI platforms from Google, Microsoft, and Amazon.

            Practical Projects:
                Based on the user's technical skills ({extracted_data.get('List of technical skills')}), selected role ({user_data.get('Role')}), and existing projects ({extracted_data.get('Existing projects')}), suggest personalized and practical projects that will enhance their practical skills and align with their learning journey. Ensure the projects are distinct from their existing portfolio and tailored to their skill category (beginner, intermediate, or expert). Additionally, align these projects with Saudi Arabia's Vision 2030 initiatives and local industry needs. Refer to Vision 2030 projects and goals to ensure relevance to the Saudi market.
               For each skill category {extracted_data.get("Experience Level")} (beginner, intermediate, expert), recommend at least five unique projects. Please provide a brief explanation for each project in the following format:

            **Practical Project Example Format:**
            - **Project Name:** Provide a descriptive title.
            - **Explanation:** Briefly describe what the project entails, the relevant tech stack, and its expected functionality.
            - **Steps to Build:** Outline the main steps to develop the project, from setup to deployment.

            **Example Projects:**
            - **Project Name:** AI-Powered Sales Forecasting Dashboard
            - **Explanation:** Build a dynamic sales forecasting dashboard using Python, machine learning, and Tableau. This project involves analyzing historical sales data to predict future trends and displaying the results through interactive visualizations.
            - **Steps to Build:**
                1. Gather and clean historical sales data from relevant sources.
                2. Use Python libraries like Pandas and NumPy for preprocessing.
                3. Apply time-series machine learning algorithms (e.g., ARIMA or Prophet) to forecast future sales trends.
                4. Use Tableau to design an interactive dashboard that visualizes historical data and forecasts.

            Ensure all recommendations are actionable and tailored to the user's skills, career goals, and the demands of the Saudi Arabian market, aligning with Vision 2030 initiatives.

            Tailor the project complexity to the user's skill level {extracted_data.get("Experience Level")}:

                if {extracted_data.get("Experience Level")} is Beginner: Focus on fundamental skills with simple use cases, such as basic AI or data visualization projects.
                if {extracted_data.get("Experience Level")} is Intermediate: Suggest medium-complexity projects like predictive analytics, MLOps pipelines, or domain-specific applications in healthcare, logistics, or manufacturing.
                if {extracted_data.get("Experience Level")} is Expert: Provide high-impact, cutting-edge projects such as Generative AI applications, advanced cloud AI deployments, or smart city solutions using AI and IoT, aligned with Vision 2030.
            Ensure all project suggestions are actionable, impactful, and aligned with the Saudi Arabian market's current and future demands. Each user should receive a unique and relevant set of project recommendations based on their individual skills, career goals, and Vision 2030 needs.

            Career Growth Guidance:
                Provide strategies for career progression in the selected role ({user_data.get('Role')}), including leadership opportunities and specialization tracks.
                Offer advice on transitioning into more senior or strategic positions, with a focus on the unique dynamics of the Saudi market (e.g., the increasing role of AI in government, smart cities, and healthcare).
                Also Recommend course from https://www.dama-uk.org/cdmp-info based on the {extracted_data.get('List of technical skills')} and if role ({user_data.get('Role')}) is related to **AI Manager**

            Considerations:
                Ensure recommendations are aligned with industry standards and regulatory requirements in Saudi Arabia, particularly regarding AI, data security, and compliance. For instance, in AI projects involving healthcare, fintech, or government, ensure compliance with the Saudi Data and Artificial Intelligence Authority (SDAIA). Also Recommend learning resources from https://sdaia.gov.sa/en/SDAIA/about/Pages/AboutAI.aspx based on the {extracted_data.get('List of technical skills')} and if role ({user_data.get('Role')}) is  related to AI Manager for legal and regulatory context of AI in Saudi Arabia.
                Also relevant regulations like HIPAA for medical data or SAMA for fintech.
                Ensure all recommendations are tailored to the user's career goals and the Saudi Arabian market              
                Avoid recommending foundational topics (e.g., Python basics, introductory ML, etc.) if the user is already proficient in these areas.
                Give Direct links to courses, learning paths, or career growth sites. Provide only suggestions or course categories.
                Focus on certifications that are recognized in the region, particularly those aligned with the Saudi market and Vision 2030 initiatives.

            Format:
                The roadmap should be structured in Markdown format and should offer clear, actionable next steps.
                Adjust the complexity based on the user existing technical skill level and selected role ({user_data.get('Role')}).
            User Details (from CV):
                Extracted Skills: {extracted_data.get('List of technical skills')}
                Current Job Title: {extracted_data.get('Current job title')}
                Education: {extracted_data.get('Education')}
                Experience Level: {extracted_data.get("Experience Level")}

            Roadmap Structure:
                Overview:
                    Provide an overview of the user's current skills and strengths based on the CV analysis.
                Skill Gaps:
                    Identify areas where the user needs improvement to qualify for their desired role ({user_data.get('Role')}). Focus on local trends and the role's requirements in Saudi Arabia.
                Learning Path:
                    Recommend specific courses, certifications, and learning resources. Prioritize advanced materials that expand on the user existing strengths and fill gaps relevant to the role.
                Practical Projects:
                    Suggest projects that address skill gaps and align with the user professional goals. Focus on projects that are high-impact and locally relevant (aligned with Vision 2030 and local industries).
                Career Growth:
                    Provide personalized advice on career progression, advanced specializations, and leadership development, especially tailored to the Saudi Arabian market and industry trends.

                Please dont mention **user** word in roadmap; pronounce user with name ({user_data.get("name")})

                Just mention name in the start of the roadmap.then use second person pronoun (you, your, yours) later.

                Visit us at Leap:
                 If you want to have a discussion about your roadmap, you can visit our stall Number 381H in Hall 3 at LEAP conference. Our AI experts will meet and guide you further.
                """
        # Get the response from OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt_cv}],
            temperature=0,
            seed=42,
            max_tokens=5000
        )

        # Extract the content and replace the placeholder
        response_text = response.choices[0].message.content
        roadmap = response_text.replace("{search_results}", search_results)    

         
        # roadmap = roadmap +"\n To explore the recommended course, check out these links: \n"+ str(search_results)

        user_data["roadmap"] = response_text
        CV_collection.insert_one(user_data)


        emailagent.email_sender(subject= "Thank You for Using myAIpath; Here is your Personalized Roadmap", body= roadmap, name= user_data.get('name').capitalize(), receiver_email_add= user_data.get('email'))
        return {"message": "CV processed successfully.", "roadmap": roadmap}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint: Handle Questions
@app.post("/submit-questions/")
async def submit_questions(
    name: str = Form(...),
    email: str = Form(...),
    Role: str = Form(...),
    educational_background: str = Form(...),
    years_of_experience: str = Form(...),
    current_job_title: str = Form(...),
    technical_skill_rate: int = Form(..., description="1-Zero Technical Knowledge, 2-Beginner, 3-Intermediate, 4-Advanced, 5-Expert"),
    prefered_field: str = Form(...),
):
    try: 
        if technical_skill_rate == 1:
            skill_level = "Zero Technical Knowledge"
        elif technical_skill_rate == 2:
            skill_level = "Beginner"
        elif technical_skill_rate == 3:
            skill_level = "Intermediate"
        elif technical_skill_rate == 4:
            skill_level = "Advanced"
        else:
            skill_level = "Expert"

        user_data = {
            "name": name,
            "email": email,
            "Role": Role,
            "educational_background": educational_background,
            "years_of_experience": years_of_experience,
            "current_job_title": current_job_title,
            "technical_skills": [],
            "skill_level": skill_level,
            "user_id": str(uuid.uuid4())
        }

        search_results = searchCourses.search_courses(
                role=user_data.get("Role"),
                skills=[],
                skill_gaps=[],
                skill_level=user_data.get("skill_level")
            )
        prompt_ques = f"""
                You are an advanced AI model assisting users in building personalized career roadmaps for their selected role: **{user_data.get('Role')}**. The user has completed a questionnaire detailing their educational background (**{user_data.get('educational_background')}**), prefered field {user_data.get('prefered_field')},  skill level (**{user_data.get('skill_level')}**: beginner, intermediate, or expert), and years of experience (**{user_data.get('years_of_experience')}**). Based on this information, generate a roadmap that aligns with their desired role, addressing skill gaps, practical projects, and career growth strategies tailored to their expertise level and the Saudi Arabian market.

                ### Steps to Follow:   

                - Categorize the user's skills into Zero Technical Knowledge, Beginner,Intermediate, Advanced, Expert levels based on their self-reported skill level (**{user_data.get('skill_level')}**) and align them with the role (**{user_data.get('Role')}**).           
                - Always provide actionable, fair, and personalized advice
                - Highlight their current strengths and competencies relevant to the role.

                2. **Identify Gaps**:
                - Pinpoint skill gaps or areas for improvement to excel in the selected role (**{user_data.get('Role')}**).
                - Ensure alignment with industry trends and job market demands specific to Saudi Arabia, such as Vision 2030 projects and compliance with SDAIA and other local frameworks.

                3. **Learning Path Recommendations** (Tailored by Skill Level):
                    Provide a tailored learning path for the assessed level:

                    Based on skill level {user_data.get("skill_level")}, Please recommend specific and constructive improvements; and Please Suggest relevant courses from trusted platforms like Coursera, Udemy, DataCamp, and Udacity. Strictly display the courses below in the following format: Title, Platform and URL Like this: Python for Data Science, AI & Development on Coursera: [Link](https://www.coursera.org/learn/python-for-applied-data-science-ai)

                    {search_results}


                    **Include this sdaia link for learning suggestion against each user selected role {user_data.get("Role")} https://sdaia.gov.sa/en/Sectors/academy/Pages/default.aspx  **

                    ### **Skill Levels and Recommendations**

                    - **if {user_data.get("skill_level")} is 1 (Zero Knowledge):**  
                    - **Focus:** AI basics and awareness.  
                    - **Path:** Intro to AI, Python basics, IBM Applied AI, Google Cloud Fundamentals.

                    - **if {user_data.get("skill_level")} is 2 (Beginner):**  
                    - **Focus:** Build core skills.  
                    - **Path:** Python, AI/ML basics, data visualization, TensorFlow Developer, IBM AI Practitioner.

                    - **if {user_data.get("skill_level")} is 3 (Intermediate):**  
                    - **Focus:** Practical experience.  
                    - **Path:** Applied AI, model deployment, AWS AI/ML Specialist, Google ML Engineer.

                    - **if {user_data.get("skill_level")} is 4 (Advanced):**  
                    - **Focus:** Specialization and leadership.  
                    - **Path:** Advanced AI, scalable deployment, TensorFlow Advanced, AI governance.

                    - **if {user_data.get("skill_level")} is 5 (Expert):**  
                    - **Focus:** Innovation and thought leadership.  
                    - **Path:** Cutting-edge AI, Google AI Residency, OpenAI Scholar, publish and mentor.

                4. **Practical Projects**:

                    Based on the user's skill level ({user_data.get("skill_level")}), selected role ({user_data.get('Role')}), and their education ({user_data.get('educational_background')}) existing portfolio, recommend personalized and practical projects striclty from this ({user_data.get("prefered_field")}) domain that will enhance their skills and align with their learning goals. Ensure the projects are distinct from their existing portfolio and tailored to their skill category (zero-knowledge, beginner, intermediate, advanced, or expert). Additionally, ensure relevance to Saudi Arabia's Vision 2030 initiatives and local industry needs.

                    For each skill category ({user_data.get("skill_level")}), provide at least five unique projects with brief explanations, structured as follows:

                    **Practical Project Example Format:**
                    - **Project Name:** Provide a descriptive title.
                    - **Explanation:** Briefly describe the project, including its objectives, the tech stack to be used, and its expected functionality.
                    - **Steps to Build:** Outline the key steps, from setup to deployment, to guide the development of the project.

                    **Example Projects by Role:**

                    **1. AI Manager**  
                    - **Project Name:** AI Workflow Automation for Enterprises  
                    - **Explanation:** Develop an automated workflow using AI tools to optimize processes such as document classification or resource allocation.  
                    - **Steps to Build:**  
                        1. Identify an enterprise workflow that can benefit from automation.  
                        2. Use Python and tools like TensorFlow or OpenCV to implement AI for specific tasks.  
                        3. Integrate the workflow with project management tools like Jira or Trello for seamless automation.  

                    - **Project Name:** AI Governance and Compliance Framework  
                    - **Explanation:** Design a compliance framework for AI systems adhering to SDAIA guidelines and Vision 2030 regulatory requirements.  
                    - **Steps to Build:**  
                        1. Research regulatory frameworks such as SAMA, SDAIA, and global AI ethics standards.  
                        2. Design a compliance model tailored to local industry needs (e.g., healthcare, finance).  
                        3. Use tools like Power BI to monitor and visualize compliance metrics.  

                    **2. AI Engineer**  
                    - **Project Name:** MLOps Pipeline for Scalable AI Models  
                    - **Explanation:** Build a scalable MLOps pipeline to deploy and monitor machine learning models in real-world applications.  
                    - **Steps to Build:**  
                        1. Set up a CI/CD pipeline using tools like Jenkins or GitHub Actions.  
                        2. Use Docker and Kubernetes for containerization and orchestration.  
                        3. Deploy the model on AWS or Google Cloud and monitor its performance using tools like Prometheus.  

                    - **Project Name:** AI-Powered Predictive Maintenance System  
                    - **Explanation:** Create a system that predicts equipment failure in industries such as manufacturing or oil and gas.  
                    - **Steps to Build:**  
                        1. Collect sensor data and preprocess it for analysis.  
                        2. Use Python and machine learning algorithms (e.g., Random Forest or Neural Networks) to build predictive models.  
                        3. Visualize results using dashboards built in Tableau or Power BI.  

                    **3. AI Entrepreneur**  
                    - **Project Name:** AI Startup Prototype for Healthcare Diagnostics  
                    - **Explanation:** Develop a prototype for an AI tool that performs diagnostics based on patient data, addressing a specific healthcare challenge.  
                    - **Steps to Build:**  
                        1. Research healthcare pain points and validate the startup idea.  
                        2. Develop the prototype using Python and TensorFlow, focusing on key functionalities.  
                        3. Pitch the prototype with a business plan, including market research and financial projections.  

                    - **Project Name:** AI-Driven Market Analysis Tool  
                    - **Explanation:** Build a tool to analyze market trends and customer behavior using natural language processing (NLP).  
                    - **Steps to Build:**  
                        1. Use APIs to collect real-time data from social media and market reports.  
                        2. Apply NLP techniques with libraries like SpaCy or Hugging Face for sentiment analysis.  
                        3. Create visualizations to summarize findings and provide actionable insights.  

                    **4. AI Data Scientist**  
                    - **Project Name:** Customer Segmentation with Machine Learning  
                    - **Explanation:** Perform customer segmentation using clustering algorithms to identify distinct customer groups based on purchasing behavior.  
                    - **Steps to Build:**  
                        1. Collect customer data and preprocess it using Python (Pandas, NumPy).  
                        2. Apply clustering algorithms like K-Means or DBSCAN to segment customers.  
                        3. Visualize segments using libraries like Matplotlib or Tableau.  

                    - **Project Name:** Social Media Sentiment Analysis Dashboard  
                    - **Explanation:** Create a dashboard to monitor public sentiment about a product or brand using social media data.  
                    - **Steps to Build:**  
                        1. Collect social media data using APIs.  
                        2. Preprocess and clean text data with NLP libraries (e.g., NLTK, Hugging Face).  
                        3. Build sentiment analysis models and display results on an interactive dashboard.  

                    **Alignment with Saudi Vision 2030:**  
                    - **AI Manager:** Focus on projects emphasizing compliance, ethics, and smart city implementations.  
                    - **AI Engineer:** Prioritize building scalable systems for healthcare, energy, and logistics.  
                    - **AI Entrepreneur:** Align projects with Vision 2030 initiatives in fintech, healthcare, and smart cities.  
                    - **AI Data Scientist:** Work on predictive models and analytics for local industries, emphasizing energy, finance, and urban planning.  

                    Tailor the project complexity to the user's skill level ({user_data.get("skill_level")}) and prefered ({user_data.get("prefered_field")}) domain:
                    - **Zero-Knowledge:** Recommend simple projects focusing on basic AI or data visualization.  
                    - **Beginner:** Suggest foundational projects such as basic predictive models or exploratory data analysis.  
                    - **Intermediate:** Propose medium-complexity projects, including deploying AI solutions or creating MLOps pipelines.  
                    - **Advanced:** Recommend advanced projects such as generative AI applications, cloud-based AI solutions, or domain-specific innovations.  
                    - **Expert:** Focus on large-scale, cutting-edge initiatives such as AI governance systems, quantum AI applications, or leadership in national AI strategies.  

                    Ensure each recommendation provides actionable, tailored steps to align with the user's skills, role-specific goals, and Vision 2030 priorities.


                5- Career Growth Suggestions
                    General Framework:
                    Provide tailored career growth strategies based on the user's skill level ({user_data.get("skill_level")}) and selected role ({user_data.get('Role')}). Align these strategies with Vision 2030 initiatives and the Saudi Arabian market trends.

                    1. AI Manager:

                    Zero-Knowledge:
                    Gain foundational knowledge about AI concepts and leadership.
                    Focus on understanding AI workflows and ethical considerations.
                    Participate in workshops or seminars on leadership in AI.

                    Beginner:
                    Develop a basic understanding of AI lifecycle management and regulatory compliance (e.g., SDAIA, SAMA).
                    Pursue certifications in project management with an AI focus
                    Work on small-scale AI projects with cross-functional teams.

                    Intermediate:
                    Enhance skills in managing large-scale AI deployments and MLOps workflows.
                    Earn certifications such as "Microsoft Certified: Azure AI Engineer" or "AWS Certified AI/ML Specialist."
                    Lead mid-sized AI projects focused on healthcare, fintech, or energy applications.

                    Advanced:
                    Take on leadership roles in AI ethics, governance, and national AI initiatives.
                    Contribute to Vision 2030 projects in smart cities, fintech, or healthcare.
                    Attend international conferences, publish thought leadership articles, and network with AI industry leaders.

                    Expert:
                    Focus on strategy and innovation in AI across industries.
                    Lead national-level AI initiatives, including governance frameworks and ethical AI.
                    Mentor upcoming AI managers and contribute to policymaking in AI ethics and regulation.

                    2. AI Engineer:

                    Zero-Knowledge:
                    Start with programming basics (e.g., Python) and foundational AI concepts.
                    Take introductory courses
                    Gain basic coding experience through simple projects like data visualization or chatbot creation.

                    Beginner:
                    Build technical expertise in machine learning frameworks like TensorFlow and PyTorch.
                    Earn certifications like "Google TensorFlow Developer" or "AWS Machine Learning Foundations."
                    Work on foundational projects such as image classification or data preprocessing.

                    Intermediate:
                    Focus on deploying scalable AI models and optimizing workflows using MLOps.
                    Take certifications such as "AWS Certified Machine Learning Specialist" or "Google Cloud AI Engineer."
                    Work on domain-specific applications (e.g., predictive maintenance for manufacturing).

                    Advanced:
                    Master advanced concepts like generative AI, reinforcement learning, and large-scale deployments.
                    Build expertise in deploying AI systems for industries like healthcare, logistics, and energy.
                    Publish research or lead open-source AI initiatives.

                    Expert:
                    Lead innovation in AI engineering by contributing to global standards and practices.
                    Mentor teams, optimize AI pipelines, and spearhead advanced AI applications
                    Collaborate on global AI research projects and Vision 2030 initiatives.

                    3. AI Entrepreneur:

                    Zero-Knowledge:
                    Learn the basics of AI applications and business strategies.
                    Research market opportunities and validate startup ideas.

                    Beginner:
                    Build a foundational understanding of AI technology and startup frameworks.
                    Earn certifications in business strategy and AI fundamentals
                    Develop a prototype for an AI tool or service.

                    Intermediate:
                    Focus on scaling AI products, funding strategies, and team management.
                    Pursue certifications
                    Launch an MVP and conduct market testing.

                    Advanced:
                    Expand your startup into new markets by aligning with Vision 2030 sectors like fintech or healthcare.
                    Participate in Saudi entrepreneurship programs and AI accelerator initiatives.
                    Focus on strategic partnerships and investor engagement.

                    Expert:
                    Lead AI-driven innovation by launching large-scale initiatives in emerging domains.
                    Influence policymaking and support national-level entrepreneurial programs.
                    Mentor other entrepreneurs and advocate for AI adoption in the region.

                    4. AI Data Scientist:

                    Zero-Knowledge:
                    Build foundational skills in data analysis and visualization.
                    Take courses like "Introduction to Data Analytics" or "Python for Data Science"
                    Work on small projects like exploring datasets using Python.

                    Beginner:
                    Develop a strong foundation in data wrangling, machine learning basics, and visualization tools.
                    Earn certifications like "Google Data Analytics Professional Certificate" or "IBM Data Science Certificate."
                    Work on projects like customer segmentation or exploratory data analysis.

                    Intermediate:
                    Focus on advanced data analysis techniques, predictive modeling, and domain-specific applications.
                    Take certifications such as "Advanced Data Science with Python" or "AWS Data Analytics."
                    Work on real-world projects like churn prediction or fraud detection.

                    Advanced:
                    Develop expertise in big data, deep learning, and model optimization.
                    Pursue certifications in advanced AI techniques 
                    Contribute to large-scale AI initiatives in healthcare or smart cities.

                    Expert:
                    Lead innovation in data science by mentoring teams and publishing research.
                    Spearhead AI initiatives for predictive analytics in national projects like energy optimization.
                    Collaborate on global research and drive data science applications in emerging domains.



                - **Saudi Market-Specific Focus**:
                - Align AI initiatives with Vision 2030 goals in sectors like smart cities, healthcare, energy, and fintech.
                - Include compliance with local regulations (e.g., SDAIA, SAMA).
                - Encourage participation in Saudi-based AI events, mentorship programs, or government initiatives.

                Format:
                The roadmap should be structured in Markdown format and should offer clear, actionable next steps.
                Adjust the complexity based on the user skill level {user_data.get('skill_level')} and selected role ({user_data.get('Role')}).

                Considerations:
                    Ensure recommendations are aligned with industry standards and regulatory requirements in Saudi Arabia, particularly regarding AI, data security, and compliance. For instance, in AI projects involving healthcare, fintech, or government, ensure compliance with the Saudi Data and Artificial Intelligence Authority (SDAIA). Also Recommend learning resources from https://sdaia.gov.sa/en/SDAIA/about/Pages/AboutAI.aspx based on the {user_data.get('skill_level')} and if role ({user_data.get('Role')}) is  related to AI Manager for legal and regulatory context of AI in Saudi Arabia.
                    Also relevant regulations like HIPAA for medical data or SAMA for fintech.
                    Ensure all recommendations are tailored to the user's career goals and the Saudi Arabian market              
                    Give Direct links to courses, learning paths, or career growth sites. Provide only suggestions or course categories.
                    Focus on certifications that are recognized in the region, particularly those aligned with the Saudi market and Vision 2030 initiatives.

                ### User Details (from Questionnaire):
                - **Current Job Title**: {user_data.get('current_job_title')}
                - **Education Background**: {user_data.get('educational_background')}
                - **Skill Level**: {user_data.get('skill_level')}
                - **Years of Experience**: {user_data.get('years_of_experience')}


                ### Output Structure:
                1. **Overview**:
                - Summarize the user current skills and strengths relative to their role.

                2. **Skill Gaps**:
                - Identify areas needing improvement, with an emphasis on local job market demands.

                3. **Learning Path**:
                - Suggest courses, certifications, and learning resources based on their skill level and role. (give direct link)

                4. **Practical Projects**:
                - Recommend impactful, role-aligned projects tailored to Vision 2030 and Saudi Arabia industry needs.

                5. **Career Growth**:
                - Provide actionable career progression strategies, including leadership pathways and regional networking opportunities.

                Please dont mention **user** word in roadmap; pronounce user with name ({user_data.get("name")})
                Just mention name in the start of the roadmap.then use second person pronoun (you, your, yours) later

                Visit us at Leap:
                If you want to have a discussion about your roadmap, you can visit our stall Number 381H in Hall 3 at LEAP conference. Our AI experts will meet and guide you further.

                This roadmap is based on the information that you have provided through answers to a few questions. If you need a more personalized roadmap, we would suggest you to use this platform while having your CV ready to be uploaded.

                """

        # Get the response from OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o",
            seed= 42,
            messages=[{"role": "system", "content": prompt_ques}],
            temperature=0,
            max_tokens=5000
        )

        # Extract the content and replace the placeholder
        response_text = response.choices[0].message.content
        roadmap = response_text.replace("{search_results}", search_results)

        # roadmap = roadmap +"\n To explore the recommended course, check out these links: \n"+ str(search_results)
        user_data["roadmap"] = roadmap

        # Insert into the database
        question_roadmap.insert_one(user_data)

        emailagent.email_sender(subject= "Thank You for Using myAIpath; Here is your Personalized Roadmap", name= user_data.get('name'), body= roadmap, receiver_email_add= user_data.get('email'))
        return {"message": "Questions processed successfully.", "roadmap": roadmap}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)