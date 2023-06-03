import re
import model as ai
import os

screener_xls_data = {}
delimiter = "####"

company_data = 'companyinfo/sjvn'

screener_tabs = ['income_statement','income_statement_quarterly', 'balance_sheet', 'cashflow_statement', 'ratio_analysis']
screener_data = {}

def preprocess_text(text):
    # Lowercase the text
    text = text.lower()

    # Remove special characters
    text = re.sub(r'\W', ' ', text)

    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)

    return text

def load_screener_data():

    for i in range(0, len(screener_tabs)):
        tabname = screener_tabs[i]
        f = open(f'{company_data}/{tabname}.txt')
        data = f.read()
        f.close()
        screener_data[tabname] = data


def company_info_analysis():
    file = f'{company_data}/company_info.txt'
    data = 'No company info'
    if os.path.isfile(file):
        f = open(file)
        data = f.read()
        f.close()
    print('Analyzing company_info data...') 
    system_message = f'As a financial analyst for equity markets, perform an evaluation of the company based on the inputs provided. The input is enclosed within {delimiter}.\
        You must to the analysis in the following steps.\
        Step 8: Prepare a short description of the comapnys business, factories, plants and operations in general.\
        Step 9: Prepare shareholding trend and status, separetly, if shareholding data is provided. \
        Step 10: Perpare a separate detailed summary of concall data if provided. \
        Step 11: If credit rating data is provided, list out positive and negative points separately. \
        Give your analysis in as detailed manner as possible, however summarize it to limit to max_tokens = 2000 '
    user_message = f'{delimiter}{data}{delimiter}'
    messages =  [  
        {'role':'system', 
        'content': system_message},    
        {'role':'user', 
        'content': f"{delimiter}{user_message}{delimiter}"},  
        ] 
    response = ai.get_completion_from_messages(messages,max_tokens=2000)
    return response

def fin_statement_analysis():
    print('Analyzing screener data...')
    system_message = f'As a financial analyst for equity markets, you need to perform an evaluation of the company based on the inputs provided. Some of these inputs will be standard financial data and some will be unstructured. \
            The input data will be encloded with {delimiter} You must to the analysis in the following steps. \
            Step 1:{delimiter} Perform a financial analysis of the company from stock market investing perspective from its annual income statement quarterly income statment \
                balance sheet and cashflow statement. Each will be provided to you enclosed as {delimiter}income_statement:{delimiter} {delimiter}balance_sheet{delimiter} and so on. \
                Step 2: Using the ratio_analysis statement analyze the working capital cycle. Step 3: Perform a Du-Pont analysis using the above data. Step 4: Perform profitibility analysis of this financial data\
                    Step 5: Provide trend analysis and competitive advantages of the company based on given financial data. Step 6: Check pricing power of this company? \
                    Step 6: Detect and report any red flags about the company from the data \
                    Step 7: Report preparation/ Take special care. As an analyst perform these analysis and prepare a report that is very detailed but summarize it to limit to  max_tokens=2000.'

    msg = ''
    for key,val in screener_data.items():
        msg = f'{delimiter}{key}:{val}{delimiter}'
    user_message = f'{delimiter}{msg}{delimiter}'
    messages =  [  
        {'role':'system', 
        'content': system_message},    
        {'role':'user', 
        'content': f"{delimiter}{user_message}{delimiter}"},  
        ] 
    response = ''
    response = ai.get_completion_from_messages(messages,max_tokens=2000)
    return response


def main():
    ai.set_api()
    load_screener_data()

    #Financial statement analysis from screener data
    fin_screener_analysis = ''
    fin_screener_analysis = fin_statement_analysis()
    # print(fin_screener_analysis)
    with open(f'{company_data}/financial_analysis.txt', 'w', encoding='utf-8') as file:
        file.write(fin_screener_analysis)

    #Perform company info analysis from data from internet and elsewhere
    co_info_analysis = ''
    co_info_analysis = company_info_analysis()
    with open(f'{company_data}/company_info_analysis.txt', 'w', encoding='utf-8') as file:
        file.write(co_info_analysis)

    print('Done')

if __name__ == "__main__":
    main()
