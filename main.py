"""
AIQE CrewAI - Main CLI Entry Point
Run: python main.py
"""
import os
import sys
import io
from pathlib import Path
from datetime import datetime

# Force UTF-8 encoding for stdout/stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load .env before anything else
from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich import print as rprint

from crew_orchestrator import run_crew

# Create console with UTF-8 support
console = Console(force_terminal=True, legacy_windows=False, width=100)


BANNER = """
AIQE - Agentic AI QE Framework (CrewAI)
Powered by NVIDIA Nemotron + CrewAI Agents
--------------------------------------------------
Agents available:
  * Business Analyst - Analyze user stories from Jira
  * Manual Tester   - Write manual test cases
  * Automation Tester - Write TestNG automation code
  * Java Maven Expert - Create project templates

Tip: Provide a Jira ticket key (e.g., SCRUM-100) to auto-read the user story from Jira
"""

EXAMPLES = """
Example requests:
  * "Phân tích user story SCRUM-100"
  * "Viết manual test case cho SCRUM-100"
  * "Tạo automation test code cho SCRUM-100 dùng TestNG"
  * "Tạo Java TestNG Maven project example"
  * "Analyze requirements in SCRUM-100 and write manual test cases"
"""


def save_output(request: str, result: str):
    """Save output to file."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"result_{timestamp}.md"
    content = f"# AIQE Output - {timestamp}\n\n## Request\n{request}\n\n## Result\n{result}\n"
    filename.write_text(content, encoding="utf-8")
    return filename


def validate_env():
    """Validate required environment variables."""
    required = ["API_KEY", "JIRA_URL", "JIRA_USER", "JIRA_TOKEN"]
    missing = [k for k in required if not os.getenv(k) or "your" in (os.getenv(k) or "").lower() or os.getenv(k) == "my_key_here"]
    if missing:
        console.print(f"[yellow]Warning: These .env values may not be set: {', '.join(missing)}[/yellow]")
        console.print("[yellow]   Edit .env file with your real credentials.[/yellow]\n")


def main():
    console.print(BANNER, style="bold cyan")
    validate_env()
    console.print(EXAMPLES, style="dim")

    console.print("[bold green]AIQE System Ready.[/bold green] Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            user_input = Prompt.ask("[bold blue]Your request[/bold blue]").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                console.print("[yellow]Goodbye![/yellow]")
                sys.exit(0)

            if user_input.lower() == "help":
                console.print(EXAMPLES)
                continue

            console.print("\n[bold cyan]Processing request...[/bold cyan]\n")

            result = run_crew(user_input)

            console.print("\n" + "="*60)
            console.print("[bold green]Result:[/bold green]")
            console.print("="*60)

            # Try to render as Markdown
            try:
                console.print(Markdown(result))
            except Exception:
                console.print(result)

            # Save output
            output_file = save_output(user_input, result)
            console.print(f"\n[dim]Output saved: {output_file}[/dim]\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error: {str(e)}[/red]")
            console.print("[dim]Check your .env credentials and try again.[/dim]\n")


if __name__ == "__main__":
    main()
