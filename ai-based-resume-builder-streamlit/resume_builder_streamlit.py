
import streamlit as st
import tempfile
import os
from pathlib import Path
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
import requests
from bs4 import BeautifulSoup
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "resume_generator"
os.environ["LANGSMITH_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGSMITH_API_KEY"]="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"
# streamlit_app.py

# === LLM Setup ===
llm = ChatGroq(
    model="gemma2-9b-it",
    temperature=0,
    max_tokens=None,
    timeout=60,
    groq_api_key="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",
)

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

# === Node Functions ===
def load_pdf(state: StoreMessage) -> StoreMessage:
    from langchain_community.document_loaders import PyMuPDFLoader
    loader = PyMuPDFLoader(state["resume_path"])
    docs = loader.load()
    for doc in docs:
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
    sys_msg = SystemMessage(content="You are a resume writer and ATS expert. Rewrite the resume to match the job description and optimize for ATS. Return a well-formatted markdown resume. and dont give the notes")
    user_msg = HumanMessage(content=f"""
My resume:
{state["resume_content"]}

Job description:
{state["job_description"]}
""")
    final = llm.invoke([sys_msg, user_msg])
    state["md_formated"] = final.content
    return state

def llm_review(state: StoreMessage) -> StoreMessage:
    state["valid"] = False
    return state

# === Graph Definition ===
graph = StateGraph(StoreMessage)
graph.add_node("load_pdf", load_pdf)
graph.add_node("get_job_description", get_job_description)
graph.add_node("llm_with_score", llm_with_score)
graph.add_node("create_resume", create_resume)
graph.add_node("llm_review", llm_review)

graph.set_entry_point("load_pdf")
graph.add_edge("load_pdf", "get_job_description")
graph.add_edge("get_job_description", "llm_with_score")

def score_check(state: StoreMessage) -> str:
    return "create_resume" if state["score"] > 70 else "llm_review"

graph.add_conditional_edges("llm_with_score", score_check)
graph.add_edge("create_resume", END)
graph.add_edge("llm_review", END)

workflow = graph.compile()

# === Save Markdown ===
def save_markdown_to_file(md_content: str, file_path: str = "optimized_resume.md") -> str:
    full_path = os.path.abspath(file_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    return full_path

# === Convert Markdown to PDF ===
def pdf_convector(paths):
    import markdown
    import pdfkit
    import re

    if not paths or not isinstance(paths, str) or not os.path.isfile(paths):
        raise ValueError(f"Invalid file path: {paths}")

    with open(paths, "r", encoding="utf-8") as f:
        md_text = f.read()

    contact_section_match = re.search(r'### Contact Information(.*?)###', md_text, re.DOTALL)
    contact_md = contact_section_match.group(1).strip() if contact_section_match else ""

    contact_items = dict()
    for line in contact_md.splitlines():
        match = re.match(r'-\s*(\w+):\s*(.+)', line)
        if match:
            key, value = match.groups()
            contact_items[key.lower()] = value.strip()

    contact_info_html = '<div class="contact-info">\n'
    if "email" in contact_items:
        contact_info_html += f'<strong>📧</strong> <a href="mailto:{contact_items["email"]}">{contact_items["email"]}</a> | '
    if "phone" in contact_items:
        phone = contact_items["phone"].replace(" ", "")
        contact_info_html += f'<strong>📞</strong> <a href="tel:+91{phone}">+91 {contact_items["phone"]}</a> | '
    if "location" in contact_items:
        contact_info_html += f'<strong>📍</strong> {contact_items["location"]} | '
    if "portfolio" in contact_items:
        contact_info_html += f'<strong>🌐</strong> <a href="{contact_items["portfolio"]}">Portfolio</a> | '
    if "linkedin" in contact_items:
        contact_info_html += f'<strong>🔗</strong> <a href="{contact_items["linkedin"]}">LinkedIn</a> | '
    if "github" in contact_items:
        contact_info_html += f'<strong>💻</strong> <a href="{contact_items["github"]}">GitHub</a>'
    contact_info_html += '\n</div><hr>\n'

    html = markdown.markdown(md_text, extensions=["extra", "smarty"])
    full_html = contact_info_html + html

    styled_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px auto;
            max-width: 850px;
            line-height: 1.6;
            color: #333;
            background-color: #fff;
        }}
        h1 {{
            color: #0a2c58;
            font-size: 2em;
            border-bottom: 2px solid #0a2c58;
            padding-bottom: 6px;
            margin-bottom: 10px;
        }}
        h2 {{
            color: #0a2c58;
            font-size: 1.5em;
            border-bottom: 1px solid #ccc;
            padding-bottom: 4px;
            margin-top: 30px;
        }}
        h3 {{
            color: #0a2c58;
            font-size: 1.2em;
            margin-top: 20px;
        }}
        .contact-info {{
            font-size: 0.95em;
            color: #0a2c58;
            margin-bottom: 20px;
        }}
        </style>
    </head>
    <body>
    {full_html}
    </body>
    </html>
    """

    with open("resume_temp.html", "w", encoding="utf-8") as f:
        f.write(styled_html)

    path_to_wkhtmltopdf = r'D:\Help_project_list\resume_builder\reume_builder_checking\ai-resume-creator\wkhtmltox\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    pdfkit.from_file("resume_temp.html", "Kevin_Andrews_Resume.pdf", configuration=config)

# === Streamlit UI ===
st.title("📄 AI Resume Evaluator")

with st.form("resume_form"):
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    url = st.text_input("Paste Job Description URL")
    submitted = st.form_submit_button("Submit")

if submitted and uploaded_file and url:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        path = tmp_file.name

    initial_state = {
        "messages": [],
        "resume_content": "",
        "job_description": "",
        "url": url,
        "md_formated": "",
        "score": 0.0,
        "valid": True,
        "resume_path": path
    }

    final_state = workflow.invoke(initial_state)

    if len(final_state["md_formated"]) > 0:
        st.success(f"✅ Match Score: {final_state['score']}")
        final_path = save_markdown_to_file(final_state["md_formated"])
        pdf_convector(final_path)
        st.markdown(final_state["md_formated"])
        st.download_button("Download Optimized Resume", data=open("Kevin_Andrews_Resume.pdf", "rb"), file_name="Kevin_Andrews_Resume.pdf")
    else:
        st.warning("❌ Resume not satisfied the match criteria.")
