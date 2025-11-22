import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, Tuple

from network_transport.solver.utils import SolutionState

from ..models.graph import Graph
from .layout_context import LayoutContext
from .styles import VisualStyle
from .renderers import LegendRenderer, SidebarRenderer



class GraphVisualizer:
    """Facade for graph visualization with complete encapsulation of matplotlib internals."""
    
    def __init__(
        self, 
        graph: Graph, 
        layout_context: LayoutContext,
        style: Optional[VisualStyle] = None
    ):
        """
        Initialize visualizer.
        
        Args:
            graph: Network graph with domain model
            layout_context: UI layer state (positions, visual properties)
            style: Optional visual style configuration
        """
        self.graph = graph
        self.layout = layout_context
        self.style = style if style is not None else VisualStyle()
        
        # Matplotlib components (private, encapsulated)
        self._fig = None
        self._ax_main = None
        self._ax_legend = None
        self._ax_sidebar = None
        
        # Renderers (created on demand)
        self._node_renderer = None
        self._edge_renderer = None
        self._supply_demand_renderer = None
        self._legend_renderer = None
        self._sidebar_renderer = None
        
        # Interaction state
        self._interaction_handler = None
        self._interactive_mode = False
        
        # Current solution state (for ViewModels)
        self._current_state: Optional[SolutionState] = None
    
    def set_window_title(self, title: str) -> None:
        """
        Set window title.
        
        Args:
            title: Window title text
        """
        if self._fig and self._fig.canvas and self._fig.canvas.manager:
            try:
                self._fig.canvas.manager.set_window_title(title)
            except:
                pass
    
    def start_interaction(self) -> None:
        """
        Start interactive matplotlib display.
        """
        if self._fig:
            plt.show()
    
    def close(self) -> None:
        """Close the visualization window."""
        if self._fig:
            plt.close(self._fig)
    
    def is_ready(self) -> bool:
        """Check if visualization is ready to be shown."""
        return self._fig is not None
    
    def setup_interactive_layout(self, done_callback=None) -> None:
        """
        Interactive mode for positioning nodes and edge labels.
        User can drag elements to desired positions.
        
        Args:
            done_callback: Optional callback to call when layout is finalized
        """
        if self.layout.is_layout_fixed():
            print("[WARNING] Layout is already fixed. Call layout.unfix_layout() to edit again.")
            return
        
        self._prepare_interactive_mode()
        self._print_setup_instructions()
        self._render()
        self._connect_interaction_handlers()
        
        # Add "Done" button if callback provided
        if done_callback:
            self._add_done_button(done_callback)
        
        self.set_window_title('Interactive Graph Setup - Drag nodes and labels')
    
    def render(self, save_path: Optional[str] = None) -> None:
        """
        Render the graph visualization.
        
        Args:
            save_path: Optional path to save figure
        """
        self._ensure_layout_ready()
        self._render()
        if save_path:
            self._save_figure(save_path)
    
    def apply_solution_state(self, state: Optional[SolutionState]) -> None:
        """
        Apply a solution state to the visualization.
        
        Updates the current state and triggers a redraw to reflect changes.
        
        Args:
            state: Solution state from solver, or None to reset to initial state
        """
        self._current_state = state
        self._trigger_redraw()
    
    def redraw(self) -> None:
        """Force a complete redraw of the visualization."""
        if self._fig:
            self._quick_redraw()
    
    # === Private Implementation ===
    
    def _prepare_interactive_mode(self) -> None:
        """Prepare for interactive layout editing."""
        self._initialize_default_positions()
        self._interactive_mode = True
    
    def _finalize_interactive_mode(self, keep_window_open: bool = False) -> None:
        """
        Finalize interactive layout editing.
        
        Args:
            keep_window_open: If True, don't close the window (for seamless transition)
        """
        self._interactive_mode = False
        self.layout.fix_layout()
        
        # Remove Done button if exists
        if self._done_button and self._done_button.ax:
            self._done_button.ax.remove()
            self._done_button = None
        
        if not keep_window_open:
            if self._fig is not None:
                plt.close(self._fig)
                self._fig = None
        
        print("[OK] Layout saved and fixed!")
    
    def _print_setup_instructions(self) -> None:
        """Print instructions for interactive setup."""
        print("[SETUP] Interactive Setup Mode")
        print("=" * 50)
        print("• Drag nodes to reposition them")
        print("• Drag edge labels to reposition them")
        print("• Click 'Done' button when ready")
        print("=" * 50)
    
    def _add_done_button(self, callback) -> None:
        """Add 'Done' button to finalize layout setup."""
        from matplotlib.widgets import Button
        
        if not self._fig:
            return
        
        # Create button at bottom center
        ax_done = plt.axes([0.45, 0.02, 0.1, 0.04])
        self._done_button = Button(ax_done, 'Done', color='lightgreen', hovercolor='green')
        self._done_button.on_clicked(callback)
    
    def _initialize_default_positions(self) -> None:
        """Create default circular layout if positions not set."""
        if len(self.graph.nodes) == 0:
            return
        
        # Only set positions for nodes that don't have them
        nodes_without_positions = [
            (i, node) for i, node in enumerate(self.graph.nodes.values())
            if not self.layout.has_position(node.id)
        ]
        
        if not nodes_without_positions:
            return
        
        radius = 5.0
        for i, node in nodes_without_positions:
            angle = 2 * np.pi * i / len(self.graph.nodes)
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            self.layout.set_node_position(node.id, x, y)
    
    def _ensure_layout_ready(self) -> None:
        """Ensure layout is ready for rendering."""
        if not self.layout.is_layout_fixed():
            print("[WARNING] Layout is not fixed. Run setup_interactive_layout() first.")
            self._initialize_default_positions()
    
    def _render(self) -> None:
        """Main rendering pipeline."""
        self._create_figure()
        self._create_axes()
        self._configure_axes()
        self._create_renderers_with_layout()
        self._draw_all_elements()
        self._auto_scale()
        self._set_background_color()
    
    def _create_figure(self) -> None:
        """Create matplotlib figure."""
        if self._fig is not None:
            plt.close(self._fig)
        
        self._fig = plt.figure(
            figsize=(self.style.layout.figure_width, self.style.layout.figure_height)
        )
    
    def _create_axes(self) -> None:
        """Create all axes for the visualization."""
        # Main graph axis
        self._ax_main = self._fig.add_axes([
            0.05, 0.05, self.style.layout.graph_width_ratio, 0.9
        ])
        
        # Legend axis
        x_offset = 0.05 + self.style.layout.graph_width_ratio + 0.02
        self._ax_legend = self._fig.add_axes([
            x_offset, 0.55, self.style.layout.sidebar_width_ratio, 0.4
        ])
        
        # Sidebar axis
        self._ax_sidebar = self._fig.add_axes([
            x_offset, 0.05, self.style.layout.sidebar_width_ratio, 0.45
        ])
    
    def _configure_axes(self) -> None:
        """Configure axis properties."""
        self._ax_main.set_aspect('equal')
        self._ax_main.axis('off')
        
        # Configure legend axis with background
        self._ax_legend.axis('off')
        self._ax_legend.set_facecolor('#F5F5F5')
        
        # Configure sidebar axis with background
        self._ax_sidebar.axis('off')
        self._ax_sidebar.set_facecolor('#F5F5F5')
    
    def _create_renderers_with_layout(self) -> None:
        """Create renderers adapted to use LayoutContext."""
        from .rendering_adapters import (
            LayoutAwareNodeRenderer,
            LayoutAwareEdgeRenderer,
            LayoutAwareSupplyDemandRenderer
        )
        
        self._node_renderer = LayoutAwareNodeRenderer(
            self._ax_main, self.graph, self.layout, self.style
        )
        self._edge_renderer = LayoutAwareEdgeRenderer(
            self._ax_main, self.graph, self.layout, self.style
        )
        self._supply_demand_renderer = LayoutAwareSupplyDemandRenderer(
            self._ax_main, self.graph, self.layout, self.style
        )
        self._legend_renderer = LegendRenderer(self._ax_legend, self.style)
        self._sidebar_renderer = SidebarRenderer(self._ax_sidebar, self.graph)
        
        # Interaction handler
        from .interaction_handler import LayoutAwareInteractionHandler
        self._interaction_handler = LayoutAwareInteractionHandler(
            self.graph, self.layout, self._node_renderer, self._edge_renderer
        )
    
    def _draw_all_elements(self) -> None:
        """
        Draw all visual elements.
        
        Creates node and edge view models to provide unified access
        to both static problem data and dynamic solution state.
        """
        from .view_models import NodeViewModel, EdgeViewModel
        
        # Create ViewModels wrapping models with current state
        node_vms = {
            node_id: NodeViewModel(node, self._current_state)
            for node_id, node in self.graph.nodes.items()
        }
        
        edge_vms = {
            edge_id: EdgeViewModel(edge, self._current_state)
            for edge_id, edge in self.graph.edges.items()
        }
        
        # Pass ViewModels to renderers
        self._supply_demand_renderer.draw_supply_demand_arrows()
        self._edge_renderer.draw_all_edges(edge_vms)
        self._node_renderer.draw_all_nodes(node_vms)
        self._legend_renderer.draw_legend()
        self._sidebar_renderer.draw_sidebar(self._current_state)
    
    def _set_background_color(self) -> None:
        """Set figure background color."""
        self._fig.patch.set_facecolor(self.style.layout.background_color)
    
    def _auto_scale(self) -> None:
        """Automatically scale axes to fit content."""
        positions = [
            self.layout.get_node_position(node.id)
            for node in self.graph.nodes.values()
            if self.layout.has_position(node.id)
        ]
        
        if not positions:
            return
        
        xs = [pos[0] for pos in positions]
        ys = [pos[1] for pos in positions]
        
        padding = 2.0 if self._interactive_mode else self.style.layout.padding
        extra = self.style.supply_demand.arrow_length + 1.0
        
        x_min, x_max = min(xs) - padding, max(xs) + padding
        y_min, y_max = min(ys) - padding - extra, max(ys) + padding + extra
        
        # Ensure minimum size
        x_min, x_max = self._ensure_minimum_range(x_min, x_max, 10)
        y_min, y_max = self._ensure_minimum_range(y_min, y_max, 10)
        
        self._ax_main.set_xlim(x_min, x_max)
        self._ax_main.set_ylim(y_min, y_max)
    
    def _ensure_minimum_range(
        self, min_val: float, max_val: float, min_size: float
    ) -> Tuple[float, float]:
        """Ensure axis range is at least min_size."""
        if max_val - min_val < min_size:
            center = (min_val + max_val) / 2
            return (center - min_size / 2, center + min_size / 2)
        return (min_val, max_val)
    
    def _connect_interaction_handlers(self) -> None:
        """Connect mouse event handlers for interaction."""
        self._fig.canvas.mpl_connect('button_press_event', self._on_press)
        self._fig.canvas.mpl_connect('button_release_event', self._on_release)
        self._fig.canvas.mpl_connect('motion_notify_event', self._on_motion)
    
    def _on_press(self, event) -> None:
        """Handle mouse press event."""
        if self._interactive_mode:
            self._interaction_handler.handle_press(event, self._ax_main)
    
    def _on_release(self, event) -> None:
        """Handle mouse release event."""
        if self._interactive_mode:
            self._interaction_handler.handle_release(event)
    
    def _on_motion(self, event) -> None:
        """Handle mouse motion event."""
        if self._interactive_mode:
            if self._interaction_handler.handle_motion(event, self._ax_main):
                self._quick_redraw()
    
    def _quick_redraw(self, preserve_limits: bool = True) -> None:
        """
        Quickly redraw graph elements without recreating figure.
        
        Args:
            preserve_limits: If True, preserve existing axis limits. If False, recalculate.
        """
        if not self._fig:
            return
        
        from .view_models import NodeViewModel, EdgeViewModel
        
        # Save axis limits if needed
        if preserve_limits:
            xlim = self._ax_main.get_xlim()
            ylim = self._ax_main.get_ylim()
        
        # Clear and redraw
        self._ax_main.clear()
        self._ax_main.set_aspect('equal')
        self._ax_main.axis('off')
        
        # Create ViewModels
        node_vms = {
            node_id: NodeViewModel(node, self._current_state)
            for node_id, node in self.graph.nodes.items()
        }
        
        edge_vms = {
            edge_id: EdgeViewModel(edge, self._current_state)
            for edge_id, edge in self.graph.edges.items()
        }
        
        self._supply_demand_renderer.draw_supply_demand_arrows()
        self._edge_renderer.draw_all_edges(edge_vms)
        self._node_renderer.draw_all_nodes(node_vms)
        
        # Restore or recalculate axis limits
        if preserve_limits:
            self._ax_main.set_xlim(xlim)
            self._ax_main.set_ylim(ylim)
        else:
            self._auto_scale()
        
        # Redraw sidebar and legend
        self._legend_renderer.draw_legend()
        self._sidebar_renderer.draw_sidebar(self._current_state)
        
        self._fig.canvas.draw_idle()
    
    def _trigger_redraw(self) -> None:
        """Trigger a redraw if figure exists."""
        if self._fig is not None:
            self._quick_redraw()
    

    
    def _save_figure(self, path: str) -> None:
        """Save figure to file."""
        if self._fig:
            plt.savefig(path, dpi=300, bbox_inches='tight')
            print(f"[SAVED] Saved to {path}")
