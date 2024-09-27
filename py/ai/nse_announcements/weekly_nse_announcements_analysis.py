import pandas as pd
import requests
import fitz  # PyMuPDF
import os
from openai import OpenAI
from urllib.parse import urlparse
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
import argparse
import logging

log_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOCAL_MODEL = '' #'llama3.1:latest'  # keep it blank if, gpt is used
LOCAL_URL = 'http://10.0.0.4:7862/v1'  # Update with cloud URL or Local
GPT_MODEL = 'gpt-4o-mini'  # if LOCAL_MODEL is blank, GPT will be used
CONTEXT_LEN = 1500

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Load environment variables
def set_api():
    load_dotenv(find_dotenv())
    return os.getenv('OPENAI_API_KEY')

# Get LLM client (GPT or local)
def get_llm_client_model():
    if not LOCAL_MODEL:
        gpt_client = OpenAI(api_key=set_api())
        return gpt_client, GPT_MODEL
    else:
        my_local_client = OpenAI(base_url=LOCAL_URL, api_key="local-llm")
        return my_local_client, LOCAL_MODEL

client, model = get_llm_client_model()

critical_subjects = [
    "Updates", "Press Release", "Financial Result Updates", "Sale or Disposal-XBRL",
    "Acquisition-XBRL", "Record Date", "Investor Presentation",
    "Change in Directors/Key Managerial Personnel/Auditor/Compliance Officer/Share Transfer Agent",
    "Acquisition", "Scheme of Arrangement", "Resignation", "Appointment", 
    "Date of Payment of Dividend", "Dividend", "Increase in Authorised Capital",
    "Credit Rating", "Rights Issue", "Public Announcement-Open Offer"
]

routine_updates_subjects = [
    "Shareholders meeting", "Outcome of Board Meeting", "Copy of Newspaper Publication",
    "Analysts/Institutional Investor Meet/Con. Call Updates", "Loss/Duplicate-Share Certificate-XBRL",
    "Board Meeting Intimation", "Trading Window-XBRL", "Notice Of Shareholders Meetings-XBRL",
    "Change in Director(s)", "ESOP/ESOS/ESPS", "Clarification - Financial Results",
    "Corporate Insolvency Resolution Process-XBRL", "Limited Review Report",
    "Disclosure under SEBI (PIT) Reg 2015"
]

# Function to download and extract PDF or XML text
def download_and_extract_pdf(url, local_path):
    # Skip download if file already exists
    if os.path.exists(local_path):
        logger.info(f"File already exists locally: {local_path}")
        return extract_pdf_text(local_path)

    try:
        # Make the request to download the file
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()  # Ensure no bad response

        # Check the Content-Type header to determine file type
        content_type = response.headers.get('Content-Type')
        file_extension = None
        
        if 'application/pdf' in content_type:
            file_extension = 'pdf'
        elif 'application/xml' in content_type:
            file_extension = 'xml'
        
        # Ensure we append the correct file extension to local_path
        if file_extension:
            local_path += f'.{file_extension}'
        else:
            logger.warning(f"Unknown content type: {content_type}. Assuming default .pdf")
            file_extension = 'pdf'
            local_path += '.pdf'
        
        # Write the file to the local path
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        # Extract text based on file type
        if file_extension == 'pdf':
            return extract_pdf_text(local_path)
        elif file_extension == 'xml':
            return extract_xml_text(local_path)
        else:
            logger.error(f"Unsupported file type: {file_extension}")
            return ""
    
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return ""

# Function to extract text from PDF
def extract_pdf_text(local_path):
    try:
        doc = fitz.open(local_path)
        text = "".join(page.get_text() for page in doc)
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {local_path}: {e}")
        return ""

# Function to extract text from XML
def extract_xml_text(local_path):
    try:
        with open(local_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to extract text from XML file {local_path}: {e}")
        return ""

# Truncate text to context length
def truncate_words(text):
    words = text.split()
    return ' '.join(words[:CONTEXT_LEN]) if len(words) > CONTEXT_LEN else text

# Get summary and sentiment using OpenAI API
def get_summary_and_sentiment(text):
    truncated_text = truncate_words(text)
    try:
        response = client.chat.completions.create(
            model=model, temperature=1.0, max_tokens=500,
            messages=[
                {"role": "user", "content": "Please summarize the company announcement provided."},
                {"role": "user", "content": truncated_text}
            ]
        )
        summary = response.choices[0].message.content
        sentiment_response = client.chat.completions.create(
            model=model, temperature=1.0, max_tokens=20,
            messages=[
                {"role": "user", "content": f"Provide an investor sentiment analysis score in a scale between 0 (negative sentiment) to 1 (positive sentiment) for the following text. The answer should be a single float value, no explanation is required: {summary}"}
            ]
        )
        sentiment_score = float(sentiment_response.choices[0].message.content.strip())
        return summary, sentiment_score
    except Exception as e:
        logger.error(f"Error in generating summary/sentiment: {e}")
        return "", -1.0

# Write result to file
def write_to_file(file, data):
    with open(file, 'a') as f:
        f.write(data)

# Main processing function
def process_announcement(index, row, stock):
    pdf_url = row['ATTACHMENT']
    filename = os.path.basename(urlparse(pdf_url).path)
    pdf_local_path = os.path.join('notifications', filename)
    pdf_text = download_and_extract_pdf(pdf_url, pdf_local_path)
    summary, sentiment_score = get_summary_and_sentiment(pdf_text)
    return {
        'Stock': stock, 'Company': row['COMPANY NAME'], 'Subject': row['SUBJECT'],
        'Summary': summary, 'Score': sentiment_score, 'Link': row['ATTACHMENT']
    }

# Main function
def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze announcements')
    parser.add_argument('--file', type=str, help='Input file path')
    parser.add_argument('--start', type=str, help='Stock to start from in stocks.csv')
    args = parser.parse_args()

    try:
        stocks = pd.read_csv("stocks.csv", usecols=["Ticker"])
        df = pd.read_csv(args.file)
        df = df[~df['SUBJECT'].isin(routine_updates_subjects) & df['SUBJECT'].isin(critical_subjects)]
        logger.info(f"Analyzing {len(df)} announcements")

        result_df = pd.DataFrame(columns=['Stock', 'Company', 'Subject', 'Summary', 'Score', 'Link'])

        for stock in stocks["Ticker"]:
            for index, row in df[df['SYMBOL'] == stock].iterrows():
                try:
                    result = process_announcement(index, row, stock)
                    # Append the new row to the DataFrame
                    result_df.loc[len(result_df)] = result
                except Exception as e:
                    logger.error(f"Error processing {stock}: {e}")

        file_name = f'output/{args.file}_report_{log_timestamp}.csv'
        result_df.to_csv(file_name, index=False)
        logger.info(f"Results saved to {file_name}")

    except Exception as e:
        logger.error(f"Error during processing: {e}")

if __name__ == "__main__":
    main()
