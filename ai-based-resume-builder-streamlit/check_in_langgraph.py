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
    resume_content: str =""
    job_description: str =""
    url: str =""
    md_formated: str =""
    score: float = 0.0
    valid: bool = False

# === Import your LLM instance ===
# Define or import your LLM here (like from LangChain)
# For example:
paths = r"D:\Help_project_list\resume_builder\reume_builder_checking\ai-resume-creator\Kevin_Andrews_Resume.pdf"
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
    path = paths
    print("////////// PDF path /////")
    print("Loading PDF from path: ", path)
    print("////////// PDF path /////")
    loader = PyMuPDFLoader(path)
    docs = loader.load()
    print("////////// doc path /////")
    print(docs)
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
    sys_msg = SystemMessage(content="You are a resume writer and ATS expert. Rewrite the resume to match the job description and optimize for ATS. Return a well-formatted markdown resume.")
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

graph.add_edge(START,"load_pdf")

graph.add_edge("load_pdf", "get_job_description")
graph.add_edge("get_job_description", "llm_with_score")

def score_check(state: StoreMessage) -> str:
    return "create_resume" if state["score"] > 70 else "llm_review"

graph.add_conditional_edges("llm_with_score", score_check)

graph.add_edge("create_resume", END)
graph.add_edge("llm_review", END)

workflow = graph.compile()
