import time
from ..models.graph import Graph
from .layout_context import LayoutContext
from .geometry import project_point_to_edge


class LayoutAwareInteractionHandler:
    """Handles user interactions for layout editing."""
    
    def __init__(
        self,
        graph: Graph,
        layout: LayoutContext,
        node_renderer,
        edge_renderer
    ):
        """
        Initialize interaction handler.
        
        Args:
            graph: Network graph
            layout: Layout context
            node_renderer: Node renderer with artist references
            edge_renderer: Edge renderer with artist references
        """
        self.graph = graph
        self.layout = layout
        self.node_renderer = node_renderer
        self.edge_renderer = edge_renderer
        
        # Interaction state
        self.dragging_node = None
        self.dragging_label = None
        self.press_event = None
        
        # Throttling for performance
        self.last_update_time = 0
        self.update_interval = 0.05
    
    def handle_press(self, event, ax) -> None:
        """
        Handle mouse button press.
        
        Args:
            event: Matplotlib mouse event
            ax: Axes being interacted with
        """
        if event.inaxes != ax:
            return
        
        self._try_select_node(event)
        self._try_select_label(event)
    
    def _try_select_node(self, event) -> None:
        """Try to select a node for dragging."""
        for node_id, circle in self.node_renderer.node_artists.items():
            if self._is_clicked(circle, event):
                self.dragging_node = node_id
                self.press_event = event
                return
    
    def _try_select_label(self, event) -> None:
        """Try to select an edge label for dragging."""
        for edge_id, text in self.edge_renderer.edge_labels.items():
            if self._is_clicked(text, event):
                self.dragging_label = edge_id
                self.press_event = event
                return
    
    def _is_clicked(self, artist, event) -> bool:
        """Check if an artist was clicked."""
        contains, _ = artist.contains(event)
        return contains
    
    def handle_release(self, event) -> None:
        """
        Handle mouse button release.
        
        Args:
            event: Matplotlib mouse event
        """
        self.dragging_node = None
        self.dragging_label = None
        self.press_event = None
    
    def handle_motion(self, event, ax) -> bool:
        """
        Handle mouse motion.
        
        Args:
            event: Matplotlib mouse event
            ax: Axes being interacted with
        
        Returns:
            True if redraw is needed, False otherwise
        """
        if not self._should_process_motion(event, ax):
            return False
        
        if not self._check_throttling():
            return False
        
        if self.dragging_node:
            self._handle_node_drag(event)
            return True
        
        if self.dragging_label:
            self._handle_label_drag(event)
            return True
        
        return False
    
    def _should_process_motion(self, event, ax) -> bool:
        """Check if motion event should be processed."""
        return (event.inaxes == ax and 
                event.xdata is not None and 
                event.ydata is not None)
    
    def _check_throttling(self) -> bool:
        """Check if enough time has passed since last update (throttling)."""
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return False
        self.last_update_time = current_time
        return True
    
    def _handle_node_drag(self, event) -> None:
        """
        Handle node dragging - updates LayoutContext.
        
        Args:
            event: Matplotlib mouse event
        """
        self.layout.set_node_position(self.dragging_node, event.xdata, event.ydata)
    
    def _handle_label_drag(self, event) -> None:
        """
        Handle edge label dragging - updates LayoutContext.
        
        Args:
            event: Matplotlib mouse event
        """
        from_node, to_node = self.dragging_label
        
        # Get node positions from layout
        pos1 = self.layout.get_node_position(from_node)
        pos2 = self.layout.get_node_position(to_node)
        
        if not pos1 or not pos2:
            return
        
        # Project mouse position onto edge
        t, offset = project_point_to_edge((event.xdata, event.ydata), pos1, pos2)
        
        # Update layout context
        self.layout.set_edge_label_position(from_node, to_node, t, offset)
