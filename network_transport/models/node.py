from dataclasses import dataclass
from enum import Enum


class NodeType(Enum):
    SOURCE = "source"
    SINK = "sink"
    TRANSIT = "transit"


@dataclass(frozen=True, slots=True)
class Node:
    """Transport network node with supply or demand."""
    
    id: str
    balance: float = 0.0
    
    @property
    def node_type(self) -> NodeType:
        if self.balance > 0:
            return NodeType.SOURCE
        elif self.balance < 0:
            return NodeType.SINK
        return NodeType.TRANSIT
    
    def __str__(self) -> str:
        return f"Node {self.id} [{self.node_type.value}]: b={self.balance}"
