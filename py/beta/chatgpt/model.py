import openai


def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

def get_completion_large(messages, 
                        model="gpt-3.5-turbo", 
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
                                 model="gpt-3.5-turbo", 
                                 temperature=0, 
                                 max_tokens=500):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, 
        max_tokens=max_tokens,
    )
    return response.choices[0].message["content"]

f = open(f'api.txt')
api_key = f.read()
f.close()

def set_api():
    openai.api_key  = api_key
