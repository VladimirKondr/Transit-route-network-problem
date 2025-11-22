from typing import List, Tuple
import matplotlib.patches as mpatches
from matplotlib.axes import Axes
from ..styles import VisualStyle

class LegendRenderer:
    """Renders legend panel showing node types and edge types."""
    def __init__(self, ax: Axes, style: VisualStyle):
        """
        Initialize legend renderer.
        
        Args:
            ax: Matplotlib axes for legend
            style: VisualStyle configuration
        """
        
        self.ax = ax
        self.style = style
    
    def draw_legend(self) -> None:
        """Draw legend with node and edge type information."""
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
        
        # Title
        self.ax.text(0.5, 0.95, 'Legend', ha='center', va='top',  # type: ignore[call-arg]
                    fontsize=11, fontweight='bold')
        
        # Node types section
        y_pos = 0.80
        self.ax.text(0.1, y_pos, 'Node Types:', ha='left', va='top', # pyright: ignore[reportUnknownMemberType]
                    fontsize=9, fontweight='bold')
        
        # Draw node type circles with colors
        node_types: List[Tuple[str, str]] = [
            ('Source', self.style.get_node_color('source')),
            ('Sink', self.style.get_node_color('sink')),
            ('Transit', self.style.get_node_color('transit'))
        ]
        
        y_pos -= 0.12
        for label, color in node_types:
            # Draw colored circle
            circle = mpatches.Circle((0.15, y_pos), 0.03, 
                                    facecolor=color, 
                                    edgecolor='black', 
                                    linewidth=1.5,
                                    transform=self.ax.transAxes)
            self.ax.add_patch(circle)
            
            # Draw label
            self.ax.text(0.25, y_pos, label, ha='left', va='center', # pyright: ignore[reportUnknownMemberType]
                        fontsize=8, transform=self.ax.transAxes)
            y_pos -= 0.10
        
        # Edge types section
        y_pos -= 0.05
        self.ax.text(0.1, y_pos, 'Edge Types:', ha='left', va='top', # pyright: ignore[reportUnknownMemberType]
                    fontsize=9, fontweight='bold')
        
        # Draw edge type lines
        edge_types = [
            ('Basis', self.style.edge.basis_color, 'solid', 2.5),
            ('Non-basis', self.style.edge.non_basis_color, 'dashed', 1.5),
            ('Violation', self.style.edge.violation_color, 'solid', 2.5)
        ]
        
        y_pos -= 0.10
        for label, color, linestyle, linewidth in edge_types:
            # Draw line
            self.ax.plot([0.12, 0.22], [y_pos, y_pos],  # pyright: ignore[reportUnknownMemberType]
                        color=color, linestyle=linestyle, 
                        linewidth=linewidth, transform=self.ax.transAxes)
            
            # Draw label
            self.ax.text(0.25, y_pos, label, ha='left', va='center', # pyright: ignore[reportUnknownMemberType]
                        fontsize=8, transform=self.ax.transAxes)
            y_pos -= 0.10
