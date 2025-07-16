# 🤖 Autonomous AI Business Intelligence Department

This repository contains the code for a fully autonomous, multi-agent system designed to function as a Business Intelligence (BI) department. This system automates the entire workflow of market research, from initial data gathering and analysis to the final synthesis of a professional, human-readable report.

This project is the capstone of the "Autonomous AI Systems Architect" course, demonstrating advanced concepts in agentic design, system architecture, and production-ready deployment.

---

## ✨ Key Features & Capabilities

This is not just a script; it's a prototype of a fully automated business function designed for real-world application.

* **Autonomous Operation:** The system runs end-to-end without any human intervention. It takes a list of research topics and handles the entire process from data gathering to final report generation.

* **Multi-Agent Collaboration:** It uses a sophisticated crew of specialized AI agents (Researcher, Analyst, and Writer/Notifier) that collaborate to solve the problem, with each agent handling a specific part of the workflow.

* **Intelligent & Adaptive:** The system is built on **LangGraph**, allowing for complex, stateful workflows. It can handle real-world failures (like un-scrapable websites), adapt its strategy, and make decisions based on the quality of data at each stage.

* **Structured & Reliable Output:** It leverages **Pydantic** to enforce strict data schemas, ensuring the output from the analysis agent is always clean, predictable, and reliable for use in the final report.

---

## 🏛️ Architectural Overview

The core problem this system solves is the time-consuming, manual process of market research. The architecture is designed as a **stateful graph** where each node represents a specialized agent, ensuring a clear separation of concerns and a robust data pipeline.

**Workflow:**
`Start` -> `[Agent 1: News Researcher]` -> `[Agent 2: Data Analyst]` -> `[Agent 3: Report Writer & Notifier]` -> `End`

1.  **News Researcher:** Scans the web for the latest news on a given topic using the Tavily API, which provides pre-cleaned article content.
2.  **Data Analyst:** Reads the research and synthesizes it into a structured `AnalysisReport` containing key findings, overall sentiment, and potential business impact.
3.  **Report Writer & Notifier:** Takes the structured analysis and delivers the final, formatted report to a specified online source (e.g., via Resend or Discord) for easy access.

---

## 🛠️ Technology Stack

This project utilizes a modern, production-grade AI stack:

* **Orchestration Framework:** LangGraph
* **LLM:** OpenAI GPT-4o
* **Core AI Library:** LangChain
* **Web Search Tool:** Tavily AI
* **Data Validation:** Pydantic
* **Containerization:** Docker
* **Deployment (Scheduled Job):** Render / Cloud Services

---

## 🚀 Setup & Usage

### 1. Clone the Repository

```bash
git clone [Your-GitHub-Repo-URL]
cd [repository-folder]
```

## 2. Create and Configure the Environment

Install the required libraries:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the root directory and add your secret API keys:

```env
OPENAI_API_KEY="sk-..."
TAVILY_API_KEY="tvly-..."
# Optional: Notification service key
RESEND_API_KEY="resend-..."
```

## 3. Run the System

This script is designed to be non-interactive. It automatically processes the list of topics defined in the main block or in your `TOPICS_TO_RESEARCH` environment variable.

```bash
python your_script_name.py
```

The system will print its progress to the console and deliver the final reports to your configured notification channel.

---

## 🔮 Future Enhancements

This project serves as a powerful foundation. Possible future improvements include:

### Persistent Inter-run Memory
Implement a persistent state (e.g., using SQLite checkpointer) so the agent can perform longitudinal, trend-based analysis by comparing today’s news to previous data.

### Scalable Deployment
Deploy the Docker container to a cloud provider like Render or AWS and configure it as a Cron Job to run automatically on a daily schedule.

### Advanced Notification System
Expand the Notifier agent to save reports to a cloud storage bucket (e.g., AWS S3) or a database, in addition to sending notifications via email, Slack, or Discord.

---

## 📄 License

This project is licensed for educational and demonstration purposes. Please refer to the LICENSE file for more details.
