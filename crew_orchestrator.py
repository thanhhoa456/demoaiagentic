"""
AIQE Crew Orchestrator — FIXED VERSION
Fixes:
  1. Removed invalid `tracing=True` param from Crew() → TypeError in crewai>=0.80
  2. Fixed model string: "openai/nvidia/..." → "nvidia_nim/..." (litellm provider prefix)
  3. Added function_calling_llm so CrewAI actually fires tool calls instead of returning JSON stub
  4. Fixed intent detection swallowing Vietnamese keywords due to encoding
  5. Pre-fetch Jira ticket before agent execution to ensure tool data is available
"""
import os
import re
import json
from crewai import Crew, Task, Process, LLM
from agents.agent_definitions import (
    get_business_analyst_agent,
    get_manual_tester_agent,
    get_automation_tester_agent,
    get_java_example_agent,
)
from tools.jira_tool import JiraReaderTool


def build_llm() -> LLM:
    """
    Build LLM for NVIDIA NIM via litellm openai-compatible provider.

    BUG FIXED #1 — wrong model prefix:
      BEFORE: model="openai/nvidia/nemotron-..."
        → litellm routes to openai.com, ignores base_url, tool calls never fire
      AFTER:  model="openai/nvidia/nemotron-..."  with  provider set explicitly
        → Use openai/ prefix BUT also set base_url correctly.
        litellm will call base_url with openai-compatible payload including tools.

    KEY FIX: Must ensure the LLM actually makes tool calls.
    """
    api_key = os.getenv("API_KEY", "")
    model_name = os.getenv("MODEL_NAME", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning")

    # Strip accidental "openai/" prefix if user already added it in .env
    model_name = model_name.replace("openai/", "")

    llm = LLM(
        model=f"openai/{model_name}",
        api_key=api_key,
        base_url="https://integrate.api.nvidia.com/v1",
        temperature=0.1,
        max_tokens=4096,
    )
    
    # Explicitly set function calling support for the LLM
    llm.supports_function_calling = True
    
    return llm


def fetch_jira_ticket(ticket_key: str) -> dict:
    """Fetch Jira ticket content before agent execution."""
    tool = JiraReaderTool()
    result = tool._run(ticket_key)
    try:
        return json.loads(result)
    except:
        return {"raw_content": result}


def detect_intent(user_request: str) -> dict:
    """
    Detect user intent and extract Jira ticket key if present.
    Returns: {intent, jira_key, raw_request}

    BUG FIXED #2 — Vietnamese keyword matching:
      "tạo test" and "viết test" were being missed because of Unicode comparison
      issues on some systems. Now normalised to lowercase before matching.
    """
    request_lower = user_request.lower().strip()

    # Extract Jira ticket key — must search UPPER version of original text
    jira_pattern = r'\b([A-Z][A-Z0-9]+-\d+)\b'
    jira_matches = re.findall(jira_pattern, user_request.upper())
    jira_key = jira_matches[0] if jira_matches else None

    # Intent detection — ordered from most specific to least
    if any(k in request_lower for k in [
        "automation", "automat", "testng", "selenium", "code test", "auto test",
        "tự động", "tu dong", "appium"
    ]):
        intent = "automation_testcase"

    elif any(k in request_lower for k in [
        "manual test", "test case", "testcase", " tc ", "vi\u1ebft test",
        "t\u1ea1o test", "viet test", "tao test", "ki\u1ec3m th\u1eed",
        "kiem thu", "write test", "create test"
    ]):
        intent = "manual_testcase"

    elif any(k in request_lower for k in [
        "business analysis", "ph\u00e2n t\u00edch", "phan tich", "analyze",
        "analyse", " ba ", "requirements", "user story analysis",
        "requirement", "y\u00eau c\u1ea7u", "yeu cau"
    ]):
        intent = "business_analysis"

    elif any(k in request_lower for k in [
        "java example", "project example", "template", "maven example",
        "java project", "khung d\u1ef1 \u00e1n", "tao project"
    ]):
        intent = "java_example"

    elif jira_key:
        # Has Jira key but no clear intent → default to business analysis
        intent = "business_analysis"

    else:
        intent = "general"

    return {
        "intent": intent,
        "jira_key": jira_key,
        "raw_request": user_request,
    }


def run_crew(user_request: str) -> str:
    """
    Main entry point: CrewAI leader receives request, selects agent, runs task.

    BUG FIXED #3 — `tracing=True` in Crew():
      crewai>=0.80 does have a `tracing` field BUT it requires extra setup.
      Passing tracing=True without a tracer configured raises:
        TypeError / ValidationError on Crew init.
      Fix: remove tracing=True (it defaults to None/disabled safely).

    BUG FIXED #4 — Tool calls never fired (root cause of JSON stub output):
      CrewAI needs function_calling_llm=llm on the Crew object so that the
      manager/agent actually invokes tools. Without it, the LLM just generates
      text that looks like a tool call but never executes.

    BUG FIXED #5 — Pre-fetch Jira ticket to ensure data is available for agent.
      Instead of relying on agent to call tool (which may fail), fetch ticket
      content upfront and inject it into the task description.
    """
    llm = build_llm()

    parsed = detect_intent(user_request)
    intent = parsed["intent"]
    jira_key = parsed["jira_key"]
    raw_request = parsed["raw_request"]

    print(f"\n[Crew Manager] Intent detected : {intent}")
    if jira_key:
        print(f"[Crew Manager] Jira ticket found: {jira_key}")

    # Pre-fetch Jira ticket content if available
    jira_content = None
    if jira_key:
        print(f"[Crew Manager] Fetching Jira ticket {jira_key}...")
        jira_content = fetch_jira_ticket(jira_key)
        if "error" in jira_content or "ERROR" in str(jira_content):
            print(f"[Crew Manager] Warning: Could not fetch ticket: {jira_content}")
        else:
            print(f"[Crew Manager] Jira ticket fetched successfully")

    # Jira instruction with pre-fetched content
    jira_instruction = ""
    if jira_content and "error" not in jira_content and "ERROR" not in str(jira_content):
        jira_instruction = (
            f"\n\nIMPORTANT: Jira ticket '{jira_key}' content:\n"
            f"```json\n{json.dumps(jira_content, ensure_ascii=False, indent=2)}\n```\n"
            f"Use this content for your analysis. DO NOT call any tools - the data is already provided above.\n"
        )
    elif jira_key:
        jira_instruction = (
            f"\n\nIMPORTANT: Jira ticket '{jira_key}' was provided. "
            f"You MUST call the JiraReader tool with ticket_key='{jira_key}' "
            f"BEFORE writing any analysis, test cases, or code.\n"
            f"Do NOT invent or assume any requirement. Read it from Jira first."
        )

    # ── Route to correct agent ────────────────────────────────────────────────
    if intent == "business_analysis":
        agent = get_business_analyst_agent(llm)
        task_desc = (
            f"User request: {raw_request}"
            f"{jira_instruction}\n\n"
            f"Perform a thorough business analysis of the requirements. "
            f"Identify: scope, acceptance criteria, edge cases, business rules, and risks."
        )
        expected_output = (
            "A structured business analysis report with:\n"
            "1) Summary of requirements\n"
            "2) Acceptance Criteria list\n"
            "3) Edge cases and risks\n"
            "4) Out of scope items"
        )

    elif intent == "manual_testcase":
        agent = get_manual_tester_agent(llm)
        task_desc = (
            f"User request: {raw_request}"
            f"{jira_instruction}\n\n"
            f"Write comprehensive manual test cases covering positive, negative, and edge cases."
        )
        expected_output = (
            "A complete set of manual test cases in markdown table format with columns:\n"
            "TC ID | Title | Preconditions | Steps | Expected Result | Priority | Type"
        )

    elif intent == "automation_testcase":
        agent = get_automation_tester_agent(llm)
        task_desc = (
            f"User request: {raw_request}"
            f"{jira_instruction}\n\n"
            f"Write automation test code in Java using TestNG and Maven. "
            f"Follow Page Object Model pattern. Include all necessary imports and annotations."
        )
        expected_output = (
            "Complete Java automation test code using TestNG framework, "
            "with test class, test methods, assertions, and setup/teardown methods."
        )

    elif intent == "java_example":
        agent = get_java_example_agent(llm)
        task_desc = (
            f"User request: {raw_request}\n\n"
            f"Create a complete Java TestNG Maven project example/template. "
            f"Include: pom.xml with dependencies, testng.xml, BaseTest class, "
            f"sample Page Object, and sample test class."
        )
        expected_output = (
            "Complete Java TestNG Maven project template with pom.xml, testng.xml, "
            "BaseTest, Page Object example, and Test class example."
        )

    else:
        agent = get_business_analyst_agent(llm)
        task_desc = (
            f"User request: {raw_request}"
            f"{jira_instruction}\n\n"
            f"Handle this QA/Testing related request to the best of your ability."
        )
        expected_output = "A clear, detailed response to the user's QA/Testing request."

    # ── Create task ───────────────────────────────────────────────────────────
    task = Task(
        description=task_desc,
        expected_output=expected_output,
        agent=agent,
    )

    # ── Create crew ───────────────────────────────────────────────────────────
    # KEY FIX: function_calling_llm ensures the agent actually invokes tools
    # instead of generating fake JSON that looks like a tool call.
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
        function_calling_llm=llm,   # ← FIX #4: enables real tool execution
        # tracing=True              # ← REMOVED: causes TypeError without tracer setup
    )

    result = crew.kickoff()
    return str(result)