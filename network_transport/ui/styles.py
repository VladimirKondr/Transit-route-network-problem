from abc import ABC
from dataclasses import dataclass
from typing import Dict

@dataclass
class BaseStyle(ABC):
    pass


@dataclass
class NodeStyle(BaseStyle):
    """Node visual properties."""
    radius: float = 0.5
    border_color: str = 'black'
    border_width: float = 2.0
    label_font_size: int = 10
    label_font_weight: str = 'bold'
    label_color: str = 'black'
    potential_font_size: int = 8
    potential_color: str = 'darkblue'
    potential_label_offset: float = 0.8


@dataclass
class EdgeStyle(BaseStyle):
    """Edge visual properties."""
    label_font_size: int = 8
    basis_linewidth: float = 2.5
    non_basis_linewidth: float = 1.5
    basis_color: str = 'black'
    non_basis_color: str = 'gray'
    violation_color: str = 'red'


@dataclass
class SupplyDemandStyle(BaseStyle):
    """Supply/demand arrow properties."""
    arrow_length: float = 1.5
    arrow_head_width: float = 0.3
    arrow_head_length: float = 0.2
    arrow_line_width: float = 2.0
    supply_color: str = 'green'
    demand_color: str = 'red'
    label_font_size: int = 9


@dataclass
class LayoutStyle(BaseStyle):
    """Layout configuration."""
    figure_width: float = 16
    figure_height: float = 10
    graph_width_ratio: float = 0.68
    sidebar_width_ratio: float = 0.22
    padding: float = 2.5
    background_color: str = 'white'


class VisualStyle(BaseStyle):
    """Complete visual style configuration."""
    
    def __init__(self):
        self.node = NodeStyle()
        self.edge = EdgeStyle()
        self.supply_demand = SupplyDemandStyle()
        self.layout = LayoutStyle()
        
        # Node type colors
        self._node_colors: Dict[str, str] = {
            'source': 'lightgreen',
            'sink': 'lightcoral',
            'transit': 'lightblue'
        }
    
    def get_node_color(self, node_type: str) -> str:
        """Get color for node type."""
        return self._node_colors.get(node_type, 'lightgray')
    
    def get_edge_style_params(self, is_basis: bool, violates_optimality: bool) -> Dict[str, any]:
        """Get matplotlib style parameters for edge."""
        if violates_optimality:
            return {
                'arrowstyle': '->',
                'color': self.edge.violation_color,
                'linewidth': self.edge.basis_linewidth,
                'linestyle': 'solid',
                'mutation_scale': 20
            }
        elif is_basis:
            return {
                'arrowstyle': '->',
                'color': self.edge.basis_color,
                'linewidth': self.edge.basis_linewidth,
                'linestyle': 'solid',
                'mutation_scale': 20
            }
        else:
            return {
                'arrowstyle': '->',
                'color': self.edge.non_basis_color,
                'linewidth': self.edge.non_basis_linewidth,
                'linestyle': 'dashed',
                'mutation_scale': 15
            }
