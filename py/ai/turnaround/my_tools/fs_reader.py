from smolagents import tool
import os
from huggingface_hub import list_models

@tool
def fs_reader(task: str) -> str:
    """
    This tool reads a file from the filesystem and returns its content.
    This can read on plain text files, markdown files, source code files, etc.
    It is useful for reading files that are part of the project or for reading
    files that are provided as input to the agent.
    Args:
        task (str): The path to the file to read.
    Returns:
        str: The content of the file or an error message if the file cannot be read.
    """
    # check if the file exists on the filesystem
    if not task:
        return "No file path provided."
    
    # Expand user path (handle ~ symbol)
    expanded_path = os.path.expanduser(task)
    
    try:
        with open(expanded_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return f"File not found: {expanded_path} (original path: {task})"
    except Exception as e:
        return f"An error occurred while reading the file: {str(e)}"