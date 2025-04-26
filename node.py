from __future__ import annotations
from typing import Callable, Dict, Any, Set, List, Optional
from .core_type import NodeInputType
from .errors import NodeConnectionError, NodeValidationError, NodeExecutionError
from .api_clients import get_client
from .logger import OrchestratorLogger

class NodeCall:
    """
    Represents a call to a BaseNode within a workflow,
    holding its prototype, inputs (other NodeCall instances),
    and an optional alias for namespacing.
    """
    def __init__(self, prototype: BaseNode, inputs: List[NodeCall], alias: Optional[str] = None):
        self.prototype = prototype
        self.inputs = inputs
        self.alias = alias

    @property
    def input_types(self) -> NodeInputType:
        """
        Return the NodeInputType of the underlying prototype,
        describing required and optional inputs.
        """
        return self.prototype.input_types

    @property
    def output_types(self) -> NodeInputType:
        """
        Return the NodeInputType of the underlying prototype,
        describing output keys and types.
        """
        return self.prototype.output_types

    def get_inputs(self) -> List['NodeCall']:
        """
        Get the list of NodeCall instances feeding into this call.
        """
        return self.inputs

    def get_output_keys(self) -> List[str]:
        """
        Get the list of output keys produced by this call,
        including both required and optional keys.
        """
        required = list(self.output_types.required.keys())
        optional = list(self.output_types.optional.keys())
        return required + optional

    def __repr__(self) -> str:
        alias_part = f" as '{self.alias}'" if self.alias else ""
        return f"<NodeCall {self.prototype.name}{alias_part}>"

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
        run_fn: Callable[..., Dict[str, Any]]
    ):
        self.name = name
        self.input_types = input_types
        self.output_types = output_types
        self.logger = OrchestratorLogger.get_logger()
        if run_fn is None:
            raise ValueError('run_fn must be provided for BaseNode')
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

    def clone(self, name: str) -> "BaseNode":
        """
        Returns a new instance with the same logic and types,
        but a new name (useful for parallel branches).
        """
        return BaseNode(
            name=name,
            input_types=self.input_types,
            output_types=self.output_types,
            run_fn=self._run_fn,
        )

    def __call__(self, *upstream_calls: NodeCall, alias: Optional[str] = None) -> NodeCall:
        """
        Create a NodeCall representing this BaseNode applied to upstream NodeCall instances.
        """
        call = NodeCall(self, list(upstream_calls), alias)
        # register the call in the active workflow
        from .workflow import Workflow
        if Workflow.current is None:
            raise RuntimeError(
                "No active Workflow. Please use 'with Workflow(...) as wf:' to create one."
            )
        Workflow.current.register_call(call)
        return call

class LlmNode(BaseNode):
    """
    Node implementation using LLM provider.
    """
    def __init__(
        self,
        name: str,
        input_types: NodeInputType,
        output_types: NodeInputType,
        provider: str,
        model_name: str
    ):
        self.provider = provider
        self.model_name = model_name
        self.logger = OrchestratorLogger.get_logger()
        client = get_client(provider, model_name)
        output_keys = list(output_types.required.keys() or output_types.optional.keys())
        if len(output_keys) != 1:
            raise ValueError(
                f'For an LLM node with provider, exactly 1 output must be defined. Found: {output_keys}'
            )
        self._output_key = output_keys[0]

        def llm_run_fn(**inputs: Any) -> Dict[str, Any]:
            messages = inputs.get('messages')
            if messages is None:
                raise NodeValidationError(
                    f'Node {name} expects "messages" to call the LLM'
                )
            try:
                content = client.generate(
                    messages=messages,
                    **{k: v for k, v in inputs.items() if k != 'messages'}
                )
            except Exception as exc:
                self.logger.error(f'LLM error for {name}: {exc}')
                raise NodeExecutionError(f'LLM error for {name}: {exc}')
            return {self._output_key: content}

        super().__init__(name, input_types, output_types, run_fn=llm_run_fn)

    def clone(self, name: str) -> "LlmNode":
        """
        Clone this LlmNode with the same provider and model settings.
        """
        return LlmNode(
            name=name,
            input_types=self.input_types,
            output_types=self.output_types,
            provider=self.provider,
            model_name=self.model_name,
        )
    
class InputNode(BaseNode):
    def __init__(self, name: str,input_types : NodeInputType, output_types: NodeInputType):
        # pas de run_fn ; c’est juste un placeholder dans le graphe
        super().__init__(name=name,
                         input_types=input_types, 
                         output_types=output_types,
                         run_fn=lambda **kwargs: kwargs)