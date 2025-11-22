from dataclasses import dataclass

EPSILON = 1e-9


@dataclass(frozen=True, slots=True)
class Edge:
    """Transport network edge with cost and capacity."""
    
    from_node: str
    to_node: str
    cost: float
    capacity: float = float('inf')
    
    @property
    def edge_id(self) -> tuple[str, str]:
        return (self.from_node, self.to_node)
    
    def __str__(self) -> str:
        cap_str = f"{self.capacity:.0f}" if self.capacity != float('inf') else "∞"
        return f"{self.from_node}→{self.to_node}: c={self.cost}, cap={cap_str}"
