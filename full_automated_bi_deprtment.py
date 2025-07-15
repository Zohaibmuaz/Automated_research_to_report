import os
import re
import json
from typing import List, TypedDict, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END

# NEW: Import the Resend library
import resend

# --- SETUP ---
load_dotenv()
llm = ChatOpenAI(model="gpt-4o", temperature=0)
try:
    search_tool = TavilySearch(max_results=5)
except Exception as e:
    print(f"Error initializing TavilySearchResults: {e}. Ensure TAVILY_API_KEY is set.")
    exit()

# --- PYDANTIC MODELS ---
class AnalysisReport(BaseModel):
    topic: str
    overall_sentiment: str
    key_findings: List[str]
    potential_impact: str

# --- 1. DEFINE THE STATE ---
class BIState(TypedDict):
    topic: str
    search_results: str
    analysis_report: Optional[AnalysisReport]
    final_report_markdown: Optional[str]

# --- 2. DEFINE THE NODES (AGENTS) ---

def news_researcher_node(state: BIState):
    print(f"\n--- AGENT: News Researcher (Topic: {state['topic']}) ---")
    search_results_str = search_tool.invoke(f"latest news and top stories about {state['topic']}")
    print("  -> Research complete.")
    return {"search_results": search_results_str}

def analyst_agent_node(state: BIState):
    print("\n--- AGENT: Data Analyst ---")
    context_str = state['search_results']
    prompt = f"Analyze the following news content about '{state['topic']}' and generate a structured analysis report."
    structured_llm = llm.with_structured_output(AnalysisReport)
    final_analysis = structured_llm.invoke(prompt, {"input": context_str})
    final_analysis.topic = state['topic']
    return {"analysis_report": final_analysis}

def report_writer_node(state: BIState):
    print("\n--- AGENT: Report Writer ---")
    report = state['analysis_report']
    
    # Create an HTML formatted report for the email
    findings_html = "".join([f"<li>{finding}</li>" for finding in report.key_findings])
    
    report_html = f"""
    <h1>Business Intelligence Report: {report.topic}</h1>
    <h2>Overall Sentiment Analysis</h2>
    <p><b>Sentiment:</b> {report.overall_sentiment}</p>
    <h2>Key Findings</h2>
    <ul>{findings_html}</ul>
    <h2>Potential Impact</h2>
    <p>{report.potential_impact}</p>
    """
    return {"final_report_markdown": report_html}

def email_notification_node(state: BIState):
    print("\n--- AGENT: Email Notifier ---")
    report_html = state['final_report_markdown']
    topic = state['topic']
    
    # Get credentials from environment variables
    resend_api_key = os.getenv("RESEND_API_KEY")
    sender_email = os.getenv("EMAIL_SENDER_ADDRESS")
    recipient_email = os.getenv("EMAIL_RECIPIENT_ADDRESS")
    
    if not all([resend_api_key, sender_email, recipient_email]):
        print("  -> ERROR: Resend or email credentials not found in .env file. Skipping email.")
        return {}

    resend.api_key = resend_api_key
    
    params = {
        "from": sender_email,
        "to": recipient_email,
        "subject": f"Daily AI BI Report: {topic}",
        "html": report_html,
    }

    try:
        # CORRECTED: Use resend.Emails.send (capital 'E')
        email = resend.Emails.send(params)
        print(f"  -> Successfully sent email report to {recipient_email}. Message ID: {email['id']}")
    except Exception as e:
        print(f"  -> FAILED to send email: {e}")
        
    return {}

# --- 3. BUILD THE GRAPH ---
workflow = StateGraph(BIState)
workflow.add_node("researcher", news_researcher_node)
workflow.add_node("analyst", analyst_agent_node)
workflow.add_node("writer", report_writer_node)
workflow.add_node("notifier", email_notification_node)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "analyst")
workflow.add_edge("analyst", "writer")
workflow.add_edge("writer", "notifier")
workflow.add_edge("notifier", END)

app = workflow.compile()

# --- 4. MAIN EXECUTION (CONFIGURABLE & NON-INTERACTIVE) ---
if __name__ == "__main__":
    # Read the topics from an environment variable
    topics_str = os.getenv("TOPICS_TO_RESEARCH")
    
    if not topics_str:
        # Provide a default list if the environment variable is not set
        print("INFO: TOPICS_TO_RESEARCH environment variable not found. Using default topics.")
        topics_to_research = [
            "NVIDIA stock performance",
            "Latest advancements in autonomous driving",
            "Market trends in renewable energy"
        ]
    else:
        # Split the comma-separated string into a list of topics
        topics_to_research = [topic.strip() for topic in topics_str.split(',')]

    print("--- AUTONOMOUS BI DEPARTMENT: STARTING DAILY RUN ---")
    
    for topic in topics_to_research:
        print(f"\n=================================================")
        print(f"--- Processing topic: '{topic}' ---")
        
        initial_input = {"topic": topic}
        
        try:
            # We invoke the graph and the final report will be sent by the notifier node
            app.invoke(initial_input)
        except Exception as e:
            print(f"  -> An error occurred during the workflow for topic '{topic}': {e}")

    print("\n=================================================")
    print("--- All BI Department tasks complete for today. ---")
