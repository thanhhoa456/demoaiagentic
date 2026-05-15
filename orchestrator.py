"""
orchestrator.py
====================================================================
Agentic QA System - AutoGen Orchestrator (Leader)
====================================================================
Flow:
  User Request
       │
       ▼
  [Orchestrator] ── reads intent ──► decides which agents to call
       │
       ├─► [BusinessAnalysisAgent]   ← optional, for deep analysis
       │
       ├─► [ManualTestcaseAgent]     ← always called first in QA flow
       │         output ──────────────────────────────────────────►┐
       │                                                            │
       └─► [AutomationTestcaseAgent] ← receives manual TC output ◄─┘

Usage:
    python orchestrator.py --jira SCRUM-100
    python orchestrator.py --jira SCRUM-100 --task manual
    python orchestrator.py --jira SCRUM-100 --task automation
    python orchestrator.py --jira SCRUM-100 --task full
"""

import os
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
import argparse
import sys
from dotenv import load_dotenv

load_dotenv()

# ─── LLM Config ────────────────────────────────────────────────────────────────
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning")
BASE_URL = os.getenv("BASE_URL", "https://integrate.api.nvidia.com/v1")

LLM_CONFIG = {
    "config_list": [
        {
            "model": MODEL_NAME,
            "api_key": API_KEY,
            "base_url": BASE_URL,
            "api_type": "openai",          # NVIDIA uses OpenAI-compatible API
        }
    ],
    "temperature": 0.2,
    "timeout": 120,
}

# ─── Imports (after env is loaded) ────────────────────────────────────────────
from autogen import UserProxyAgent, GroupChat, GroupChatManager
from agents.business_analysis_agent import create_business_analysis_agent
from agents.manual_testcase_agent import create_manual_testcase_agent
from agents.automation_testcase_agent import create_automation_testcase_agent
from tools.jira_tool import format_user_story_for_agent
from tools.file_tool import save_output, timestamped_filename


# ─── Helper ───────────────────────────────────────────────────────────────────

def extract_last_reply(chat_result, agent_name: str) -> str:
    """
    Extract the last message from a specific agent in a chat history.
    Falls back to the very last assistant message if agent_name not found.
    """
    messages = chat_result.chat_history if hasattr(chat_result, "chat_history") else []
    # Search in reverse for the target agent
    for msg in reversed(messages):
        if msg.get("role") == "assistant" or msg.get("name") == agent_name:
            return msg.get("content", "")
    # Fallback
    for msg in reversed(messages):
        if msg.get("content"):
            return msg.get("content", "")
    return ""


def get_user_proxy() -> UserProxyAgent:
    """
    Create a silent UserProxyAgent (the orchestrator's human side).
    It never asks for human input and never executes code.
    """
    return UserProxyAgent(
        name="Orchestrator",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        code_execution_config=False,
        is_termination_msg=lambda msg: msg.get("content", "").strip().endswith("DONE"),
    )


# ─── Pipeline Steps ────────────────────────────────────────────────────────────

def step_fetch_jira(issue_key: str) -> str:
    print(f"\n{'='*60}")
    print(f"[Orchestrator] Fetching Jira story: {issue_key}")
    print(f"{'='*60}")
    user_story = format_user_story_for_agent(issue_key)
    print(user_story)
    return user_story


def step_business_analysis(user_story: str, issue_key: str) -> str:
    print(f"\n[Orchestrator] → Calling BusinessAnalysisAgent")
    agent = create_business_analysis_agent(LLM_CONFIG)
    proxy = get_user_proxy()

    prompt = (
        f"Please analyse the following Jira user story and provide a comprehensive "
        f"business analysis including: scope, acceptance criteria, test scope, risks, "
        f"and any dependencies.\n\n{user_story}"
    )

    result = proxy.initiate_chat(
        agent,
        message=prompt,
        max_turns=2,
    )

    analysis = extract_last_reply(result, "BusinessAnalysisAgent")
    fname = timestamped_filename(f"business_analysis_{issue_key}")
    save_output(analysis, fname, subfolder="business_analysis")
    print(f"\n[Orchestrator] ✓ Business analysis saved.")
    return analysis


def step_manual_testcases(user_story: str, issue_key: str, analysis: str = "") -> str:
    print(f"\n[Orchestrator] → Calling ManualTestcaseAgent")
    agent = create_manual_testcase_agent(LLM_CONFIG)
    proxy = get_user_proxy()

    context = f"{user_story}"
    if analysis:
        context += f"\n\n## Business Analysis\n{analysis}"

    prompt = (
        f"Based on the following user story (and analysis if provided), write "
        f"comprehensive manual test cases covering positive, negative, and edge cases.\n\n"
        f"{context}"
    )

    result = proxy.initiate_chat(
        agent,
        message=prompt,
        max_turns=2,
    )

    manual_tcs = extract_last_reply(result, "ManualTestcaseAgent")
    fname = timestamped_filename(f"manual_testcase_{issue_key}")
    save_output(manual_tcs, fname, subfolder="manual_testcases")
    print(f"\n[Orchestrator] ✓ Manual test cases saved.")
    return manual_tcs


def step_automation_testcases(manual_tcs: str, issue_key: str) -> str:
    print(f"\n[Orchestrator] → Calling AutomationTestcaseAgent")
    agent = create_automation_testcase_agent(LLM_CONFIG)
    proxy = get_user_proxy()

    prompt = (
        f"Convert the following manual test cases into Selenium + TestNG + Maven "
        f"Java automation test code. Follow Page Object Model pattern. "
        f"Generate complete, runnable Java test class(es).\n\n"
        f"## Manual Test Cases\n{manual_tcs}"
    )

    result = proxy.initiate_chat(
        agent,
        message=prompt,
        max_turns=2,
    )

    auto_tcs = extract_last_reply(result, "AutomationTestcaseAgent")
    fname = timestamped_filename(f"automation_testcase_{issue_key}", extension="java")
    save_output(auto_tcs, fname, subfolder="automation_testcases")
    print(f"\n[Orchestrator] ✓ Automation test cases saved.")
    return auto_tcs


# ─── Main Orchestrator ─────────────────────────────────────────────────────────

def run_pipeline(issue_key: str, task: str = "full"):
    """
    Main entry point. Decide which agents to invoke based on task type.

    task options:
      - "fetch"       : Only fetch the Jira story (no agents)
      - "analysis"    : Fetch + business analysis
      - "manual"      : Fetch + manual test cases
      - "automation"  : Fetch + manual + automation test cases
      - "full"        : Fetch + analysis + manual + automation (default)
    """
    print(f"\n{'='*60}")
    print(f"  Agentic QA System | Issue: {issue_key} | Task: {task}")
    print(f"{'='*60}\n")

    # Step 1: Always fetch Jira story
    user_story = step_fetch_jira(issue_key)

    analysis = ""
    manual_tcs = ""

    if task in ("analysis", "full"):
        analysis = step_business_analysis(user_story, issue_key)

    if task in ("manual", "automation", "full"):
        manual_tcs = step_manual_testcases(user_story, issue_key, analysis)

    if task in ("automation", "full"):
        step_automation_testcases(manual_tcs, issue_key)

    print(f"\n{'='*60}")
    print(f"  ✅ Pipeline completed for {issue_key}")
    print(f"  📁 Outputs saved in: {os.path.abspath('./output')}")
    print(f"{'='*60}\n")


# ─── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Agentic QA System - AutoGen Orchestrator"
    )
    parser.add_argument(
        "--jira",
        required=True,
        help="Jira issue key, e.g. SCRUM-100"
    )
    parser.add_argument(
        "--task",
        choices=["fetch", "analysis", "manual", "automation", "full"],
        default="full",
        help=(
            "Which pipeline steps to run:\n"
            "  fetch       - Only fetch Jira story\n"
            "  analysis    - Fetch + business analysis\n"
            "  manual      - Fetch + manual test cases\n"
            "  automation  - Fetch + manual + automation code\n"
            "  full        - All steps (default)"
        )
    )

    args = parser.parse_args()
    run_pipeline(args.jira, args.task)
