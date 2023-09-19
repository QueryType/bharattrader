import openai
import os
from dotenv import load_dotenv, find_dotenv

model_name = 'gpt-4' #gpt-3.5-turbo

def get_completion(prompt, model=model_name):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

def get_completion_large(messages, 
                        model=model_name, 
                        temperature=0, 
                        max_tokens=1000):
    continuation_token = None

    while True:
        response = openai.Completion.create(
            model=model,
            messages=messages,
            temperature=temperature, 
            max_tokens=max_tokens,
            continuation_token=continuation_token
        )

        chunk = response.choices[0].message['content']
        messages.append({'role': 'system', 'content': chunk})

        continuation_token = response['choices'][0]['finish_reason']

        if continuation_token == 'stop':
            break

    return response.choices[0].message["content"]


def get_completion_from_messages(messages, 
                                 model=model_name, 
                                 temperature=0, 
                                 max_tokens=500):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, 
        max_tokens=max_tokens,
    )
    return response.choices[0].message["content"]

def set_api():
    _ = load_dotenv(find_dotenv()) # read local .env file
    openai.api_key = os.environ['OPENAI_API_KEY']
