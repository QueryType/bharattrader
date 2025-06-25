# load .env into environment
import os
from dotenv import load_dotenv
load_dotenv()

from smolagents import CodeAgent, MLXModel
from my_tools import search_web as web_fetcher
from my_tools import save_report as save_report
from my_tools import fs_reader as fs_reader
from my_tools import cmd_executor  as cmd_executor
from smolagents import CodeAgent, LiteLLMModel

import datetime
import csv

# Initialize the tools and models
#local_model=mlx_model = MLXModel("Path to local model directory")
model = LiteLLMModel(model_id="openai/gpt-4.1-mini", api_key=os.getenv("OPENAI_API_KEY"))

#Create the agent with the model and tools
agent = CodeAgent(tools=[web_fetcher, save_report, fs_reader, cmd_executor], model=model, additional_authorized_imports=["os", "openai", "json", "csv"]) # Not adding base tools.

# Define the data directory and today's date
data_dir = "data/financial_data.csv"
date_today = datetime.datetime.now().strftime("%Y-%m-%d")

instructions = f"""
You are an expert financial analyst specializing in identifying turnaround in companies. Analyze for the company mentioned below in Step 1. With the searched financial data and your analysis generate a comprehensive markdown report that detects potential turnarounds if any for the company. To achieve this, you will follow these steps in sequence:
Step 1. Company/Business Name/Stock Codes: {{business_name}}.
Step 2. For this business, analyse if the business is experiencing a turnaround. Give a short report of your analysis. You will gather additional latest information using the web_fetcher tool. This includes searching for the latest financial reports, news, and other relevant information about the company.
Step 3. After gathering enough information, you will prepare a report that includes a verdict about the turnaround potential of each business. The verdict can be "Strong Turnaround", "Weak Turnaround", or "No Turnaround".
Step 4. Finally, format the report into a well-structured markdown document and save it to a file. You will ensre that the report contains the following sections:
- Business Name
- Summary of Financial Data
- Analysis of Financial Health
- Turnaround Potential Verdict
Step 5. You will use the save_report tool to persist the report on disk. The report will be saved per business. You will pass the report content and the business name to the save_report tool.

General instructions:
You will use the web_fetcher tool to gather additional information about these businesses and the reporter tool to generate the markdown report. You can look up for latest financial reports, news and other relevant information for the company. 
Today is: {date_today}.
Always search for tools available to you before writing new code, esp. the cmd_executor tool, which can execute read only shell commands to gather more information if needed.
"""

# Read the financial data file and start the analysis
print("Loading financial data from:", data_dir)
if not os.path.exists(data_dir):
    raise FileNotFoundError(f"The financial data file {data_dir} does not exist. Please check the path.")
businesses = []
with open(data_dir, 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    # For each row in the CSV, create a entry, that contains the Name, Stock Symbol. Assuming the columns are Name,BSE Code,NSE Code. It is possible that BSE Code or NSE Code is not available, Create the entry for businesses list as a concatenation of Name/NSE Code/BSE Code.
    for row in reader:
        name = row.get('Name', 'Unknown')
        bse_code = row.get('BSE Code', '').strip()
        nse_code = row.get('NSE Code', '').strip()
        if not nse_code and not bse_code:
            business_entry = name
        elif not nse_code and bse_code:
            business_entry = f"""Name: {name} / BSE: {bse_code}"""
        elif nse_code and not bse_code:
            business_entry = f"""Name: {name} / NSE: {nse_code}"""
        else:
            business_entry = f"""Name: {name} / NSE: {nse_code} / BSE: {bse_code}"""
        businesses.append(business_entry)

total_businesses = len(businesses)
count = 0
for business in businesses:
    print(f"Starting analyzing financial data and generating a report for {business}... Please wait.")
    final_instructions = instructions.format(business_name=business)
    #print(f"Final instructions for the agent: {final_instructions}")
    response = agent.run(final_instructions, max_steps=20)
    # Print progress
    count += 1
    print(f"Completed {count}/{total_businesses} businesses. Current business: {business}")