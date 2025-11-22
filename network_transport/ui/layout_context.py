from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class EdgeVisualData:
    """Visual properties for edge rendering."""
    label_position: float = 0.5  # Position along edge (0.0 to 1.0)
    label_offset: float = 0.15   # Perpendicular offset from edge
    
    def update_label_position(self, position: float, offset: float) -> None:
        """Update label positioning parameters."""
        self.label_position = max(0.0, min(1.0, position))
        self.label_offset = offset


class LayoutContext:
    """View-model that stores all visual/layout state for the graph."""
    
    def __init__(self) -> None:
        # Maps node_id -> (x, y) position
        self.node_positions: Dict[str, Tuple[float, float]] = {}
        
        # Maps (from_node, to_node) -> EdgeVisualData
        self.edge_metadata: Dict[Tuple[str, str], EdgeVisualData] = {}
        
        # Layout state
        self._is_fixed: bool = False
    
    def set_node_position(self, node_id: str, x: float, y: float) -> None:
        """Set the visual position of a node."""
        self.node_positions[node_id] = (x, y)
    
    def get_node_position(self, node_id: str) -> Tuple[float, float] | None:
        """Get the visual position of a node, or None if not set."""
        return self.node_positions.get(node_id)
    
    def has_position(self, node_id: str) -> bool:
        """Check if a node has a position set."""
        return node_id in self.node_positions
    
    def set_edge_label_position(self, from_node: str, to_node: str, 
                                position: float, offset: float) -> None:
        """Set the label position for an edge."""
        edge_id = (from_node, to_node)
        if edge_id not in self.edge_metadata:
            self.edge_metadata[edge_id] = EdgeVisualData()
        self.edge_metadata[edge_id].update_label_position(position, offset)
    
    def get_edge_visual_data(self, from_node: str, to_node: str) -> EdgeVisualData | None:
        """
        Get visual data for an edge.
        
        Returns:
            EdgeVisualData if exists, None otherwise
        """
        edge_id = (from_node, to_node)
        return self.edge_metadata.get(edge_id)
    
    def ensure_edge_visual_data(self, from_node: str, to_node: str) -> EdgeVisualData:
        """
        Ensure visual data exists for an edge, creating default if needed.
        
        Returns:
            EdgeVisualData (existing or newly created)
        """
        edge_id = (from_node, to_node)
        if edge_id not in self.edge_metadata:
            self.edge_metadata[edge_id] = EdgeVisualData()
        return self.edge_metadata[edge_id]
    
    def is_layout_fixed(self) -> bool:
        """Check if the layout is locked from editing."""
        return self._is_fixed
    
    def fix_layout(self) -> None:
        """Lock the layout to prevent further editing."""
        self._is_fixed = True
    
    def unfix_layout(self) -> None:
        """Unlock the layout to allow editing."""
        self._is_fixed = False
    
    def has_complete_layout(self, node_ids: list[str]) -> bool:
        """Check if all nodes have positions assigned."""
        return all(node_id in self.node_positions for node_id in node_ids)
    
    def clear(self) -> None:
        """Clear all layout data."""
        self.node_positions.clear()
        self.edge_metadata.clear()
        self._is_fixed = False
