from .openai import OpenAIClient
from .google import GoogleClient
from .anthropic import AnthropicClient


def get_client(provider: str, model_name: str):
    provider = provider.lower()
    if provider in ('openai',):
        return OpenAIClient(model_name)
    if provider in ('google', 'palm'):
        return GoogleClient(model_name)
    if provider in ('anthropic', 'claude'):
        return AnthropicClient(model_name)
    raise ValueError(f"Provider inconnu: {provider}")
