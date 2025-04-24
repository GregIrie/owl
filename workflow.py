from typing import Dict, Any, List, Set
from .node import BaseNode
from .errors import NodeConnectionError
from .logger import OrchestratorLogger

class Workflow:
    '''
    Node orchestrator, meantt for dynamic addition and execution.
    '''
    def __init__(self, name: str):
        self.name = name
        self.nodes: List[BaseNode] = []
        self.connections: Dict[BaseNode, List[BaseNode]] = {}
        self._key_map: Dict[str, BaseNode] = {}
        self.logger = OrchestratorLogger.get_logger()

    def add_node(self, node: BaseNode) -> 'Workflow':
        self.logger.debug(f'Adding node {node.name} to workflow {self.name}')
        if any(n.name == node.name for n in self.nodes):
            self.logger.error(f'Node {node.name} already exists in workflow')
            raise NodeConnectionError(f"Node '{node.name}' already added to workflow.")
        conflicts = set(node.get_output_keys()) & set(self._key_map.keys())
        if conflicts:
            self.logger.error(f'Output key conflicts: {conflicts}')
            raise NodeConnectionError(f"Output key(s) already produced: {conflicts}")
        self.nodes.append(node)
        self.connections[node] = []
        for key in node.get_output_keys():
            self._key_map[key] = node
        return self

    def connect(self, from_node: BaseNode, to_node: BaseNode) -> 'Workflow':
        self.logger.debug(f'Connecting {from_node.name} -> {to_node.name} in workflow {self.name}')
        if from_node not in self.nodes or to_node not in self.nodes:
            self.logger.error('Both nodes must be added before connecting')
            raise NodeConnectionError("Both nodes must be added before connecting.")
        try:
            to_node.validate_connection(from_node)
        except Exception as exc:
            self.logger.error(f'Connection validation failed: {exc}')
            raise NodeConnectionError(str(exc))
        self.connections[from_node].append(to_node)
        return self

    def _topological_sort(self) -> List[BaseNode]:
        in_degree: Dict[BaseNode, int] = {node: 0 for node in self.nodes}
        for src, dests in self.connections.items():
            for dst in dests:
                in_degree[dst] += 1
        queue = [n for n, deg in in_degree.items() if deg == 0]
        ordered: List[BaseNode] = []
        while queue:
            n = queue.pop(0)
            ordered.append(n)
            for m in self.connections.get(n, []):
                in_degree[m] -= 1
                if in_degree[m] == 0:
                    queue.append(m)
        if len(ordered) != len(self.nodes):
            self.logger.error('Cycle detected in workflow')
            raise NodeConnectionError('Cycle detected in the workflow.')
        return ordered
    
    def pretty_print(self) -> None:
        """
        Display the workflow structure as an ASCII tree.
        Example:
            node1
            ├── node2
            │   └── node4
            └── node3
        """
        # Identify root nodes: nodes without any parent
        all_nodes = set(self.connections.keys()) | {dst for v in self.connections.values() for dst in v}
        children = {dst for v in self.connections.values() for dst in v}
        roots = [node for node in all_nodes if node not in children]

        def _rec(node: BaseNode, prefix: str, visited: Set[BaseNode], is_last: bool) -> None:
            # Avoid cycles
            if node in visited:
                print(prefix + ("└── " if is_last else "├── ") + f"{node.name} (cycle)")
                return
            visited.add(node)

            # Print current node
            branch = "└── " if is_last else "├── "
            print(prefix + branch + node.name)

            # Prepare prefix for children
            child_nodes = self.connections.get(node, [])
            if not child_nodes:
                return
            new_prefix = prefix + ("    " if is_last else "│   ")

            # Iterate over children
            for index, child in enumerate(child_nodes):
                last_child = index == len(child_nodes) - 1
                _rec(child, new_prefix, visited.copy(), last_child)

        # Print each root and its subtree
        for index, root in enumerate(roots):
            last_root = index == len(roots) - 1
            # Print root name without prefix
            print(root.name)
            for c_idx, child in enumerate(self.connections.get(root, [])):
                _rec(child, '', set([root]), c_idx == len(self.connections[root]) - 1)
                
    def run(self, initial_inputs: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f'Starting workflow {self.name} with initial inputs: {initial_inputs}')
        results: Dict[str, Any] = {}
        results.update(initial_inputs)
        for node in self._topological_sort():
            self.logger.debug(f'Running node {node.name}')
            node_inputs: Dict[str, Any] = {}
            for key in node.get_input_keys():
                if key in results:
                    node_inputs[key] = results[key]
            out = node.run(node_inputs)
            results.update(out)
        self.logger.info(f'Workflow {self.name} completed with results: {results}')
        return results
