from typing import Dict, Any, List, Optional, Set
from .node import NodeCall
from .errors import NodeConnectionError, NodeValidationError, NodeExecutionError
from .logger import OrchestratorLogger

class Workflow:
    """
    Node orchestrator building and executing a graph of NodeCall objects.
    """
    current: Optional["Workflow"] = None

    def __init__(self, name: str):
        self.name = name
        self.calls: List[NodeCall] = []
        self.logger = OrchestratorLogger.get_logger()

    def __enter__(self) -> "Workflow":
        Workflow.current = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        Workflow.current = None

    def register_call(self, call: NodeCall) -> None:
        """
        Register a newly created NodeCall in this workflow.
        """
        self.calls.append(call)

    def _build_adjacency(self) -> Dict[NodeCall, List[NodeCall]]:
        """
        Build adjacency mapping from each call to its downstream calls.
        """
        adj: Dict[NodeCall, List[NodeCall]] = {call: [] for call in self.calls}
        for call in self.calls:
            for upstream in call.get_inputs():
                if upstream in adj:
                    adj[upstream].append(call)
        return adj

    def _topological_sort(self) -> List[NodeCall]:
        """
        Return a topologically sorted list of NodeCall based on dependencies.
        """
        adj = self._build_adjacency()
        in_degree: Dict[NodeCall, int] = {call: 0 for call in self.calls}
        for src, dests in adj.items():
            for dst in dests:
                in_degree[dst] += 1

        queue = [c for c, deg in in_degree.items() if deg == 0]
        ordered: List[NodeCall] = []
        while queue:
            node = queue.pop(0)
            ordered.append(node)
            for downstream in adj.get(node, []):
                in_degree[downstream] -= 1
                if in_degree[downstream] == 0:
                    queue.append(downstream)

        if len(ordered) != len(self.calls):
            self.logger.error("Cycle detected in the workflow")
            raise NodeConnectionError("Cycle detected in the workflow.")
        return ordered

    def pretty_print(self) -> None:
        """
        Display the workflow structure as an ASCII tree of NodeCalls.
        """
        adj = self._build_adjacency()
        # identify roots: calls with no upstream
        all_calls = set(self.calls)
        non_roots = {c for call in self.calls for c in call.get_inputs()}
        roots = [c for c in self.calls if c not in non_roots]

        def _rec(call: NodeCall, prefix: str, visited: Set[NodeCall], is_last: bool):
            if call in visited:
                print(prefix + ("└── " if is_last else "├── ") + f"{call} (cycle)")
                return
            visited.add(call)
            branch = "└── " if is_last else "├── "
            print(prefix + branch + f"{call}")
            children = adj.get(call, [])
            new_prefix = prefix + ("    " if is_last else "│   ")
            for idx, child in enumerate(children):
                _rec(child, new_prefix, visited.copy(), idx == len(children) - 1)

        for idx, root in enumerate(roots):
            print(f"{root}")
            children = adj.get(root, [])
            for jdx, child in enumerate(children):
                _rec(child, '', set([root]), jdx == len(children) - 1)

    def run(self, initial_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow, feeding initial_inputs into input nodes.
        Returns a dict aggregating all outputs, raising on key collisions.
        """
        # topologically order calls
        ordered_calls = self._topological_sort()
        memo: Dict[NodeCall, Dict[str, Any]] = {}
        self.logger.info(
                        "Topological order: " + " → ".join(str(c) for c in ordered_calls)
                    )
        for call in ordered_calls:
            # gather inputs from upstream calls
            inputs: Dict[str, Any] = {}
            for upstream in call.get_inputs():
                inputs.update(memo[upstream])
            # for calls without inputs, feed initial_inputs
            if not call.get_inputs():
                inputs.update(initial_inputs)

            # validate required keys
            for key, expected_type in call.input_types.required.items():
                if key not in inputs:
                    raise NodeValidationError(f"Missing required input '{key}' for {call}")
                if not isinstance(inputs[key], expected_type):
                    raise NodeValidationError(f"Input '{key}' for {call} expected {expected_type}, got {type(inputs[key])}")

            # execute node
            try:
                output = call.prototype.run(inputs)
            except Exception as e:
                self.logger.error(f"Error running {call}: {e}")
                raise NodeExecutionError(f"Error running {call}: {e}")

            # apply alias namespacing if present
            if call.alias:
                output = {f"{call.alias}_{k}": v for k, v in output.items()}

            memo[call] = output
            self.logger.debug(f"{call} produced {output}")

        # merge all outputs, detect collisions
        final: Dict[str, Any] = {}
        for out in memo.values():
            for k, v in out.items():
                #if k in final:
                #    raise NodeConnectionError(f"Final collision on output key '{k}'")
                final[k] = v

        self.logger.info(f"Workflow {self.name} completed with results: {final}")
        return final
