import os
# Hypothétique librairie Google PaLM
from google import genai
from .base_client import BaseClient

class GoogleClient(BaseClient):
    def __init__(self, model_name: str):
        super().__init__(model_name)
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise EnvironmentError('Variable GEMINI_API_KEY not defined')
        client = genai.Client(api_key="GEMINI_API_KEY")

    def generate(self, messages, **kwargs):
        prompt = "".join([m['content'] for m in messages if m['role'] in ('system','user')])
        response = self.client.models.generate_content(
            model=self.model_name,
            prompt=prompt,
            **kwargs
        )
        return response.text
