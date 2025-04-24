from typing import Callable, Dict, Any, Set, Optional
from .types import NodeInputType
from .errors import NodeConnectionError, NodeValidationError, NodeExecutionError
from .api_clients import get_client
from .logger import OrchestratorLogger

class BaseNode:
    '''
    Base class for any Node/Agent. Defines inputs, outputs, and run logic.

    Can be initialized with a Python function (run_fn) or through an LLM provider.
    '''
    def __init__(
        self,
        name: str,
        input_types: NodeInputType,
        output_types: NodeInputType,
        run_fn: Optional[Callable[..., Dict[str, Any]]] = None,
        provider: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.name = name
        self.input_types = input_types
        self.output_types = output_types
        self.logger = OrchestratorLogger.get_logger()

        # Initialization using an LLM provider
        if provider is not None:
            if run_fn is not None:
                raise ValueError('Do not provide run_fn when provider is specified.')
            if model_name is None:
                raise ValueError('model_name is required when provider is specified.')
            self.client = get_client(provider, model_name)
            output_keys = list(self.output_types.required.keys() or self.output_types.optional.keys())
            if len(output_keys) != 1:
                raise ValueError(
                    f'For an LLM node with provider, exactly 1 output must be defined. Found: {output_keys}'
                )
            self._output_key = output_keys[0]

            def _llm_run_fn(**inputs: Any) -> Dict[str, Any]:
                messages = inputs.get('messages')
                if messages is None:
                    raise NodeValidationError(
                        f'Node {self.name} expects "messages" to call the LLM'
                    )
                try:
                    content = self.client.generate(messages=messages, **{k: v for k, v in inputs.items() if k != 'messages'})
                except Exception as exc:
                    self.logger.error(f'LLM error for {self.name}: {exc}')
                    raise NodeExecutionError(f'LLM error for {self.name}: {exc}')
                return {self._output_key: content}

            self._run_fn = _llm_run_fn
        else:
            if run_fn is None:
                raise ValueError('Either run_fn or provider must be specified.')
            self._run_fn = run_fn

    def get_input_keys(self) -> Set[str]:
        return self.input_types.keys()

    def get_output_keys(self) -> Set[str]:
        return self.output_types.keys()

    def validate_connection(self, upstream_node: 'BaseNode') -> None:
        missing_keys = set(self.input_types.required.keys()) - set(upstream_node.get_output_keys())
        if missing_keys:
            self.logger.error(f'Connection error {upstream_node.name} -> {self.name}: missing {missing_keys}')
            raise NodeConnectionError(
                f'Cannot connect {upstream_node.name} -> {self.name}: missing keys {missing_keys}'
            )

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.debug(f'Node {self.name} starting with inputs: {inputs}')
        try:
            self.input_types.validate(inputs)
        except Exception as exc:
            self.logger.error(f'Input validation failed for {self.name}: {exc}')
            raise NodeValidationError(f'Input validation for {self.name} failed: {exc}')

        try:
            results = self._run_fn(**inputs)
        except NodeExecutionError:
            raise
        except Exception as exc:
            self.logger.error(f'Execution error in {self.name}: {exc}')
            raise NodeExecutionError(f"Error during execution of node {self.name}: {exc}") from exc

        try:
            self.output_types.validate(results)
        except Exception as exc:
            self.logger.error(f'Output validation failed for {self.name}: {exc}')
            raise NodeValidationError(f'Output validation for {self.name} failed: {exc}')

        self.logger.debug(f'Node {self.name} completed with outputs: {results}')
        return results