from analysis_utils import initialize_client, show_parts, log_message, log_message_r, start_log_file, end_log_file
from datetime import datetime
import os

chat_output_folder = "output"
my_model = 'gemini-2.0-flash'
client = initialize_client('GOOGLE_API_KEY')

def main():
    search_tool = {'google_search': {}}
    stock_chat = client.chats.create(model=my_model, config={'tools': [search_tool]})

    while True:
        stock = input('Enter stock or company to chat on (or type bye to leave): ')
        if stock == 'bye':
            break

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f"{chat_output_folder}/{stock}_chat_log_{timestamp}.html"
        start_log_file(log_file)
        log_message(log_file, f"User selected stock/company: {stock}", "info")

        date_now = datetime.now().strftime('%Y-%m-%d')
        stock_prompt_prefix = f'Date today is: {date_now}. Answer following in context of the company/stock_code {stock}, listed in India.\n'
        
        while True:
            input_txt = input('Ask >> : ')
            if input_txt == 'exit':
                break
            log_message(log_file, f"User input: {input_txt}", "user")
            print("-" * 80)
            response = stock_chat.send_message(f"{stock_prompt_prefix}{input_txt}")
            show_parts(response)
            log_message_r(log_file, response, "model")
            print(f'Working on: {stock}\n Type exit to work on new stock/company.')

        end_log_file(log_file)

if __name__ == "__main__":
    main()
