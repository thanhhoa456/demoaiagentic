"""
tools/file_tool.py
Utilities for agents to save their output artifacts to disk.
"""
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")


def save_output(content: str, filename: str, subfolder: str = "") -> str:
    """
    Save agent output to the output directory.
    Returns the full file path of the saved file.
    """
    target_dir = os.path.join(OUTPUT_DIR, subfolder) if subfolder else OUTPUT_DIR
    os.makedirs(target_dir, exist_ok=True)

    filepath = os.path.join(target_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[FileTool] Saved: {filepath}")
    return filepath


def load_output(filename: str, subfolder: str = "") -> str:
    """
    Load a previously saved output file.
    """
    target_dir = os.path.join(OUTPUT_DIR, subfolder) if subfolder else OUTPUT_DIR
    filepath = os.path.join(target_dir, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Output file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def timestamped_filename(prefix: str, extension: str = "md") -> str:
    """Generate a timestamped filename."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{extension}"
