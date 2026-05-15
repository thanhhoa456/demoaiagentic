"""
tools/jira_tool.py
Fetches Jira user stories using the Jira REST API v3.
"""
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

JIRA_URL = os.getenv("JIRA_URL")
JIRA_USER = os.getenv("JIRA_USER")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")


def fetch_user_story(issue_key: str) -> dict:
    """
    Fetch a Jira issue (user story) by its key, e.g. SCRUM-100.
    Returns a dict with summary, description, and status.
    Raises an exception if the request fails.
    """
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    params = {
        "jql": f"key={issue_key}",
        "fields": "summary,description,status,acceptanceCriteria"
    }
    auth = HTTPBasicAuth(JIRA_USER, JIRA_TOKEN)
    headers = {"Accept": "application/json"}

    response = requests.get(url, params=params, headers=headers, auth=auth)

    if response.status_code != 200:
        raise Exception(
            f"Jira API error {response.status_code}: {response.text}"
        )

    data = response.json()
    issues = data.get("issues", [])

    if not issues:
        raise Exception(f"No issue found for key: {issue_key}")

    issue = issues[0]
    fields = issue.get("fields", {})

    # Extract plain text from Atlassian Document Format (ADF) description
    description_text = _extract_adf_text(fields.get("description"))

    return {
        "key": issue_key,
        "summary": fields.get("summary", ""),
        "description": description_text,
        "status": fields.get("status", {}).get("name", "Unknown"),
    }


def _extract_adf_text(adf: dict) -> str:
    """
    Recursively extract plain text from Atlassian Document Format (ADF).
    """
    if not adf:
        return ""

    if isinstance(adf, str):
        return adf

    text_parts = []

    if adf.get("type") == "text":
        text_parts.append(adf.get("text", ""))

    for child in adf.get("content", []):
        text_parts.append(_extract_adf_text(child))

    return " ".join(filter(None, text_parts)).strip()


def format_user_story_for_agent(issue_key: str) -> str:
    """
    Fetch and format a Jira user story as a clean string for agent consumption.
    """
    story = fetch_user_story(issue_key)
    return (
        f"## Jira User Story: {story['key']}\n"
        f"**Summary:** {story['summary']}\n"
        f"**Status:** {story['status']}\n\n"
        f"**Description:**\n{story['description']}\n"
    )


if __name__ == "__main__":
    # Quick test
    import sys
    key = sys.argv[1] if len(sys.argv) > 1 else "SCRUM-100"
    print(format_user_story_for_agent(key))
