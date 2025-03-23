# analysis_utils.py

import os
import json
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown
import markdown2
from dotenv import load_dotenv, find_dotenv
from google import genai

console = Console()

def initialize_client(api_key_env_var):
    load_dotenv(find_dotenv())
    api_key = os.getenv(api_key_env_var)
    if not api_key:
        raise ValueError(f"API key not found in environment variable {api_key_env_var}")
    return genai.Client(api_key=api_key)

def show_json(obj):
    print(json.dumps(obj.model_dump(exclude_none=True), indent=2))

def show_parts(response):
    parts = response.candidates[0].content.parts
    if parts is None:
        print(f'finish_reason={response.candidates[0].finish_reason}')
        return
    for part in parts:
        if part.text:
            console.print(Markdown(part.text, hyperlinks=True))
    grounding_metadata = response.candidates[0].grounding_metadata
    if grounding_metadata and grounding_metadata.search_entry_point:
        console.print(grounding_metadata.search_entry_point.rendered_content)

def log_message(log_file, message, message_type="info"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"<p><strong>{timestamp}</strong> - <span class='{message_type}'>{message}</span></p>\n"
    with open(log_file, 'a', encoding='utf-8') as file:
        file.write(log_entry)

def log_message_r(log_file, response, message_type="model"):
    parts = response.candidates[0].content.parts
    log_message_content = "Response: "
    if parts is None:
        log_message_content += f"\n{response.candidates[0].finish_reason}"
    else:
        log_message_content += "".join(part.text for part in parts if part.text)
    log_message_content = markdown2.markdown(log_message_content)
    grounding_metadata = response.candidates[0].grounding_metadata
    if grounding_metadata and grounding_metadata.search_entry_point:
        log_message_content += grounding_metadata.search_entry_point.rendered_content
    log_message(log_file, log_message_content, message_type)

def start_log_file(log_file):
    with open(log_file, 'w') as file:
        file.write("<html><head><style>.info {color: blue;} .user {color: green;} .model {color: red;}</style></head><body>\n")

def end_log_file(log_file):
    with open(log_file, 'a') as file:
        file.write("</body></html>")
