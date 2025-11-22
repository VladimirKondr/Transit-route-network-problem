from typing import Optional
from matplotlib.axes import Axes
import matplotlib.patches as mpatches

from network_transport.models.graph import Graph
from network_transport.solver.utils import SolutionState


class SidebarRenderer:
    """Renders problem statistics sidebar."""
    
    def __init__(self, ax: Axes, graph: Graph):
        self.ax = ax
        self.graph: Graph = graph
        self.state = None
    
    def draw_sidebar(self, state: Optional[SolutionState]=None) -> None:
        self.state = state
        
        num_nodes = len(self.graph.nodes)
        num_edges = len(self.graph.edges)
        
        supply = sum(n.balance for n in self.graph.nodes.values() if n.balance > 0)
        demand = -sum(n.balance for n in self.graph.nodes.values() if n.balance < 0)
        
        objective = self._calculate_objective()
        
        info_text = (
            f"Problem Size:\n"
            f"  Nodes: {num_nodes}\n"
            f"  Edges: {num_edges}\n\n"
            f"Balance:\n"
            f"  Supply: {supply:.0f}\n"
            f"  Demand: {demand:.0f}\n\n"
            f"Objective: {objective:.2f}"
        )

        self.ax.clear()
        self.ax.axis('off')
        
        # Draw background rectangle
        bg_rect = mpatches.Rectangle((0, 0), 1, 1, 
                                     facecolor='#F5F5F5',
                                     edgecolor='#CCCCCC',
                                     linewidth=1,
                                     transform=self.ax.transAxes,
                                     zorder=0)
        self.ax.add_patch(bg_rect)
        
        self.ax.text( # pyright: ignore[reportUnknownMemberType]
            0.5, 0.5,
            info_text,
            ha='center', va='center', fontsize=9, family='monospace'
        )
    
    def _calculate_objective(self) -> float:
        if self.state is None:
            return 0.0
        return self.state.objective_value