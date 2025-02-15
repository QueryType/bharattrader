import os
import requests
from markitdown import MarkItDown
from dotenv import load_dotenv, find_dotenv
from google import genai
import datetime

"""
Retrieve the news content from a location  https://example.xxxstockxxxnews.com
Then convert it to markdown format using markitdown library.
Then pass on the markdown content to Google Gemini API to arrange and group the news feed provided based on the order of importance for an investor in the markets.
"""

news_url = 'https://example.xxxstockxxxnews.com'

# Initialize the client, using Google Gemini API key
def initialize_client(api_key_env_var):
    load_dotenv(find_dotenv())
    api_key = os.getenv(api_key_env_var)
    if not api_key:
        raise ValueError(f"API key not found in environment variable {api_key_env_var}")
    return genai.Client(api_key=api_key)

my_model = 'gemini-2.0-flash'
client = initialize_client('GOOGLE_API_KEY')

# Main function
if __name__ == '__main__':

    # Current time is, dd-mm-YYYY HH:MM:SS
    timenow = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # get the news file
    print(f"Start getting the news file at {timenow}...")
    response = requests.get(news_url)
    html_content = response.text
    # Save it to a file
    with open('output.html', 'w') as file:
        file.write(html_content)

    print(f"Start converting the news file to markdown format at {timenow}...")
    md = MarkItDown()
    result = md.convert("output.html")
    #print(result.text_content)
    # Save the markdown content to a file
    with open('output.md', 'w') as file:
        file.write(result.text_content)

    print(f"Start arranging the news file at {timenow}...")
    analyzer = client.chats.create(model=my_model)
    response = analyzer.send_message(f"Arrange and group the news feed provided based on the order of importance for an investor in the markets. Include whatever data related to the news is available in the input, such as short summaries, hyperlinks etc. If available include time of report of the news. The time now is: {timenow}. The input is in markdown. Input: {result.text_content}")
    output = ""
    parts = response.candidates[0].content.parts
    if parts is None:
            print(f'finish_reason={response.candidates[0].finish_reason}')
    for part in parts:
        if part.text:
            #print(part.text)
            # join the text parts
            output += part.text

    # Save the output to a file
    with open('output_arranged.md', 'w') as file:
        file.write(output)
