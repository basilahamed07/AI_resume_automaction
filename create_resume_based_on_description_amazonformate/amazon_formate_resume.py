#helper function for convert to pdf

# healper function for create convert the resumen cont from md formate

import argparse
import markdown
import os
import subprocess
import tempfile
import pdfkit

# Load the ATS-friendly CSS for Amazon resumes
AMAZON_ATS_CSS = """
/* ATS-Friendly Resume CSS for Amazon Applications */

@page {
    margin: 0.5in;
    size: letter portrait;
}

body {
    font-family: 'Calibri', 'Arial', sans-serif;
    font-size: 11pt;
    line-height: 1.4;
    color: #333333;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 8.5in;
    margin: 0 auto;
    padding: 0.25in;
}

/* Name and Header */
h1 {
    font-size: 18pt;
    font-weight: bold;
    color: #232f3e; /* Amazon blue */
    margin-bottom: 0.1in;
    text-align: center;
}

/* Contact Information */
p:first-of-type {
    text-align: center;
    margin-bottom: 0.3in;
    font-size: 10pt;
}

/* Section Headings */
h2 {
    font-size: 14pt;
    font-weight: bold;
    color: #232f3e; /* Amazon blue */
    margin-top: 0.3in;
    margin-bottom: 0.1in;
    padding-bottom: 0.05in;
    border-bottom: 1px solid #888;
}

/* Sub-headings (job titles, education degrees) */
h3 {
    font-size: 11pt;
    font-weight: bold;
    margin-top: 0.2in;
    margin-bottom: 0.05in;
}

/* Job details */
h3 + p {
    margin-top: -0.05in;
    margin-bottom: 0.1in;
}

/* Lists */
ul {
    margin-top: 0.05in;
    margin-bottom: 0.15in;
    padding-left: 0.2in;
}

li {
    margin-bottom: 0.05in;
    list-style-type: disc;
}

/* Emphasis for company names and skills */
strong {
    font-weight: bold;
}

/* Ensure proper text wrapping */
p, li {
    word-wrap: break-word;
}
"""

# ATS-friendly HTML template for Amazon resumes
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Amazon Resume</title>
    <style>
        {css}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""

def extract_name(content):
    """Attempt to extract the name from the markdown content"""
    lines = content.split('\n')
    for line in lines:
        if line.strip().startswith('# '):
            return line.strip()[2:].strip()
    return "Professional Resume"

def convert_md_to_html(md_content):
    """Convert markdown content to HTML with Amazon ATS-friendly styling"""
    html_content = markdown.markdown(md_content)
    name = extract_name(md_content)
    return HTML_TEMPLATE.format(name=name, content=html_content, css=AMAZON_ATS_CSS)


def save_markdown_to_file(md_content, filename="resume.md"):
    """Save markdown content to a file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
        return filename
    except Exception as e:
        print(f"Error saving markdown file: {e}")
        return None

def pdf_converter(markdown_path, output_path="amazon_resume.pdf"):
    """Convert markdown file to PDF"""
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        html_content = convert_md_to_html(md_content)
        print("inside the pdf_converter")
        print("html content")
        return convert_html_to_pdf(html_content, output_path)
    except Exception as e:
        print(f"Error in PDF conversion: {e}")
        return False

def convert_html_to_pdf(html_content, output_path):
    """Convert HTML content to PDF using pdfkit with local wkhtmltopdf."""
    path_to_wkhtmltopdf = r'D:\Help_project_list\resume_builder\reume_builder_checking\ai-resume-creator\wkhtmltox\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

    options = {
        'enable-local-file-access': '',
        'print-media-type': '',
        'no-background': '',
        'margin-top': '12mm',
        'margin-bottom': '12mm',
        'margin-left': '12mm',
        'margin-right': '12mm',
        'page-size': 'Letter',
        'dpi': 300,
        'disable-smart-shrinking': ''
    }

    try:
        pdfkit.from_string(html_content, output_path, configuration=config, options=options)
        print(f"✅ ATS-friendly Amazon resume PDF successfully created at: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        return None


#ai workflow

#declare the workflow of the scrio using the langgraph 

# domin maine specification

#prompt optimizing

# this one for ai workflow for create the resume content

#gpt code 

# === Imports ===
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START

import requests
from bs4 import BeautifulSoup

# === Define State ===
class StoreMessage(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    resume_content: str
    job_description: str
    url: str
    md_formated: str
    score: float
    valid: bool
    resume_path: str

# === Import your LLM instance ===
# Define or import your LLM here (like from LangChain)
# For example:
paths = r"c:\Users\basilahamed.h\Downloads\DOC-20241108-WA0011. (3).pdf"
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="gemma2-9b-it",
    temperature=0,
    max_tokens=None,
    timeout=60,
    groq_api_key="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",
    # other params...
)

# === Define Nodes ===
def load_pdf(state: StoreMessage) -> StoreMessage:
    from langchain_community.document_loaders import PyMuPDFLoader
    path = state["resume_path"]
    # print("//// pdf path ")
    # print(path)
    # print("//// pdf path ")
    loader = PyMuPDFLoader(path)
    docs = loader.load()
    for doc in docs:
        # print(doc.page_content)
        state["resume_content"] += doc.page_content
    return state

def get_job_description(state: StoreMessage) -> StoreMessage:
    response = requests.get(state["url"])
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        job_description = soup.get_text(separator="\n", strip=True)
        state["job_description"] = job_description
        return state
    else:
        raise Exception(f"Failed to fetch URL: {response.status_code}")

def llm_with_score(state: StoreMessage) -> StoreMessage:
    sys_msg = SystemMessage(content="You are an expert resume evaluator. Assess the resume's match to the job description and return a score from 0 to 100.")
    user_msg = HumanMessage(content=f"""
{state['resume_content']}

Job Description:
{state['job_description']}

Give the match score out of 100. Only return the number.
""")
    result = llm.invoke([sys_msg, user_msg])
    try:
        state["score"] = float(result.content.strip())
    except ValueError:
        state["score"] = 0.0
    return state

def create_resume(state: StoreMessage) -> StoreMessage:
    sys_msg = SystemMessage(content="""


              
You are an expert Large Language Model specializing in professional resume formatting for job applications.

Your task is to take the user's raw resume content and convert it into a professionally structured, ATS-optimized Markdown resume, following the exact format and section order outlined below:

### importent 
- if you have any experance mean add that experance  else dont have experiance experian must have the company name and date duraction of the company name make sure...
                            
🔹 OUTPUT STRUCTURE (Follow This Exact Order)

# Full Name

Contact Information  
Single-line format:  
Location | [Email](mailto:example@email.com) | Phone | [LinkedIn](https://linkedin.com/in/username)

- All links must be valid and clickable in Markdown.
- No extra commentary.

## [Detected Domain Name]

Detect the most relevant professional domain based on skills, experience, certifications, education, or projects. Print it as a second-level heading (##) directly under contact information.  
(No label like "Domain:" — just the domain title.)

## Summary

Write a concise 2–4 sentence summary:
- Brief professional background and experience level
- Technical focus and career goals
- (Optional) Tie to leadership, ownership, or customer focus themes if applicable

## Skills

Group skills logically (e.g., **Languages**, **Frameworks**, **Cloud**, **Tools**).

Example:
- **Languages**: Python, Java
- **Frameworks**: React, Django

## Experience
(Only include if user provided experience.)

For each job:
### [Job Title]  
**[Company Name]** | MM/YYYY – MM/YYYY  
- Bullet describing quantifiable achievement  
- Bullet showcasing impact or leadership  

## Certifications
(Only include if user provided certifications.)

- Bullet list of certifications.

## Education

### [Degree Name]  
**[University Name]** | MM/YYYY – MM/YYYY  
- (Optional) GPA, notable coursework, or academic achievements

## Projects
(Only include if user provided projects.)

For each project:
### [Project Title]  
- What it is + technology used  
- Impact or measurable outcome

## Other
(Any additional information provided by the user that doesn't fit other sections.)

## Languages

- Bullet list of languages spoken.

## Hobbies

- Bullet list of hobbies if provided.

## Interests

- Bullet list of interests if provided.

🔹 DOMAIN DETECTION RULES

Auto-detect the most fitting domain title based on:
- Skills
- Experience
- Certifications
- Projects
- Keywords

Examples:
- React, Node.js → Full Stack Developer
- Threat Detection, SIEM → Cybersecurity Analyst
- Machine Learning, Pandas → Data Scientist

🔹 FORMATTING RULES

- Use **bold** for job titles, company names, skill headers, and domain name
- Use `-` (dash) for bullet points
- No tables, checkboxes, emojis, or images
- Consistent date format: MM/YYYY
- Hyperlinks must be functional and Markdown-compliant
- Use `#` for name, `##` for sections, `###` for job/project/education entries
- Resume must be clean Markdown and 100% ATS-compliant
- Do not add explanations or external notes in the output

🔹 TECHNICAL CONSTRAINTS

- Return only the final resume in Markdown format
- Include all content from user input (no omissions)
- If a section's content is not provided, skip that section (do not include empty headers)


    """)
    user_msg = HumanMessage(content=f"""
My resume:
{state["resume_content"]}

Job description:
{state["job_description"]}
""")
    final = llm.invoke([sys_msg, user_msg])
    state["md_formated"] = final.content
    return state

# def llm_review(state: StoreMessage) -> StoreMessage:
#     state["valid"] = False
#     return state



# === Graph Definition ===
graph = StateGraph(StoreMessage)

graph.add_node("load_pdf", load_pdf)
graph.add_node("get_job_description", get_job_description)
graph.add_node("llm_with_score", llm_with_score)
graph.add_node("create_resume", create_resume)
# graph.add_node("llm_review", llm_review)

graph.add_edge(START,"load_pdf")

graph.add_edge("load_pdf", "get_job_description")
graph.add_edge("get_job_description", "llm_with_score")

def score_check(state: StoreMessage) -> str:
    return "create_resume" if state["score"] > 70 else END

graph.add_conditional_edges("llm_with_score", score_check)

graph.add_edge("create_resume", END)
# graph.add_edge("llm_with_score", END)

workflow = graph.compile()





# app.py

from io import BytesIO
import streamlit as st
import os
import tempfile

# from your_module import workflow, save_markdown_to_file, pdf_converter

st.set_page_config(page_title="Resume Evaluator", layout="centered")
st.title("📄 Resume Evaluator with Job Description")

# Job Description URL
job_url = st.text_input("Enter the Job Description URL",
                        value="https://www.imocha.io/job-description/junior-python-developer")

uploaded_file = st.file_uploader("Upload your resume (PDF only)", type=["pdf"])

# Add a submit button
if uploaded_file and job_url:
    if "processed" not in st.session_state:
        st.session_state.processed = False

    if st.button("🚀 Submit for Evaluation"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            resume_path = tmp_file.name

        with st.spinner("Processing resume..."):
            final_state = workflow.invoke({
                "messages": [],
                "resume_content": "",
                "job_description": "",
                "resume_path": resume_path,
                "url": job_url,
                "md_formated": "",
                "score": 0.0,
                "valid": True
            })

        st.subheader("Score")
        st.write(f"Resume Score: {final_state['score']}")

        if final_state["md_formated"]:
            st.success("✅ Resume is valid. Saving markdown...")

            md_file_path = save_markdown_to_file(final_state["md_formated"])
            pdf_path = pdf_converter(md_file_path)

            with open(pdf_path, "rb") as f:
                st.session_state.pdf_bytes = f.read()
                st.session_state.processed = True

        else:
            st.error("❌ Resume not satisfied based on job description.")
            st.session_state.processed = False

# Show download button ONLY if already processed
if st.session_state.get("processed", False):
    st.download_button(
        "📥 Download PDF",
        data=BytesIO(st.session_state.pdf_bytes),
        file_name="Resume_Output.pdf",
        mime="application/pdf"
    )
