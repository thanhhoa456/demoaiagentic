"""
Agent Definitions for AIQE CrewAI Project
Each agent loads its skill prompt from the prompts/ folder.
"""
import os
from pathlib import Path
from crewai import Agent
from tools.jira_tool import JiraReaderTool
from dotenv import load_dotenv

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

jira_tool = JiraReaderTool()

# Load environment variables from .env file
load_dotenv()


def _load_prompt(filename: str) -> str:
    """Load skill prompt from prompts directory."""
    prompt_path = PROMPTS_DIR / filename
    if prompt_path.exists():
        content = prompt_path.read_text(encoding="utf-8")
        # Extract SYSTEM_PROMPT if it's a Python-style .md
        if 'SYSTEM_PROMPT = """' in content:
            start = content.find('SYSTEM_PROMPT = """') + len('SYSTEM_PROMPT = """')
            end = content.rfind('"""')
            if end > start:
                return content[start:end].strip()
        return content.strip()
    return ""


def get_business_analyst_agent(llm) -> Agent:
    """Business Analyst Agent - reads user story and analyzes requirements."""
    skill_prompt = _load_prompt("business_analysis.md")

    backstory = (
        "Bạn là một Business Analyst dày dạn kinh nghiệm trong lĩnh vực phần mềm. "
        "Bạn có khả năng đọc hiểu user story từ Jira và phân tích yêu cầu một cách chính xác. "
        "Bạn KHÔNG bao giờ tự suy đoán nội dung user story - luôn dùng JiraReader tool để đọc trước. "
        f"\n\nSkill guidance:\n{skill_prompt}" if skill_prompt else
        "Bạn là một Business Analyst dày dạn kinh nghiệm trong lĩnh vực phần mềm."
    )

    return Agent(
        role="Business Analyst",
        goal=(
            "Đọc user story từ Jira (bắt buộc dùng JiraReader tool) và phân tích requirements, "
            "xác định acceptance criteria, scope, và các edge case cần chú ý."
        ),
        backstory=backstory,
        tools=[jira_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )


def get_manual_tester_agent(llm) -> Agent:
    """Manual Tester Agent - writes manual test cases based on requirements."""
    skill_prompt = _load_prompt("manual_testcase.md")

    backstory = (
        "Bạn là QA Engineer chuyên viết manual test case với hơn 5 năm kinh nghiệm. "
        "Bạn có thể đọc user story từ Jira (dùng JiraReader tool) và viết test case chi tiết, "
        "bao gồm positive, negative, và edge case scenarios. "
        f"\n\nSkill guidance:\n{skill_prompt}" if skill_prompt else
        "Bạn là QA Engineer chuyên viết manual test case."
    )

    return Agent(
        role="Manual QA Tester",
        goal=(
            "Tạo manual test cases đầy đủ dựa trên user story. "
            "Nếu được cung cấp Jira ticket key, PHẢI dùng JiraReader tool để đọc nội dung trước. "
            "Không được tự suy đoán requirements."
        ),
        backstory=backstory,
        tools=[jira_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )


def get_automation_tester_agent(llm) -> Agent:
    """Automation Tester Agent - writes TestNG automation test cases."""
    skill_prompt = _load_prompt("automation_testcase.md")

    backstory = (
        "Bạn là Automation Engineer chuyên Java, TestNG, Maven với 7+ năm kinh nghiệm. "
        "Bạn viết automation test code chất lượng cao theo chuẩn POM (Page Object Model). "
        "Nếu có Jira ticket key, dùng JiraReader tool để đọc requirements trước. "
        f"\n\nSkill guidance:\n{skill_prompt}" if skill_prompt else
        "Bạn là Automation Engineer chuyên Java TestNG Maven."
    )

    return Agent(
        role="Automation QA Engineer",
        goal=(
            "Viết automation test code bằng Java + TestNG + Maven. "
            "Nếu được cung cấp Jira ticket key, PHẢI dùng JiraReader tool để đọc user story. "
            "Code phải compilable, follow POM pattern, và cover các scenario quan trọng."
        ),
        backstory=backstory,
        tools=[jira_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )


def get_java_example_agent(llm) -> Agent:
    """Java TestNG Maven Example Agent - creates project templates."""
    skill_prompt = _load_prompt("java_testng_maven_example.md")

    backstory = (
        "Bạn là Senior Java Automation Engineer, chuyên tạo project template và example code. "
        "Bạn tạo ra các project structure chuẩn, clean code, dễ maintain. "
        f"\n\nSkill guidance:\n{skill_prompt}" if skill_prompt else
        "Bạn là Senior Java Automation Engineer."
    )

    return Agent(
        role="Java TestNG Maven Architect",
        goal=(
            "Tạo Java TestNG Maven project example/template hoàn chỉnh. "
            "Bao gồm pom.xml, testng.xml, base classes, page objects, và sample tests."
        ),
        backstory=backstory,
        tools=[jira_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )
