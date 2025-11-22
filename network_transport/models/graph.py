from typing import Dict, List, Optional, Tuple
from .node import Node, NodeType
from .edge import Edge, EPSILON


class Graph:
    """Transport network graph managing nodes and edges."""
    
    def __init__(self) -> None:
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[Tuple[str, str], Edge] = {}
    
    def add_node(
        self, 
        node_id: str, 
        balance: float = 0.0
    ) -> Node:
        if node_id in self.nodes:
            raise ValueError(f"Node with ID '{node_id}' already exists")
        
        node = Node(node_id, balance)
        self.nodes[node_id] = node
        return node
    
    def add_edge(
        self,
        from_node: str,
        to_node: str,
        cost: float,
        capacity: float = float('inf')
    ) -> Edge:
        if from_node not in self.nodes:
            raise ValueError(f"Node '{from_node}' does not exist")
        if to_node not in self.nodes:
            raise ValueError(f"Node '{to_node}' does not exist")
        
        edge_id = (from_node, to_node)
        if edge_id in self.edges:
            raise ValueError(f"Edge {from_node}->{to_node} already exists")
        
        edge = Edge(from_node, to_node, cost, capacity)
        self.edges[edge_id] = edge
        return edge
    
    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)
    
    def get_edge(self, from_node: str, to_node: str) -> Optional[Edge]:
        return self.edges.get((from_node, to_node))
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        return [node for node in self.nodes.values() if node.node_type == node_type]
    
    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        return [edge for edge in self.edges.values() if edge.from_node == node_id]
    
    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        return [edge for edge in self.edges.values() if edge.to_node == node_id]
    
    def get_adjacent_edges(self, node_id: str) -> List[Edge]:
        return self.get_outgoing_edges(node_id) + self.get_incoming_edges(node_id)
    
    def check_balance_feasibility(self) -> bool:
        total_balance = sum(node.balance for node in self.nodes.values())
        return abs(total_balance) < EPSILON
    
    def __len__(self) -> int:
        return len(self.nodes)
    
    def __repr__(self) -> str:
        if len(self.nodes) > 20 or len(self.edges) > 50:
             return f"<Graph: {len(self.nodes)} nodes, {len(self.edges)} edges>"
        
        nodes_repr = ", ".join(
            f"{node_id}: Node(balance={node.balance}, type={node.node_type.value})"
            for node_id, node in self.nodes.items()
        )

        edges_repr = ", ".join(
            f"({edge.from_node}->{edge.to_node}): Edge(cost={edge.cost}, capacity={edge.capacity})"
            for edge in self.edges.values()
        )

        return f"Graph(nodes={{{nodes_repr}}}, edges={{{edges_repr}}})"
    
    def __str__(self) -> str:
        nodes_str = ", ".join(self.nodes.keys())
        return f"Graph with nodes: [{nodes_str}]"
