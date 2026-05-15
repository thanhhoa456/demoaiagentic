"""
agents/business_analysis_agent.py
Agent responsible for analysing Jira user stories.
"""
import os
from autogen import AssistantAgent
from dotenv import load_dotenv

load_dotenv()

PROMPT_FILE = os.path.join(os.path.dirname(__file__), "..", "prompts", "business_analysis.md")


def _load_prompt() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def create_business_analysis_agent(llm_config: dict) -> AssistantAgent:
    """
    Create and return the Business Analysis AI agent.
    This agent receives a raw Jira user story and produces a structured analysis.
    """
    system_message = _load_prompt()

    return AssistantAgent(
        name="BusinessAnalysisAgent",
        system_message=system_message,
        llm_config=llm_config,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3,
        code_execution_config=False,
    )
