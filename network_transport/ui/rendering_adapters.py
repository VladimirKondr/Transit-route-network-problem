from matplotlib.patches import Circle, FancyArrowPatch
from matplotlib.text import Text
from typing import Dict, Tuple, TYPE_CHECKING
from ..models.node import Node
from ..models.graph import Graph
from .layout_context import LayoutContext
from .styles import VisualStyle
from .geometry import calculate_label_position

if TYPE_CHECKING:
    from .view_models import EdgeViewModel, NodeViewModel


class LayoutAwareNodeRenderer:
    """Renders nodes using positions from LayoutContext."""
    
    def __init__(self, ax, graph: Graph, layout: LayoutContext, style: VisualStyle):
        self.ax = ax
        self.graph = graph
        self.layout = layout
        self.style = style
        self.node_artists: Dict[str, Circle] = {}
        self.node_labels: Dict[str, Text] = {}
        self.potential_labels: Dict[str, Text] = {}
    
    def draw_all_nodes(self, nodes: Dict[str, 'NodeViewModel']) -> None:
        """Draw all nodes using layout context positions."""
        self._clear_artifacts()
        for node in nodes.values():
            pos = self.layout.get_node_position(node.id)
            if pos:
                self._draw_single_node(node, pos)
    
    def _clear_artifacts(self) -> None:
        self.node_artists.clear()
        self.node_labels.clear()
        self.potential_labels.clear()
    
    def _draw_single_node(self, node: 'NodeViewModel', position: Tuple[float, float]) -> None:
        """Draw a single node at given position."""
        self._create_node_circle(node, position)
        self._create_node_label(node, position)
        self._create_potential_label(node, position)
    
    def _create_node_circle(self, node: 'NodeViewModel', position: Tuple[float, float]) -> None:
        """Create node circle patch."""
        x, y = position
        color = self.style.get_node_color(node.node_type.value)
        circle = Circle(
            (x, y), self.style.node.radius,
            facecolor=color, edgecolor=self.style.node.border_color,
            linewidth=self.style.node.border_width, zorder=10, picker=True
        )
        self.ax.add_patch(circle)
        self.node_artists[node.id] = circle
    
    def _create_node_label(self, node: 'NodeViewModel', position: Tuple[float, float]) -> None:
        """Create node label text."""
        x, y = position
        label_text = f"{node.id}\n[{node.balance:+.0f}]"
        label = self.ax.text(
            x, y, label_text,
            ha='center', va='center',
            fontsize=self.style.node.label_font_size,
            fontweight=self.style.node.label_font_weight,
            color=self.style.node.label_color,
            zorder=11
        )
        self.node_labels[node.id] = label
    
    def _create_potential_label(self, node: 'NodeViewModel', position: Tuple[float, float]) -> None:
        """Create potential label text if potential is set."""
        if node.potential is None:
            return
        
        x, y = position
        offset_y = self.style.node.radius + self.style.node.potential_label_offset
        potential_text = f"u={node.potential:.1f}"
        label = self.ax.text(
            x, y + offset_y, potential_text,
            ha='center', va='bottom',
            fontsize=self.style.node.potential_font_size,
            color=self.style.node.potential_color,
            bbox=dict(
                boxstyle='round,pad=0.3',
                facecolor='white',
                edgecolor='gray',
                alpha=0.8
            ),
            zorder=12
        )
        self.potential_labels[node.id] = label


class LayoutAwareEdgeRenderer:
    """Renders edges using positions from LayoutContext."""
    
    def __init__(self, ax, graph: Graph, layout: LayoutContext, style: VisualStyle):
        self.ax = ax
        self.graph = graph
        self.layout = layout
        self.style = style
        self.edge_labels: Dict[Tuple[str, str], Text] = {}
        self.edge_arrows: Dict[Tuple[str, str], FancyArrowPatch] = {}
    
    def draw_all_edges(self, edges: Dict[Tuple[str, str], 'EdgeViewModel']) -> None:
        """Draw all edges using layout context positions."""
        self._clear_artifacts()
        for edge in edges.values():
            if self._has_valid_positions(edge):
                self._draw_single_edge(edge)
    
    def _clear_artifacts(self) -> None:
        self.edge_labels.clear()
        self.edge_arrows.clear()
    
    def _has_valid_positions(self, edge: 'EdgeViewModel') -> bool:
        """Check if both nodes have positions in layout."""
        return (self.layout.has_position(edge.from_node) and 
                self.layout.has_position(edge.to_node))
    
    def _draw_single_edge(self, edge: 'EdgeViewModel') -> None:
        """Draw a single edge."""
        self._create_edge_arrow(edge)
        self._create_edge_label(edge)
    
    def _create_edge_arrow(self, edge: 'EdgeViewModel') -> None:
        """Create edge arrow patch."""
        pos1 = self.layout.get_node_position(edge.from_node)
        pos2 = self.layout.get_node_position(edge.to_node)
        
        style_params = self.style.get_edge_style_params(
            edge.is_basis, edge.violates_optimality()
        )
        
        # Calculate shrink distance to make arrows start/end at node boundaries
        # Using node radius from style and converting to points (approximately)
        node_radius = self.style.node.radius
        # Convert from data coordinates to points (rough approximation)
        shrink_distance = node_radius * 50  # Adjust multiplier as needed
        
        arrow = FancyArrowPatch(
            pos1, pos2,
            arrowstyle=style_params['arrowstyle'],
            color=style_params['color'],
            linewidth=style_params['linewidth'],
            linestyle=style_params['linestyle'],
            mutation_scale=style_params['mutation_scale'],
            shrinkA=shrink_distance,  # Shrink from start node
            shrinkB=shrink_distance,  # Shrink from end node
            zorder=5
        )
        self.ax.add_patch(arrow)
        self.edge_arrows[edge.edge_id] = arrow
    
    def _create_edge_label(self, edge: 'EdgeViewModel') -> None:
        """Create edge label text."""
        pos1 = self.layout.get_node_position(edge.from_node)
        pos2 = self.layout.get_node_position(edge.to_node)
        
        # Ensure visual data exists for this edge
        visual_data = self.layout.ensure_edge_visual_data(edge.from_node, edge.to_node)
        
        # Calculate label position
        label_pos = calculate_label_position(
            pos1, pos2,
            visual_data.label_position,
            visual_data.label_offset
        )
        
        # Build label text
        label_text = self._build_label_text(edge)
        
        # Create text
        label = self.ax.text(
            label_pos[0], label_pos[1], label_text,
            ha='center', va='center',
            fontsize=self.style.edge.label_font_size,
            bbox=dict(
                boxstyle='round,pad=0.3',
                facecolor='white',
                edgecolor='gray',
                alpha=0.9
            ),
            zorder=6,
            picker=True
        )
        self.edge_labels[edge.edge_id] = label
    
    def _build_label_text(self, edge: 'EdgeViewModel') -> str:
        """Build label text for edge."""
        parts = []
        
        # Add cycle sign if this edge is part of a cycle
        if edge.cycle_sign is not None:
            parts.append(f"[{edge.cycle_sign}]")
        
        parts.append(f"x={edge.flow:.0f}")
        parts.append(f"c={edge.cost:.0f}")
        
        if edge.capacity != float('inf'):
            parts.append(f"d={edge.capacity:.0f}")
        
        if edge.delta is not None:
            parts.append(f"Δ={edge.delta:+.1f}")
        
        return "\n".join(parts)


class LayoutAwareSupplyDemandRenderer:
    """Renders supply/demand arrows using positions from LayoutContext."""
    
    def __init__(self, ax, graph: Graph, layout: LayoutContext, style: VisualStyle):
        self.ax = ax
        self.graph = graph
        self.layout = layout
        self.style = style
    
    def draw_supply_demand_arrows(self) -> None:
        """Draw supply and demand arrows for all nodes."""
        for node in self.graph.nodes.values():
            pos = self.layout.get_node_position(node.id)
            if pos and node.balance != 0:
                self._draw_arrow_for_node(node, pos)
    
    def _draw_arrow_for_node(self, node: Node, position: Tuple[float, float]) -> None:
        """Draw supply or demand arrow for a node."""
        x, y = position
        arrow_length = self.style.supply_demand.arrow_length
        
        if node.balance > 0:  # Supply
            # Arrow pointing down into node
            self.ax.arrow(
                x, y + arrow_length, 0, -arrow_length * 0.8,
                head_width=self.style.supply_demand.arrow_head_width,
                head_length=self.style.supply_demand.arrow_head_length,
                fc=self.style.supply_demand.supply_color,
                ec=self.style.supply_demand.supply_color,
                linewidth=self.style.supply_demand.arrow_line_width,
                zorder=4
            )
            # Label
            self.ax.text(
                x, y + arrow_length + 0.3,
                f"+{node.balance:.0f}",
                ha='center', va='bottom',
                fontsize=self.style.supply_demand.label_font_size,
                fontweight='bold',
                color=self.style.supply_demand.supply_color
            )
        
        elif node.balance < 0:  # Demand
            # Arrow pointing down from node
            self.ax.arrow(
                x, y - arrow_length, 0, arrow_length * 0.8,
                head_width=self.style.supply_demand.arrow_head_width,
                head_length=self.style.supply_demand.arrow_head_length,
                fc=self.style.supply_demand.demand_color,
                ec=self.style.supply_demand.demand_color,
                linewidth=self.style.supply_demand.arrow_line_width,
                zorder=4
            )
            # Label
            self.ax.text(
                x, y - arrow_length - 0.3,
                f"{node.balance:.0f}",
                ha='center', va='top',
                fontsize=self.style.supply_demand.label_font_size,
                fontweight='bold',
                color=self.style.supply_demand.demand_color
            )
