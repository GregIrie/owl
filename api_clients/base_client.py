from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseClient(ABC):
    """
    Abstract interface for LLM clients.
    """
    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],  # {'role': 'system'|'user'|'assistant', 'content': str}
        **kwargs: Any
    ) -> str:
        """
        Sends a prompt in the form of messages and returns the textual response.
        """
        pass
