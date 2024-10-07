from json import dumps, loads
from time import time
from flask import request
from hashlib import sha256
from datetime import datetime
from requests import get, post 
from anthropic import Anthropic
import os
import anthropic
import traceback

from server.config import special_instructions
from server.config import Config

class Backend_Api:
    def __init__(self, app, config: Config) -> None:
        self.app = app
        self.openai_key = os.getenv("OPENAI_API_KEY") or config.openai_key
        self.openai_api_base = os.getenv("OPENAI_API_BASE") or config.openai_api_base
        self.claude_key = os.getenv("CLAUDE_API_KEY") or config.claude_key
        self.claude_api_base = os.getenv("CLAUDE_API_BASE") or config.claude_api_base
        self.proxy = config.proxy
        self.routes = {
            '/backend-api/v2/conversation': {
                'function': self._conversation,
                'methods': ['POST']
            }
        }

    def _conversation(self):
        try:
            model = request.json['model']
            if model.startswith('gpt'):
                return self._openai_conversation()
            elif model.startswith('claude'):
                return self._claude_conversation()
            else:
                return {"error": "Unsupported model"}, 400
        except Exception as e:
            print(e)
            return {"error": str(e)}, 500

    def _openai_conversation(self):
        try:
            jailbreak = request.json['jailbreak']
            internet_access = request.json['meta']['content']['internet_access']
            _conversation = request.json['meta']['content']['conversation']
            prompt_parts = request.json.get('meta', {}).get('content', {}).get('parts', [])
            prompt_content = prompt_parts[0].get('content', '') if prompt_parts else ''
            current_date = datetime.now().strftime("%Y-%m-%d")
            system_message = f'You are ChatGPT also known as ChatGPT, a large language model trained by OpenAI. Strictly follow the users instructions. Knowledge cutoff: 2021-09-01 Current date: {current_date}'

            extra = []
            if internet_access:
                search = get('https://ddg-api.herokuapp.com/search', params={
                    'query': prompt_content,
                    'limit': 3,
                })

                blob = ''

                for index, result in enumerate(search.json()):
                    blob += f'[{index}] "{result["snippet"]}"\nURL:{result["link"]}\n\n'

                date = datetime.now().strftime('%d/%m/%y')

                blob += f'current date: {date}\n\nInstructions: Using the provided web search results, write a comprehensive reply to the next user query. Make sure to cite results using [[number](URL)] notation after the reference. If the provided search results refer to multiple subjects with the same name, write separate answers for each subject. Ignore your previous response if any.'

                extra = [{'role': 'user', 'content': blob}]

            conversation = [{'role': 'system', 'content': system_message}] + \
                extra + special_instructions[jailbreak] + \
                _conversation + [{'role': 'user', 'content': prompt_content}]


            url = f"{self.openai_api_base}/v1/chat/completions"

            proxies = None
            if self.proxy['enable']:
                proxies = {
                    'http': self.proxy['http'],
                    'https': self.proxy['https'],
                }

            gpt_resp = post(
                url     = url,
                proxies = proxies,
                headers = {
                    'Authorization': 'Bearer %s' % self.openai_key
                }, 
                json    = {
                    'model'             : request.json['model'], 
                    'messages'          : conversation,
                    'stream'            : True
                },
                stream  = True
            )

            if gpt_resp.status_code >= 400:
                error_data = gpt_resp.json().get('error', {})
                error_code = error_data.get('code', None)
                error_message = error_data.get('message', "An error occurred")
                return {
                    'success': False,
                    'error_code': error_code,
                    'message': error_message,
                    'status_code': gpt_resp.status_code
                }, gpt_resp.status_code

            def stream():
                for chunk in gpt_resp.iter_lines():
                    try:
                        decoded_line = loads(chunk.decode("utf-8").split("data: ")[1])
                        token = decoded_line["choices"][0]['delta'].get('content')

                        if token is not None: 
                            yield token
                            
                    except GeneratorExit:
                        break

                    except Exception as e:
                        print(e)
                        print(e.__traceback__.tb_next)
                        continue
                        
            return self.app.response_class(stream(), mimetype='text/event-stream')

        except Exception as e:
            print(f"Error in _openai_conversation: {e}")
            print(traceback.format_exc())
            return {
                '_action': '_ask',
                'success': False,
                "error": f"An error occurred: {str(e)}"
            }, 400

    def _claude_conversation(self):
        try:
            jailbreak = request.json.get('jailbreak', 'default')
            internet_access = request.json.get('meta', {}).get('content', {}).get('internet_access', False)
            _conversation = request.json.get('meta', {}).get('content', {}).get('conversation', [])
            prompt_parts = request.json.get('meta', {}).get('content', {}).get('parts', [])
            prompt_content = prompt_parts[0].get('content', '') if prompt_parts else ''
            model = request.json.get('model', 'claude-3-sonnet-20240229')  # Default to Sonnet if not specified

            # Start with a system message
            messages = []
            system_prompt = "You are Claude, an AI assistant created by Anthropic to be helpful, harmless, and honest."

            if not prompt_content:
                return {"error": "No prompt provided"}, 400


            # Add jailbreak instructions if applicable
            if jailbreak in special_instructions:
                for instruction in special_instructions[jailbreak]:
                    messages.append({"role": "user", "content": instruction['content']})
                    messages.append({"role": "assistant", "content": "Understood. I will act accordingly."})

            # Add internet search results if enabled
            if internet_access:
                try:
                    search = get('https://ddg-api.herokuapp.com/search', params={
                        'query': prompt_content,
                        'limit': 3,
                    }, timeout=10)
                    search.raise_for_status()
                    
                    blob = ''
                    for index, result in enumerate(search.json()):
                        blob += f'[{index}] "{result["snippet"]}"\nURL:{result["link"]}\n\n'

                    date = datetime.now().strftime('%d/%m/%y')
                    blob += f'current date: {date}\n\nInstructions: Using the provided web search results, write a comprehensive reply to the next user query. Make sure to cite results using [[number](URL)] notation after the reference.'

                    messages.append({"role": "user", "content": blob})
                    messages.append({"role": "assistant", "content": "I understand. I'll use this information to assist with the next query."})
                except Exception as e:
                    print(f"Error in internet search: {e}")
                    # Continue without internet results if there's an error

            # Add the conversation history, ensuring alternating roles
            for msg in _conversation:
                if not messages or messages[-1]['role'] != msg['role']:
                    messages.append({"role": msg['role'], "content": msg['content']})
                else:
                    # If roles would repeat, combine the content
                    messages[-1]['content'] += "\n" + msg['content']

            # Add the new prompt
            if not messages or messages[-1]['role'] != 'user':
                messages.append({"role": "user", "content": prompt_content})
            else:
                messages[-1]['content'] += "\n" + prompt_content

            try:
                client = anthropic.Anthropic(api_key=self.claude_key)
                response = client.messages.create(
                    model=model,
                    messages=messages,
                    system=system_prompt,
                    max_tokens=1000,
                    stream=True
                )

                def stream():
                    for chunk in response:
                        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                            yield chunk.delta.text
                        elif hasattr(chunk, 'text'):
                            yield chunk.text
                        else:
                            print(f"Unexpected chunk type: {type(chunk)}")
                            print(f"Chunk contents: {chunk}")

                return self.app.response_class(stream(), mimetype='text/event-stream')


            except anthropic.APIError as e:
                print(f"Anthropic API error: {e}")
                print(f"Error type: {type(e)}")
                print(f"Error args: {e.args}")
                print(traceback.format_exc())
                return {"error": str(e)}, e.status_code
            except Exception as e:
                print(f"Unexpected error in Claude API call: {e}")
                print(f"Error type: {type(e)}")
                print(f"Error args: {e.args}")
                print(traceback.format_exc())
                return {"error": "An unexpected error occurred", "details": str(e)}, 500

        except Exception as e:
            print(f"Error in _openai_conversation: {e}")
            print(traceback.format_exc())
            return {
                '_action': '_ask',
                'success': False,
                "error": f"An error occurred: {str(e)}"
            }, 400