"""
AIQE Crew Orchestrator
CrewAI acts as the leader/manager - receives requests and routes to the right agent.
Uses hierarchical process so the manager (CrewAI) delegates tasks intelligently.
"""
import os
import re
from crewai import Crew, Task, Process
from crewai import LLM
from agents.agent_definitions import (
    get_business_analyst_agent,
    get_manual_tester_agent,
    get_automation_tester_agent,
    get_java_example_agent,
)

def build_llm() -> LLM:
    """Build LLM using OpenAI-compatible API (NVIDIA NIM or similar)."""
    api_key = os.getenv("API_KEY")
    model_name = os.getenv("MODEL_NAME", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning")

    # NVIDIA NIM API uses OpenAI-compatible endpoint
    return LLM(
        model=f"openai/{model_name}",
        api_key=api_key,
        base_url="https://integrate.api.nvidia.com/v1",
        temperature=0.2,
        max_tokens=4096,
    )


def detect_intent(user_request: str) -> dict:
    """
    Detect user intent and extract Jira ticket key if present.
    Returns: {intent: str, jira_key: str|None, raw_request: str}
    """
    request_lower = user_request.lower()

    # Extract Jira ticket key (e.g., SCRUM-100, PROJECT-42)
    jira_pattern = r'\b([A-Z][A-Z0-9]+-\d+)\b'
    jira_matches = re.findall(jira_pattern, user_request.upper())
    jira_key = jira_matches[0] if jira_matches else None

    # Detect intent based on keywords
    if any(k in request_lower for k in ["automation", "automat", "testng", "selenium", "code test", "auto test"]):
        intent = "automation_testcase"
    elif any(k in request_lower for k in ["manual test", "test case", "testcase", "tc", "viết test", "tạo test"]):
        intent = "manual_testcase"
    elif any(k in request_lower for k in ["business analysis", "phân tích", "analyze", "ba ", "requirements", "user story analysis"]):
        intent = "business_analysis"
    elif any(k in request_lower for k in ["java example", "project example", "template", "maven example", "java project"]):
        intent = "java_example"
    elif jira_key:
        # Has Jira key but unclear intent -> default to business analysis first
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
    """
    llm = build_llm()

    parsed = detect_intent(user_request)
    intent = parsed["intent"]
    jira_key = parsed["jira_key"]
    raw_request = parsed["raw_request"]

    print(f"\n[Crew Manager] Intent detected: {intent}")
    if jira_key:
        print(f"[Crew Manager] Jira ticket found: {jira_key}")

    # Build task description with Jira context
    jira_instruction = ""
    if jira_key:
        jira_instruction = (
            f"\n\nIMPORTANT: Jira ticket '{jira_key}' was provided. "
            f"You MUST use the JiraReader tool to read the full user story from Jira BEFORE doing anything else. "
            f"Do NOT assume or guess the content of the ticket."
        )

    # Route to correct agent based on intent
    if intent == "business_analysis":
        agent = get_business_analyst_agent(llm)
        task_desc = (
            f"User request: {raw_request}\n"
            f"{jira_instruction}\n"
            f"Perform a thorough business analysis of the requirements. "
            f"Identify: scope, acceptance criteria, edge cases, business rules, and risks."
        )
        expected_output = (
            "A structured business analysis report with: "
            "1) Summary of requirements, 2) Acceptance Criteria, "
            "3) Edge cases and risks, 4) Out of scope items."
        )

    elif intent == "manual_testcase":
        agent = get_manual_tester_agent(llm)
        task_desc = (
            f"User request: {raw_request}\n"
            f"{jira_instruction}\n"
            f"Write comprehensive manual test cases covering positive, negative, and edge cases."
        )
        expected_output = (
            "A complete set of manual test cases in table format with: "
            "TC ID, Title, Preconditions, Steps, Expected Result, Priority, Type."
        )

    elif intent == "automation_testcase":
        agent = get_automation_tester_agent(llm)
        task_desc = (
            f"User request: {raw_request}\n"
            f"{jira_instruction}\n"
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
            f"User request: {raw_request}\n"
            f"Create a complete Java TestNG Maven project example/template. "
            f"Include: pom.xml with dependencies, testng.xml, BaseTest class, "
            f"sample Page Object, and sample test class."
        )
        expected_output = (
            "Complete Java TestNG Maven project template with pom.xml, testng.xml, "
            "BaseTest, Page Object example, and Test class example."
        )

    else:
        # General request - use Business Analyst as default
        agent = get_business_analyst_agent(llm)
        task_desc = (
            f"User request: {raw_request}\n"
            f"{jira_instruction}\n"
            f"Handle this QA/Testing related request to the best of your ability."
        )
        expected_output = "A clear, detailed response to the user's QA/Testing request."

    # Create task
    task = Task(
        description=task_desc,
        expected_output=expected_output,
        agent=agent,
    )

    # Create crew with single agent (sequential process)
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
        tracing=True

    )

    result = crew.kickoff()
    return str(result)
