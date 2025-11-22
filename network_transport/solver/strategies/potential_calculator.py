from typing import Dict, Set
from collections import deque

from ...models.graph import Graph
from .base import PotentialCalculationStrategy


class PotentialCalculator(PotentialCalculationStrategy):
    def execute(self, graph: Graph, basis_edges: Set[tuple[str, str]]) -> Dict[str, float]:
        """Calculate node potentials using BFS traversal of basis tree. """
        potentials: Dict[str, float] = {}
        root = next(iter(graph.nodes.keys()))
        potentials[root] = 0.0
        
        self._traverse_basis_tree(graph, basis_edges, root, potentials)
        
        return potentials
    
    def _traverse_basis_tree(
        self,
        graph: Graph,
        basis_edges: Set[tuple[str, str]],
        root: str,
        potentials: Dict[str, float]
    ) -> None:
        visited = {root}
        queue = deque([root])
        
        while queue:
            current = queue.popleft()
            current_potential = potentials[current]
            
            for edge_id in basis_edges:
                edge = graph.get_edge(*edge_id)
                assert edge is not None
                
                if edge.from_node == current and edge.to_node not in visited:
                    potentials[edge.to_node] = current_potential + edge.cost
                    visited.add(edge.to_node)
                    queue.append(edge.to_node)
                
                elif edge.to_node == current and edge.from_node not in visited:
                    potentials[edge.from_node] = current_potential - edge.cost
                    visited.add(edge.from_node)
                    queue.append(edge.from_node)
