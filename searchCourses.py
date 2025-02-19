import requests

SERPER_API_KEY = "8e0c1fe50a2a55129c6c85f06672560c874f32e4"

def search_courses(role: str, skills: list, skill_gaps: list, skill_level: str):
    """Search for relevant courses based on role, skills, technical skill gaps, and skill level using Serper API."""
    all_courses = []
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    # Ensure skills and skill_gaps are lists and not strings
    if isinstance(skills, str):
        skills = [skills]
    if isinstance(skill_gaps, str):
        skill_gaps = [skill_gaps]

    # Define topics based on role, skills, and skill gaps
    topics = set(skills + skill_gaps)

    if role.lower() == "ai engineer":
        topics.update(["AI", "Machine Learning", "MLOps", "Deep Learning"])
    elif role.lower() == "ai manager":
        topics.update(["AI Project Management", "AI Ethics", "AI Governance"])
    elif role.lower() == "ai entrepreneur":
        topics.update(["AI Startup", "Venture Funding", "Product Management"," Hiring and Managing Tech team", "product lifecycle", "AI Business Use Cases"])
    elif role.lower() == "ai data scientist":
        topics.update(["Data Analytics", "Tableau", "Data Visualization", "Python for Data Science", "Machine Learning for Data Science", "Data Management","Basics of Data Engineering"])

    for topic in topics:
        query = f"{topic} {skill_level} level online course certification 2024 site:coursera.org OR site:udemy.com OR site:datacamp.com OR site:edx.org OR site:udacity.com OR site:microsoft.com/learn OR site:google.com/learning"
        try:
            response = requests.post(
                "https://google.serper.dev/search",
                headers=headers,
                json={"q": query, "num": 2}
            )
            search_result = response.json()

            for result in search_result.get('organic', []):
                url = result.get('link')

                if any(platform in url.lower() for platform in ['coursera', 'udemy', 'udacity', 'microsoft', 'google', 'Github', 'Datacamp']):
                    platform = next((p for p in ['Coursera', 'Udemy', 'Udacity', 'Datacamp', 'Microsoft', 'Google', 'Github'] 
                                  if p.lower() in url.lower()), 'Online Platform')
                    title = result.get('title', '').replace('[', '(').replace(']', ')')
                    all_courses.append(f"- **{title}**\n  - Platform: {platform}\n  - URL: {url}")

        except Exception as e:
            print(f"Error searching for {topic}: {str(e)}")
            continue
        print(all_courses)            
    return "\n".join(all_courses) if all_courses else "No specific courses found"
