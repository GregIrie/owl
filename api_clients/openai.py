import os
from openai import OpenAI

from .base_client import BaseClient

class OpenAIClient(BaseClient):
    def __init__(self, model_name: str):
        super().__init__(model_name)
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise EnvironmentError('Variable OPENAI_API_KEY not defined')
        self.client = OpenAI()

    def generate(self, message, **kwargs):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": message
                }
                ],           
            **kwargs
        )
        return response.choices[0].message.content
