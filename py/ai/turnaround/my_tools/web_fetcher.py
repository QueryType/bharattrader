from smolagents import tool
import os
from openai import OpenAI
import json

model="gpt-4.1-mini"
client = OpenAI()

@tool
def search_web(query: str) -> str:
    """
    This tool searches the web for the given query and returns the results.
    It is useful for gathering information from the web to assist in decision-making or analysis.
    Args:
        query (str): The search query to use. Be as specific as possible to get relevant results.
    Returns:
        str: The search results or an error message if the search fails. It is json formatted string.
    """
    # check if the file exists on the filesystem
    if not query:
        return "No file path provided."
    
    response = client.responses.create(
        model=model,  # or another supported model
        input=query,
        tools=[
            {
                "type": "web_search"
            }
        ]
    )
    return json.dumps(response.output, default=lambda o: o.__dict__, indent=2)