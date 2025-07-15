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
    # Using Tavily for its reliability in scraping content
    search_tool = TavilySearch(max_results=15)
except Exception as e:
    print(f"Error initializing TavilySearchResults: {e}. Ensure TAVILY_API_KEY is set.")
    exit()

# --- PYDANTIC MODELS ---
class AnalysisReport(BaseModel):
    topic: str
    overall_sentiment: str
    key_findings: List[str]
    potential_impact: str
    sentiment_score: int = Field(description="A sentiment score from -10 (very negative) to +10 (very positive).")

# --- 1. DEFINE THE STATE (SIMPLIFIED) ---
class BIState(TypedDict):
    topic: str
    search_results: str  # UPDATED: This is now a single string
    analysis_report: Optional[AnalysisReport]
    chart_path: Optional[str]
    final_report: Optional[str]

# --- 2. DEFINE THE NODES (AGENTS) ---

def news_researcher_node(state: BIState):
    print("\n--- AGENT: News Researcher ---")
    # The tool returns a single, clean string of concatenated results
    search_results_str = search_tool.invoke(f"latest news and top stories about {state['topic']}")
    print(f"  -> Research complete.")
    return {"search_results": search_results_str}

def analyst_agent_node(state: BIState):
    print("\n--- AGENT: Data Analyst ---")
    # UPDATED: No loop needed. Use the string directly.
    context_str = state['search_results']
    prompt = f"""You are a senior financial analyst. Analyze the following news content about '{state['topic']}' and generate a structured report.
    Your report must include a 'sentiment_score' from -10 (very negative) to +10 (very positive).

    News Content: --- {context_str} ---
    """
    structured_llm = llm.with_structured_output(AnalysisReport)
    final_analysis = structured_llm.invoke(prompt)
    final_analysis.topic = state['topic']
    return {"analysis_report": final_analysis}

def visualization_agent_node(state: BIState):
    print("\n--- AGENT: Visualization Specialist ---")
    report = state['analysis_report']
    chart_prompt = f"""
    You are a data visualization expert. Write Python code using matplotlib and seaborn to generate a single, visually appealing bar chart that visualizes the sentiment score.
    The score is {report.sentiment_score} (out of a range from -10 to 10).
    The chart should have a title: 'Sentiment Analysis for: {report.topic}'.
    Save the chart to a file named 'sentiment_chart.png'.
    Return ONLY the raw Python code."""
    
    raw_charting_code = llm.invoke(chart_prompt).content
    cleaned_charting_code = raw_charting_code.replace("```python", "").replace("```", "").strip()
    
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        exec(cleaned_charting_code, globals(), locals())
        print("  -> Successfully saved chart to sentiment_chart.png")
        return {"chart_path": "sentiment_chart.png"}
    except Exception as e:
        print(f"  -> Error executing charting code: {e}")
        return {"chart_path": None}

def report_writer_node(state: BIState):
    print("\n--- AGENT: Report Writer ---")
    analysis_report = state['analysis_report']
    chart_path = state.get('chart_path')
    findings_str = "\n".join([f"- {finding}" for finding in analysis_report.key_findings])
    
    report_text = f"""# Business Intelligence Report: {analysis_report.topic}
## 1. Overall Sentiment Analysis
**Overall Sentiment:** {analysis_report.overall_sentiment} (Score: {analysis_report.sentiment_score}/10)
This sentiment is based on the analysis of recent news and developments.
## 2. Key Findings
Here are the most important points identified from the research:
{findings_str}
## 3. Potential Impact
{analysis_report.potential_impact}
"""
    if chart_path:
        report_text += f"\n## 4. Sentiment Visualization\n![Sentiment Chart]({chart_path})"
    else:
        report_text += "\n\n*(A chart could not be generated for this report.)*"
    
    return {"final_report": report_text}

# --- 3. BUILD THE GRAPH ---
workflow = StateGraph(BIState)

workflow.add_node("researcher", news_researcher_node)
workflow.add_node("analyst", analyst_agent_node)
workflow.add_node("visualizer", visualization_agent_node)
workflow.add_node("writer", report_writer_node)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "analyst")
workflow.add_edge("analyst", "visualizer")
workflow.add_edge("visualizer", "writer")
workflow.add_edge("writer", END)

app = workflow.compile()

# --- 4. MAIN EXECUTION ---
if __name__ == "__main__":
    topic = input("Enter a topic for the BI report (e.g., 'Tesla's new Gigafactory announcement'): ")
    initial_input = {"topic": topic}
    
    print(f"\n--- STARTING AUTONOMOUS BI REPORT for topic: '{topic}' ---")
    final_state = app.invoke(initial_input)
    
    print("\n\n--- WORKFLOW COMPLETE ---")
    final_report_md = final_state.get("final_report")
    if final_report_md:
        filename = "final_bi_report.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_report_md)
        print(f"Success! Report saved to {filename}")
    else:
        print("Workflow finished, but no final report was generated.")
