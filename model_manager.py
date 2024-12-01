# model_manager.py

from openai import OpenAI
import requests
import anthropic
import streamlit as st

class ModelManager:
    """
    A class to manage different language models.
    """
    def __init__(self, model_name, api_key, provider='openai'):
        self.model_name = model_name
        self.api_key = api_key
        self.provider = provider.lower()

        if self.provider == 'openai':
            self.client = OpenAI(api_key=self.api_key)
        elif self.provider == 'anthropic':
            self.client = anthropic.Client(api_key=self.api_key)
        else:
            raise ValueError("Unsupported provider")

    def generate_response(self, prompt, **kwargs):
        """
        Generate a response from the specified model.
        """
        if self.provider == 'openai':
            return self._generate_openai_response(prompt, **kwargs)
        elif self.provider == 'anthropic':
            return self._generate_anthropic_response(prompt, **kwargs)
        else:
            return ""

    def _generate_openai_response(self, prompt, **kwargs):
        """
        Generate a response using OpenAI's API.
        """
        try:
            # Determine if the model is a chat model
            chat_models = [
                "gpt-4",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
                "gpt-4o-mini",
                "gpt-4o",
                "o1-mini-2024-09-12",
                "o1-preview-2024-09-12"
            ]

            if self.model_name in chat_models:
                messages = kwargs.get('messages', [
                    {'role': 'user', 'content': prompt}
                ])
                # Remove 'messages' from kwargs if it exists
                kwargs.pop('messages', None)

                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    **kwargs
                )
                return response.choices[0].message.content.strip()
            else:
                # For completion models
                response = self.client.completions.create(
                    model=self.model_name,
                    prompt=prompt,
                    **kwargs
                )
                return response.choices[0].text.strip()
            content = response.choices[0].message.content
            if content:
                return content.strip()
            else:
                print("Received empty response from OpenAI.")
                return ""
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Return the error message for visibility
            return f"Error: {e}"

    def _generate_anthropic_response(self, prompt, **kwargs):
        """
        Generate a response using Anthropic's Messages API.
        """
        try:
            # Prepare parameters
            max_tokens = kwargs.pop('max_tokens', 256)
            temperature = kwargs.pop('temperature', 1.0)

            # Define the message structure for Anthropic's Messages API
            messages = [
                {"role": "user", "content": prompt}
            ]

            response = self.client.messages.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs  # Remaining kwargs
            )

            # Access the assistant's reply from 'response'
            if isinstance(response.content, list):
                return "\n".join([block.text for block in response.content]).strip()
            else:
                return response.content.strip()

        except Exception as e:
            print(f"Anthropic API error: {e}")
            return ""