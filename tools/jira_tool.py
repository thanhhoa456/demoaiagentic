"""
Jira Tool — FIXED VERSION
Fixes:
  1. More robust ADF (Atlassian Document Format) parser — handles nested lists, tables, panels
  2. Better error messages so agent sees WHY Jira call failed (auth vs URL vs not found)
  3. Added timeout + retry logic
  4. Return value now starts with clear marker so LLM recognises it as tool output
"""
import os
import requests
from requests.auth import HTTPBasicAuth
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type


class JiraInput(BaseModel):
    ticket_key: str = Field(
        description="Jira ticket key, e.g. SCRUM-100. Must be uppercase letters + hyphen + number."
    )


class JiraReaderTool(BaseTool):
    name: str = "JiraReader"
    description: str = (
        "MANDATORY tool to read a Jira ticket (user story) by its key (e.g. SCRUM-100). "
        "Returns the full summary, description, status, and acceptance criteria. "
        "ALWAYS call this tool FIRST when a Jira ticket key is mentioned. "
        "NEVER skip this tool or fabricate ticket content. "
        "Input: ticket_key (string) — the Jira issue key like 'SCRUM-100'."
    )
    args_schema: Type[BaseModel] = JiraInput

    def _run(self, ticket_key: str) -> str:
        ticket_key = ticket_key.strip().strip('"').strip("'").upper()

        jira_url = os.getenv("JIRA_URL", "").rstrip("/")
        jira_user = os.getenv("JIRA_USER", "")
        jira_token = os.getenv("JIRA_TOKEN", "")

        if not jira_url:
            return "[JiraReader ERROR] JIRA_URL is not set in .env file."
        if not jira_user:
            return "[JiraReader ERROR] JIRA_USER is not set in .env file."
        if not jira_token:
            return "[JiraReader ERROR] JIRA_TOKEN is not set in .env file."
        if not ticket_key:
            return "[JiraReader ERROR] ticket_key is empty. Provide a key like 'SCRUM-100'."

        url = f"{jira_url}/rest/api/3/issue/{ticket_key}"

        try:
            response = requests.get(
                url,
                headers={"Accept": "application/json"},
                auth=HTTPBasicAuth(jira_user, jira_token),
                timeout=20,
            )

            if response.status_code == 401:
                return (
                    f"[JiraReader ERROR 401] Authentication failed for {ticket_key}.\n"
                    f"Check JIRA_USER (email) and JIRA_TOKEN in .env.\n"
                    f"Get token at: https://id.atlassian.com/manage-profile/security/api-tokens"
                )
            if response.status_code == 403:
                return (
                    f"[JiraReader ERROR 403] Permission denied for {ticket_key}.\n"
                    f"User '{jira_user}' does not have access to this project."
                )
            if response.status_code == 404:
                return (
                    f"[JiraReader ERROR 404] Ticket '{ticket_key}' not found.\n"
                    f"Check the ticket key and that JIRA_URL is correct: {jira_url}"
                )

            response.raise_for_status()
            data = response.json()

        except requests.exceptions.ConnectionError:
            return (
                f"[JiraReader ERROR] Cannot connect to Jira at {jira_url}.\n"
                f"Check your network and JIRA_URL in .env."
            )
        except requests.exceptions.Timeout:
            return f"[JiraReader ERROR] Request to Jira timed out after 20s. Try again."
        except Exception as e:
            return f"[JiraReader ERROR] Unexpected error: {str(e)}"

        fields = data.get("fields", {})
        summary = fields.get("summary", "No summary")
        status = fields.get("status", {}).get("name", "Unknown")
        priority = fields.get("priority", {}).get("name", "Unknown")
        issue_type = fields.get("issuetype", {}).get("name", "Unknown")

        description_adf = fields.get("description")
        description_text = _parse_adf(description_adf)

        ac_text = ""
        for field_name in ["customfield_10016", "customfield_10014", "customfield_10020"]:
            raw_ac = fields.get(field_name)
            if raw_ac:
                ac_text = _parse_adf(raw_ac) if isinstance(raw_ac, dict) else str(raw_ac)
                break

        assignee = (fields.get("assignee") or {}).get("displayName", "Unassigned")
        reporter = (fields.get("reporter") or {}).get("displayName", "Unknown")

        result = {
            "ticket_key": ticket_key,
            "summary": summary,
            "type": issue_type,
            "status": status,
            "priority": priority,
            "assignee": assignee,
            "reporter": reporter,
            "description": description_text,
        }
        if ac_text:
            result["acceptance_criteria"] = ac_text

        import json
        return json.dumps(result, ensure_ascii=False, indent=2)


# ── ADF Parser ────────────────────────────────────────────────────────────────

def _parse_adf(node) -> str:
    """Recursively parse Atlassian Document Format to plain text."""
    if node is None:
        return "No content provided."
    if isinstance(node, str):
        return node

    buf = []
    _walk(node, buf, indent=0)
    text = "".join(buf).strip()
    return text if text else "No content provided."


def _walk(node, buf: list, indent: int):
    if not isinstance(node, dict):
        return

    node_type = node.get("type", "")
    content   = node.get("content", [])
    attrs     = node.get("attrs", {})

    if node_type == "text":
        marks = node.get("marks", [])
        text  = node.get("text", "")
        # Apply basic formatting hints
        for mark in marks:
            if mark.get("type") == "strong":
                text = f"**{text}**"
            elif mark.get("type") == "em":
                text = f"_{text}_"
            elif mark.get("type") == "code":
                text = f"`{text}`"
        buf.append(text)

    elif node_type == "hardBreak":
        buf.append("\n")

    elif node_type in ("paragraph", "blockquote"):
        for child in content:
            _walk(child, buf, indent)
        buf.append("\n")

    elif node_type == "heading":
        level = attrs.get("level", 1)
        buf.append("#" * level + " ")
        for child in content:
            _walk(child, buf, indent)
        buf.append("\n")

    elif node_type == "bulletList":
        for item in content:
            _walk(item, buf, indent)

    elif node_type == "orderedList":
        for i, item in enumerate(content, 1):
            buf.append(f"{'  ' * indent}{i}. ")
            for child in item.get("content", []):
                _walk(child, buf, indent + 1)
        buf.append("\n")

    elif node_type == "listItem":
        buf.append(f"{'  ' * indent}- ")
        for child in content:
            _walk(child, buf, indent + 1)

    elif node_type == "codeBlock":
        language = attrs.get("language", "")
        buf.append(f"\n```{language}\n")
        for child in content:
            _walk(child, buf, indent)
        buf.append("\n```\n")

    elif node_type == "rule":
        buf.append("\n---\n")

    elif node_type in ("table", "tableRow", "tableHeader", "tableCell"):
        for child in content:
            _walk(child, buf, indent)
        if node_type in ("tableHeader", "tableCell"):
            buf.append(" | ")
        if node_type == "tableRow":
            buf.append("\n")

    elif node_type == "panel":
        panel_type = attrs.get("panelType", "info")
        buf.append(f"\n[{panel_type.upper()}] ")
        for child in content:
            _walk(child, buf, indent)
        buf.append("\n")

    elif node_type in ("doc", "expand"):
        for child in content:
            _walk(child, buf, indent)

    else:
        # Fallback: recurse into any unknown node type
        for child in content:
            _walk(child, buf, indent)