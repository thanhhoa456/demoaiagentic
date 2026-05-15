"""
agents/manual_testcase_agent.py
Agent responsible for writing manual test cases from a user story.
"""
import os
from autogen import AssistantAgent
from dotenv import load_dotenv

load_dotenv()

PROMPT_FILE = os.path.join(os.path.dirname(__file__), "..", "prompts", "manual_testcase.md")


def _load_prompt() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def create_manual_testcase_agent(llm_config: dict) -> AssistantAgent:
    """
    Create and return the Manual Test Case Writer AI agent.
    Input  : Jira user story (passed in the message by the orchestrator).
    Output : Structured manual test cases in Markdown format.
    """
    system_message = _load_prompt()

    return AssistantAgent(
        name="ManualTestcaseAgent",
        system_message=system_message,
        llm_config=llm_config,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3,
        code_execution_config=False,
    )
