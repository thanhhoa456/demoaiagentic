"""
Jira Tool - Reads user stories from Jira via REST API
"""
import os
import requests
from requests.auth import HTTPBasicAuth
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class JiraInput(BaseModel):
    ticket_key: str = Field(description="Jira ticket key, e.g. SCRUM-100")


class JiraReaderTool(BaseTool):
    name: str = "JiraReader"
    description: str = (
        "Reads a Jira ticket (user story) by its key (e.g. SCRUM-100). "
        "Returns the summary, description, and status of the ticket. "
        "ALWAYS use this tool when the user provides a Jira ticket key. "
        "Do NOT assume or fabricate ticket content."
    )
    args_schema: Type[BaseModel] = JiraInput

    def _run(self, ticket_key: str) -> str:
        jira_url = os.getenv("JIRA_URL")
        jira_user = os.getenv("JIRA_USER")
        jira_token = os.getenv("JIRA_TOKEN")

        if not all([jira_url, jira_user, jira_token]):
            return "ERROR: Jira credentials not configured in .env file."

        url = f"{jira_url}/rest/api/3/search/jql"
        params = {
            "jql": f"key={ticket_key}",
            "fields": "summary,description,status,acceptance criteria"
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers={"Accept": "application/json"},
                auth=HTTPBasicAuth(jira_user, jira_token),
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            issues = data.get("issues", [])
            if not issues:
                return f"No ticket found with key: {ticket_key}"

            issue = issues[0]
            fields = issue.get("fields", {})
            summary = fields.get("summary", "N/A")
            status = fields.get("status", {}).get("name", "N/A")

            # Parse description (Atlassian Document Format)
            description_raw = fields.get("description")
            description_text = _parse_adf(description_raw)

            return (
                f"=== Jira Ticket: {ticket_key} ===\n"
                f"Summary: {summary}\n"
                f"Status: {status}\n"
                f"Description:\n{description_text}\n"
            )
        except requests.exceptions.HTTPError as e:
            return f"HTTP Error reading Jira ticket {ticket_key}: {str(e)}"
        except Exception as e:
            return f"Error reading Jira ticket {ticket_key}: {str(e)}"


def _parse_adf(adf_content) -> str:
    """Parse Atlassian Document Format to plain text."""
    if not adf_content:
        return "No description provided."
    if isinstance(adf_content, str):
        return adf_content

    result = []

    def extract_text(node):
        if isinstance(node, dict):
            node_type = node.get("type", "")
            if node_type == "text":
                result.append(node.get("text", ""))
            elif node_type == "hardBreak":
                result.append("\n")
            elif node_type in ("paragraph", "heading", "bulletList", "orderedList"):
                for child in node.get("content", []):
                    extract_text(child)
                result.append("\n")
            elif node_type == "listItem":
                result.append("  - ")
                for child in node.get("content", []):
                    extract_text(child)
            else:
                for child in node.get("content", []):
                    extract_text(child)
        elif isinstance(node, list):
            for item in node:
                extract_text(item)

    extract_text(adf_content)
    return "".join(result).strip() or "No description provided."
