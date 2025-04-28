import streamlit as st
import os
import tempfile
import requests
from bs4 import BeautifulSoup
from typing import Annotated, Dict, Any
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_groq import ChatGroq
import markdown
import pdfkit
import re
import shutil

# Custom CSS
st.set_page_config(page_title="AI Resume Optimizer", layout="wide")
st.markdown("""
<style>
.stApp {
    max-width: 1200px;
    margin: 0 auto;
}
.success-message {
    background-color: #d4edda;
    color: #155724;
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 10px;
}
.error-message {
    background-color: #f8d7da;
    color: #721c24;
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 10px;
}
.info-card {
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# === Define State ===
class StoreMessage(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    resume_content: str
    job_description: str
    url: str
    md_formated: str
    score: float
    valid: bool

def initialize_session_state():
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    if "resume_path" not in st.session_state:
        st.session_state.resume_path = None
    if "job_url" not in st.session_state:
        st.session_state.job_url = ""
    if "optimized_resume" not in st.session_state:
        st.session_state.optimized_resume = ""
    if "score" not in st.session_state:
        st.session_state.score = 0.0
    if "progress" not in st.session_state:
        st.session_state.progress = 0

initialize_session_state()

# === PDF to Markdown Function ===
def pdf_convector(markdown_path):
    # Check if the 'paths' variable is None or not a valid path
    if not markdown_path or not isinstance(markdown_path, str) or not os.path.isfile(markdown_path):
        raise ValueError(f"Invalid file path: {markdown_path}")
    
    # Step 1: Read Markdown content
    with open(markdown_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    
    # Step 2: Extract contact info from markdown using regex
    contact_section_match = re.search(r'### Contact Information(.*?)###', md_text, re.DOTALL)
    contact_md = contact_section_match.group(1).strip() if contact_section_match else ""
    
    # Step 3: Parse contact items
    contact_items = dict()
    for line in contact_md.splitlines():
        match = re.match(r'-\s*(\w+):\s*(.+)', line)
        if match:
            key, value = match.groups()
            contact_items[key.lower()] = value.strip()
    
    # Step 4: Build dynamic contact info line
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
    
    # Step 5: Convert Markdown to HTML
    html = markdown.markdown(md_text, extensions=["extra", "smarty"])
    
    # Step 6: Insert contact info before rendered HTML
    full_html = contact_info_html + html
    
    # Step 7: Style and wrap
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
        p {{
            margin-bottom: 10px;
        }}
        ul {{
            padding-left: 20px;
            list-style-type: disc;
        }}
        li {{
            margin-bottom: 8px;
        }}
        a {{
            color: #0645ad;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        section {{
            margin-bottom: 30px;
        }}
        .contact-info {{
            font-size: 0.95em;
            color: #0a2c58;
            margin-bottom: 20px;
        }}
        hr {{
            margin: 20px 0;
            border: none;
            border-top: 1px solid #ccc;
        }}
        </style>
    </head>
    <body>
    {full_html}
    </body>
    </html>
    """
    
    # Create temporary directory for files
    temp_dir = tempfile.mkdtemp()
    html_path = os.path.join(temp_dir, "resume_temp.html")
    pdf_path = os.path.join(temp_dir, "Optimized_Resume.pdf")
    
    # Step 8: Save to HTML file
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(styled_html)
    
    # Step 9: Try to find wkhtmltopdf path
    if os.path.exists(r'D:\Help_project_list\resume_builder\reume_builder_checking\ai-resume-creator\wkhtmltox\bin\wkhtmltopdf.exe'):
        path_to_wkhtmltopdf = r'D:\Help_project_list\resume_builder\reume_builder_checking\ai-resume-creator\wkhtmltox\bin\wkhtmltopdf.exe'
    else:
        # Try to use system's wkhtmltopdf if available
        path_to_wkhtmltopdf = shutil.which('wkhtmltopdf')
        if not path_to_wkhtmltopdf:
            st.error("wkhtmltopdf not found. Please install it or place it in the 'wkhtmltox/bin' folder.")
            return None
    
    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    pdfkit.from_file(html_path, pdf_path, configuration=config)
    
    return pdf_path

# === Save Markdown to File ===
def save_markdown_to_file(md_content: str, file_path: str = "optimized_resume.md") -> str:
    # Get the absolute path of the file
    full_path = os.path.abspath(file_path)
    
    # Write the content to the file
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return full_path

# === Helper Functions ===
def load_pdf(state: StoreMessage) ->StoreMessage:
    loader = PyMuPDFLoader(state["resume_path"])
    docs = loader.load()
    state["resume_content"] = ""
    for doc in docs:
        state["resume_content"] += doc.page_content
    return state

def get_job_description(state: StoreMessage) -> StoreMessage:
    try:
        response = requests.get(state["url"])
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            job_description = soup.get_text(separator="\n", strip=True)
            state["job_description"] = job_description
        else:
            st.error(f"Failed to fetch URL: {response.status_code}")
            state["job_description"] = ""
    except Exception as e:
        st.error(f"Error fetching job description: {str(e)}")
        state["job_description"] = ""
    return state

def llm_with_score(state: StoreMessage) -> StoreMessage:
    llm = ChatGroq(
        model="gemma2-9b-it",
        temperature=0,
        max_tokens=None,
        timeout=60,
        groq_api_key=state["api_key"],
    )
    
    sys_msg = SystemMessage(content="You are an expert resume evaluator. Assess the resume's match to the job description and return a score from 0 to 100.")
    user_msg = HumanMessage(content=f""" 
    Resume: {state['resume_content']}
    
    Job Description: {state['job_description']}
    
    Give the match score out of 100. Only return the number.
    """)
    
    try:
        result = llm.invoke([sys_msg, user_msg])
        try:
            state["score"] = float(result.content.strip())
        except ValueError:
            state["score"] = 0.0
    except Exception as e:
        st.error(f"Error calculating score: {str(e)}")
        state["score"] = 0.0
    
    return state

def create_resume(state: StoreMessage) -> StoreMessage:
    llm = ChatGroq(
        model="gemma2-9b-it",
        temperature=0,
        max_tokens=None,
        timeout=60,
        groq_api_key=state["api_key"],
    )
    
    sys_msg = SystemMessage(content="You are a resume writer and ATS expert. Rewrite the resume to match the job description and optimize for ATS. Return a well-formatted markdown resume.")
    user_msg = HumanMessage(content=f""" 
    My resume: {state["resume_content"]}
    
    Job description: {state["job_description"]}
    """)
    
    try:
        final = llm.invoke([sys_msg, user_msg])
        state["md_formated"] = final.content
    except Exception as e:
        st.error(f"Error creating optimized resume: {str(e)}")
        state["md_formated"] = ""
    
    return state

# === Streamlit UI ===
st.title("🚀 AI Resume Optimizer")
final_result = {}
with st.container():
    st.markdown("""
    <div class="info-card">
    <h3>How it works:</h3>
    <ol>
        <li>Upload your resume PDF</li>
        <li>Enter the job posting URL</li>
        <li>Enter your Groq API key</li>
        <li>Click "Optimize Resume"</li>
        <li>Download your optimized resume</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    if uploaded_file:
        # Save the uploaded file to a temporary file
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "resume.pdf")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        st.session_state.resume_path = temp_path
        st.success("Resume uploaded successfully!")

with col2:
    st.session_state.job_url = st.text_input("Job posting URL", st.session_state.job_url)
    st.session_state.api_key = st.text_input("Groq API Key", st.session_state.api_key, type="password")

if st.button("Optimize Resume"):
    if not st.session_state.resume_path:
        st.error("Please upload your resume first!")
    elif not st.session_state.job_url:
        st.error("Please enter a job posting URL!")
    elif not st.session_state.api_key:
        st.error("Please enter your Groq API key!")
    else:
        with st.spinner("Processing your resume..."):
            # Define the workflow graph
            graph = StateGraph(StoreMessage)
            
            # Add nodes
            graph.add_node("load_pdf", load_pdf)
            graph.add_node("get_job_description", get_job_description)
            graph.add_node("llm_with_score", llm_with_score)
            graph.add_node("create_resume", create_resume)
            
            # Define edges
            graph.set_entry_point("load_pdf")
            graph.add_edge("load_pdf", "get_job_description")
            graph.add_edge("get_job_description", "llm_with_score")
            
            # Conditional edges
            def score_check(state:StoreMessage) -> str:
                return "create_resume" if state["score"] >= 75 else END
            
            graph.add_conditional_edges("llm_with_score", score_check)
            graph.add_edge("create_resume", END)
            
            # Compile workflow
            workflow = graph.compile()
            
            # Progress bar
            progress_bar = st.progress(0)
            st.session_state.progress = 0
            
            # Execute workflow
            state = {
                "messages": [],
                "resume_content": "",
                "job_description": "",
                "url": st.session_state.job_url,
                "md_formated": "",
                "score": 0.0,
                "valid": True,
                "resume_path": st.session_state.resume_path,
                "api_key": st.session_state.api_key
            }
            
            try:
                # Load PDF
                # state = load_pdf(state)
                # st.session_state.progress = 25
                # progress_bar.progress(st.session_state.progress)
                
                # # Get job description
                # state = get_job_description(state)
                # st.session_state.progress = 50
                # progress_bar.progress(st.session_state.progress)
                
                # # Calculate score
                # state = llm_with_score(state)
                # st.session_state.score = state["score"]
                # st.session_state.progress = 75
                # progress_bar.progress(st.session_state.progress)
                
                # # Create optimized resume if score is good enough
                # if state["score"] >= 75:
                #     state = create_resume(state)
                #     st.session_state.optimized_resume = state["md_formated"]
                final_result = workflow.invoke(state)
                st.session_state.progress = 100
                progress_bar.progress(st.session_state.progress)
                
            except Exception as e:
                st.error(f"Error in workflow: {str(e)}")

# Display results if available
if final_result["score"] > 0:
    st.subheader("Results")
    
    # Score display with color coding
    score = st.session_state.score
    if score >= 80:
        score_color = "green"
    elif score >= 60:
        score_color = "orange"
    else:
        score_color = "red"
    
    st.markdown(f"<h3>Match Score: <span style='color:{score_color}'>{score:.1f}%</span></h3>", unsafe_allow_html=True)
    
    if final_result["score"] >= 75 and st.session_state.optimized_resume:
        st.markdown("### Optimized Resume")
        
        # Display and download markdown
        with st.expander("View Markdown"):
            st.markdown(st.session_state.optimized_resume)
        
        # Save markdown and PDF for download
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Download Markdown"):
                md_path = save_markdown_to_file(st.session_state.optimized_resume)
                with open(md_path, "r") as file:
                    st.download_button(
                        label="Click to Download Markdown",
                        data=file,
                        file_name="optimized_resume.md",
                        mime="text/markdown"
                    )
        
        with col2:
            if st.button("Download PDF"):
                try:
                    with st.spinner("Generating PDF..."):
                        # Save markdown to temp file
                        md_path = save_markdown_to_file(st.session_state.optimized_resume)
                        # Convert to PDF
                        pdf_path = pdf_convector(md_path)
                        if pdf_path and os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as file:
                                st.download_button(
                                    label="Click to Download PDF",
                                    data=file,
                                    file_name="optimized_resume.pdf",
                                    mime="application/pdf"
                                )
                        else:
                            st.error("Failed to generate PDF. Please check if wkhtmltopdf is installed correctly.")
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
    elif final_result["score"] <= 74:
        st.warning("Your resume needs significant improvement to match this job description.")
        st.info("Try uploading a different version of your resume or applying to a job that better matches your skills.")

# Footer
st.markdown("---")
st.markdown("### About this app")
st.markdown("""
This app uses AI to analyze your resume against a job description, calculate a match score, 
and create an optimized version specifically tailored to the job. The optimized resume follows 
ATS (Applicant Tracking System) best practices to help you get past automated screenings.
""")