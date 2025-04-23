from functools import wraps
from typing import Callable, Dict, Any, Optional, List

from .node import BaseNode
from .types import NodeInputType
from .workflow import Workflow
from .errors import NodeConnectionError

# Registry to store declared nodes
_nodes_registry: Dict[str, BaseNode] = {}

def node(
    name: str,
    input_types: NodeInputType,
    output_types: NodeInputType,
    provider: Optional[str] = None,
    model_name: Optional[str] = None
) -> Callable[[Callable[..., Dict[str, Any]]], BaseNode]:
    """
    Decorator to declare a Node.

    Arguments:
        name: unique node name
        input_types: NodeInputType for inputs
        output_types: NodeInputType for outputs
        provider: LLM provider (openai, google, anthropic)
        model_name: model name in the provider
    Returns a BaseNode instance registered under the given name.
    """
    def decorator(fn: Callable[..., Dict[str, Any]]) -> BaseNode:
        if name in _nodes_registry:
            raise NodeConnectionError(f"Node '{name}' already declared.")
        # Creation of the BaseNode
        node_obj = BaseNode(
            name=name,
            input_types=input_types,
            output_types=output_types,
            run_fn=fn,
            provider=provider,
            model_name=model_name
        )
        _nodes_registry[name] = node_obj
        return node_obj

    return decorator

def workflow(name: str) -> Callable[[Callable[..., Any]], Callable[..., Workflow]]:
    """
    Decorator to declare a Workflow.

    The decorated function should accept an argument `wf: Workflow` and add/connect nodes to it.
    Adds automatic validations:
      - Topological sort (cycles)
      - Detection of orphan nodes
    """
    def decorator(build_fn: Callable[..., Any]) -> Callable[..., Workflow]:
        @wraps(build_fn)
        def wrapper(*args: Any, **kwargs: Any) -> Workflow:
            wf = Workflow(name)
            # Call the workflow construction function
            build_fn(wf, *args, **kwargs)
            # Cycle validation
            try:
                ordered: List[BaseNode] = wf._topological_sort()
            except NodeConnectionError as exc:
                raise NodeConnectionError(
                    f"Validation of workflow '{name}' failed (cycle detected): {exc}"
                )
            # Detection of orphan nodes
            orphan_nodes = [node.name for node in wf.nodes
                            if not wf.connections.get(node)
                            and all(node not in dests for dests in wf.connections.values())]
            if orphan_nodes:
                raise NodeConnectionError(
                    f"Orphan nodes detected in workflow '{name}': {orphan_nodes}"
                )
            return wf
        return wrapper
    return decorator

def get_registered_nodes() -> Dict[str, BaseNode]:
    """Returns the registry of declared nodes."""
    return dict(_nodes_registry)
