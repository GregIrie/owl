import os
from anthropic import Anthropic
from .base_client import BaseClient

class AnthropicClient(BaseClient):
    def __init__(self, model_name: str):
        super().__init__(model_name)
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise EnvironmentError('Variable ANTHROPIC_API_KEY not defined')
        self.client = Anthropic(api_key=api_key)

    def generate(self, messages, **kwargs):
        prompt = messages
        response = self.client.messages.create(
            model=self.model_name,
            prompt=prompt,
            **kwargs
        )
        return response.completion
