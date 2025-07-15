import os
import re
import requests
import json
from bs4 import BeautifulSoup
from typing import List, TypedDict, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END

# --- SETUP ---
load_dotenv()
llm = ChatOpenAI(model="gpt-4o", temperature=0)
try:
    search_tool = TavilySearch(max_results=5)
except Exception as e:
    print(f"Error initializing TavilySearchResults: {e}")
    exit()

# --- PYDANTIC MODELS ---
class AnalysisReport(BaseModel):
    topic: str; overall_sentiment: str; key_findings: List[str]; potential_impact: str

# --- STATE DEFINITION ---
class BIState(TypedDict):
    topic: str
    search_results: str
    analysis_report: Optional[AnalysisReport]
    
# --- AGENT NODES ---
def news_researcher_node(state: BIState):
    print(f"\n--- AGENT: News Researcher (Topic: {state['topic']}) ---")
    search_results_str = search_tool.invoke(f"latest news and top stories about {state['topic']}")
    print(f"  -> Research complete.")
    return {"search_results": search_results_str}

def analyst_agent_node(state: BIState):
    print(f"\n--- AGENT: Data Analyst ---")
    context_str = state['search_results']
    prompt = f"""You are a senior financial analyst. Analyze the following news content about '{state['topic']}' and generate a structured analysis report with sentiment, key findings, and potential impact.
    Full Research Content: --- {context_str} ---"""
    structured_llm = llm.with_structured_output(AnalysisReport)
    final_analysis = structured_llm.invoke(prompt)
    final_analysis.topic = state['topic']
    return {"analysis_report": final_analysis}

# We will combine the writer and notifier for this version
def report_and_save_node(state: BIState):
    print("\n--- AGENT: Report Writer & Notifier ---")
    report = state['analysis_report']
    findings_str = "\n".join([f"- {finding}" for finding in report.key_findings])
    
    report_text = f"""# Business Intelligence Report: {report.topic}
## 1. Overall Sentiment Analysis
**Overall Sentiment:** {report.overall_sentiment}
## 2. Key Findings
{findings_str}
## 3. Potential Impact
{report.potential_impact}
"""
    # Save the report to a file
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_topic = re.sub(r'[\\/*?:"<>|]', "", report.topic).replace(" ", "_")
    filename = f"report_{safe_topic}_{date_str}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"  -> Success! Report saved to {filename}")
    return {} # End the graph

# --- GRAPH DEFINITION ---
workflow = StateGraph(BIState)
workflow.add_node("researcher", news_researcher_node)
workflow.add_node("analyst", analyst_agent_node)
workflow.add_node("writer", report_and_save_node)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "analyst")
workflow.add_edge("analyst", "writer")
workflow.add_edge("writer", END)

app = workflow.compile()

# --- MAIN EXECUTION (NON-INTERACTIVE) ---
if __name__ == "__main__":
    # This list defines the daily automated tasks.
    # In a real system, this could come from a database or an API call.
    topics_to_research = [
        "NVIDIA stock performance",
        "OpenAI's latest product releases",
        "Market trends in renewable energy"
    ]
    
    print("--- AUTONOMOUS BI DEPARTMENT: STARTING DAILY RUN ---")
    
    for topic in topics_to_research:
        print(f"\n=================================================")
        print(f"--- Processing topic: '{topic}' ---")
        
        initial_input = {"topic": topic}
        
        # Run the graph for the current topic
        app.invoke(initial_input)

    print("\n=================================================")
    print("--- All BI Department tasks complete for today. ---")
