from typing import Optional, List
from matplotlib.axes import Axes
import matplotlib.patches as mpatches

from network_transport.models.graph import Graph
from network_transport.solver.utils import SolutionState


class SidebarRenderer:
    """Renders problem statistics sidebar with optional console log."""
    
    def __init__(self, ax: Axes, graph: Graph):
        self.ax = ax
        self.graph: Graph = graph
        self.state = None
        self.current_step_log: str = ""
        self.show_console_log = True
        self.max_line_width = 50  # Max characters per line for wrapping
    
    def add_console_message(self, message: str) -> None:
        """Set current step log (replaces previous)."""
        self.current_step_log = message
    
    def clear_console_log(self) -> None:
        """Clear console log."""
        self.current_step_log = ""
    
    def set_show_console_log(self, show: bool) -> None:
        """Toggle console log visibility."""
        self.show_console_log = show
    
    def _calculate_adaptive_fontsize(self) -> float:
        """Calculate adaptive font size based on sidebar dimensions."""
        try:
            # Get figure and axes dimensions
            fig = self.ax.get_figure()
            if fig is None:
                return 8.0  # Default size
            
            # Get figure size in inches
            fig_width, fig_height = fig.get_size_inches()
            
            # Get axes position relative to figure (left, bottom, width, height)
            pos = self.ax.get_position()
            sidebar_width_inch = pos.width * fig_width
            sidebar_height_inch = pos.height * fig_height
            
            # Calculate font size based on dimensions
            # Base formula: font size proportional to sidebar area
            # Typical sidebar: 2-3 inches wide, 6-8 inches tall
            base_size = (sidebar_width_inch * 3.0 + sidebar_height_inch * 0.9) / 2
            
            # Clamp between reasonable values
            return max(6.0, min(base_size, 11.0))
        except Exception:
            # Fallback to default if anything goes wrong
            return 8.0
    
    def _calculate_adaptive_line_width(self) -> int:
        """Calculate adaptive line width based on font size."""
        fontsize = self._calculate_adaptive_fontsize()
        # Smaller font = more characters fit
        # Formula: inversely proportional to font size
        line_width = int(400 / fontsize)
        return max(40, min(line_width, 60))
    
    def _wrap_text(self, text: str, max_width: int) -> str:
        """Wrap text to fit within max width."""
        lines = text.split('\n')
        wrapped_lines = []
        
        for line in lines:
            if len(line) <= max_width:
                wrapped_lines.append(line)
            else:
                # Wrap long lines
                while len(line) > max_width:
                    # Find last space before max_width
                    wrap_pos = line.rfind(' ', 0, max_width)
                    if wrap_pos == -1:
                        # No space found, hard break
                        wrap_pos = max_width
                    
                    wrapped_lines.append(line[:wrap_pos])
                    line = line[wrap_pos:].lstrip()
                
                if line:
                    wrapped_lines.append(line)
        
        return '\n'.join(wrapped_lines)
    
    def draw_sidebar(self, state: Optional[SolutionState]=None) -> None:
        self.state = state
        
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
        
        if self.show_console_log and self.current_step_log:
            # Calculate adaptive font size and line width
            fontsize = self._calculate_adaptive_fontsize()
            line_width = self._calculate_adaptive_line_width()
            
            # Show console log with text wrapping
            wrapped_text = self._wrap_text(self.current_step_log, line_width)
            self.ax.text( # pyright: ignore[reportUnknownMemberType]
                0.02, 0.98,
                wrapped_text,
                ha='left', va='top', fontsize=fontsize, family='monospace',
                transform=self.ax.transAxes
            )
        else:
            # Show problem statistics
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
            
            self.ax.text( # pyright: ignore[reportUnknownMemberType]
                0.5, 0.5,
                info_text,
                ha='center', va='center', fontsize=9, family='monospace'
            )
    
    def _calculate_objective(self) -> float:
        if self.state is None:
            return 0.0
        return self.state.objective_value