from typing import Set, Tuple, List, Dict

from ...models.graph import Graph
from ...models.edge import Edge
from .base import CycleFindingStrategy, CycleEdge


class CycleFinder(CycleFindingStrategy):
    """Finds improvement cycle in basis tree when entering variable is added."""
    
    def execute(
        self,
        graph: Graph,
        basis_edges: Set[Tuple[str, str]],
        entering_edge: Tuple[str, str],
        direction: str,
        flows: Dict[Tuple[str, str], float]
    ) -> List[CycleEdge]:
        """Find cycle formed by adding entering edge to basis tree."""
        adjacency = self._build_adjacency(graph, basis_edges)
        tree_path = self._find_tree_path(adjacency, entering_edge)
        cycle = self._construct_cycle(graph, entering_edge, tree_path, direction, flows)
        
        return cycle
    
    def _build_adjacency(
        self,
        graph: Graph,
        basis_edges: Set[Tuple[str, str]]
    ) -> Dict[str, List[Tuple[str, Edge, bool]]]:
        """Build undirected adjacency list from basis tree."""
        adjacency: Dict[str, List[Tuple[str, Edge, bool]]] = {node_id: [] for node_id in graph.nodes.keys()}
        
        for edge_id in basis_edges:
            edge = graph.get_edge(*edge_id)
            assert edge is not None

            adjacency[edge.from_node].append((edge.to_node, edge, True))
            adjacency[edge.to_node].append((edge.from_node, edge, False))
        
        return adjacency

    def _find_tree_path(
        self,
        adjacency: Dict[str, List[Tuple[str, Edge, bool]]],
        entering_edge: Tuple[str, str]
    ) -> List[Tuple[Edge, bool]]:
        """Find path in tree containig a cycle."""
        from_node, to_node = entering_edge
        path: List[Tuple[Edge, bool]] = []
        visited: Set[str] = set()
        
        self._dfs_search(to_node, from_node, adjacency, visited, path)
        return path
    
    def _dfs_search(
        self,
        current: str,
        target: str,
        adjacency: Dict[str, List[Tuple[str, Edge, bool]]],
        visited: Set[str],
        path: List[Tuple[Edge, bool]]
    ) -> bool:
        """Recursive DFS to find path from current to target."""
        if current == target:
            return True
        
        visited.add(current)
        
        for neighbor, edge, is_forward in adjacency[current]:
            if neighbor not in visited:
                path.append((edge, is_forward))
                if self._dfs_search(neighbor, target, adjacency, visited, path):
                    return True
                path.pop()
        
        return False
    
    def _construct_cycle(
        self,
        graph: Graph,
        entering_edge_id: Tuple[str, str],
        tree_path: List[Tuple[Edge, bool]],
        direction: str,
        flows: Dict[Tuple[str, str], float]
    ) -> List[CycleEdge]:
        """Construct cycle with signs and flow limits."""
        cycle: List[CycleEdge] = []
        
        entering_edge = graph.get_edge(*entering_edge_id)
        assert entering_edge is not None

        cycle.append(self._create_entering_cycle_edge(entering_edge, direction, flows))
        
        for edge, is_forward in tree_path:
            cycle.append(self._create_tree_cycle_edge(edge, is_forward, direction, flows))
        
        return cycle
    
    def _create_entering_cycle_edge(
        self, 
        edge: Edge, 
        direction: str,
        flows: Dict[Tuple[str, str], float]
    ) -> CycleEdge:
        """Create cycle edge for entering variable."""
        sign, limit = self._get_sign_and_limit(edge, "entering", direction, flows)
        return CycleEdge(edge=edge, sign=sign, theta_limit=limit)
    
    def _create_tree_cycle_edge(
        self,
        edge: Edge,
        is_forward: bool,
        direction: str,
        flows: Dict[Tuple[str, str], float]
    ) -> CycleEdge:
        """Create cycle edge for tree path edge."""
        edge_type = "forward" if is_forward else "backward"
        sign, limit = self._get_sign_and_limit(edge, edge_type, direction, flows)
        return CycleEdge(edge=edge, sign=sign, theta_limit=limit)

    def _get_sign_and_limit(
        self,
        edge: Edge,
        edge_type: str,
        direction: str,
        flows: Dict[Tuple[str, str], float]
    ) -> Tuple[str, float]:
        """Get sign and theta limit for edge in cycle."""
        flow = flows.get(edge.edge_id, 0.0)
        
        if direction == "increase":
            if edge_type == "entering" or edge_type == "forward":
                return "+", edge.capacity - flow
            else:  # backward
                return "-", flow
        else:  # decrease
            if edge_type == "entering" or edge_type == "forward":
                return "-", flow
            else:  # backward
                return "+", edge.capacity - flow
