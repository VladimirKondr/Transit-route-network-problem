import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from typing import Optional

from ..models.graph import Graph
from ..solver.controller import SolverController
from ..solver.transport_solver import StepType
from ..logging.solution_logger import SolutionLogger
from .layout_context import LayoutContext
from .visualizer import GraphVisualizer


class InteractiveSession:
    """Coordinates interactive solution session."""
    
    def __init__(
        self,
        graph: Graph,
        layout: Optional[LayoutContext] = None,
        controller: Optional[SolverController] = None,
        show_console_in_sidebar: bool = True
    ):
        """
        Initialize interactive session.
        
        Args:
            graph: Network graph with domain model
            layout: Optional layout context (creates new if None)
            controller: Optional solver controller (creates new if None)
            show_console_in_sidebar: If True, show console log in sidebar
        """
        self.graph = graph
        self.layout = layout or LayoutContext()
        self.controller = controller or SolverController(graph)
        self.show_console_in_sidebar = show_console_in_sidebar
        
        self.logger = SolutionLogger(graph, output_callback=self._on_console_output if show_console_in_sidebar else None)
        self.visualizer = GraphVisualizer(graph, self.layout)
        
        self._btn_prev = None
        self._btn_next = None
        self._btn_solve_all = None
        self._btn_reset = None
        self._btn_toggle_console = None
    
    def _on_console_output(self, text: str) -> None:
        """Callback for console output to display in sidebar."""
        if self.visualizer._sidebar_renderer:
            self.visualizer._sidebar_renderer.add_console_message(text)
    
    def setup_and_run(self) -> None:
        """Main entry point: setup layout and run interactive session."""
        # Step 1: Ensure layout is ready
        if not self.layout.is_layout_fixed():
            self.logger.log_message("[SETUP] Layout not configured. Starting interactive layout setup...")
            # Setup interactive layout with callback to transition to solver mode
            self.visualizer.setup_interactive_layout(done_callback=self._on_layout_done)
        else:
            # Layout already fixed, go directly to solver session
            self._setup_solver_session()
        
        # Step 2: Start matplotlib event loop (for either setup or solver mode)
        self.visualizer.start_interaction()
    
    def _on_layout_done(self, event) -> None:
        """
        Callback when layout setup is complete.
        Seamlessly transitions from layout mode to solver mode in the same window.
        """
        # Finalize layout but keep window open
        self.visualizer._finalize_interactive_mode(keep_window_open=True)
        
        # Redraw without recreating figure
        if self.visualizer._fig:
            # Configure axes (legend and sidebar backgrounds)
            self.visualizer._configure_axes()
            # Redraw all content and recalculate limits
            self.visualizer._quick_redraw(preserve_limits=False)
        
        # Create navigation buttons
        self._create_navigation_buttons()
        
        # Print instructions
        self.logger.log_instructions()
        
        # Update window title
        self.visualizer.set_window_title("Transport Problem Solver - Interactive Mode")
        
        # Redraw the canvas
        if self.visualizer._fig:
            self.visualizer._fig.canvas.draw_idle()
    
    def _setup_solver_session(self) -> None:
        """Setup interactive solver session with buttons."""
        # Render initial view
        self.visualizer.render(save_path=None)
        
        # Create navigation buttons
        self._create_navigation_buttons()
        
        # Print instructions
        self.logger.print_instructions()
        
        # Update window title
        self.visualizer.set_window_title("Transport Problem Solver - Interactive Mode")
    
    def _create_navigation_buttons(self) -> None:
        """Create interactive navigation buttons."""
        button_height = 0.04
        button_width = 0.12
        button_y = 0.01
        spacing = 0.02
        
        # Previous button
        ax_prev = plt.axes([0.1, button_y, button_width, button_height])
        self._btn_prev = Button(ax_prev, '< Prev', color='lightgray', hovercolor='gray')
        self._btn_prev.on_clicked(self._on_prev_click)
        
        # Next button
        ax_next = plt.axes([0.1 + button_width + spacing, button_y, button_width, button_height])
        self._btn_next = Button(ax_next, 'Next >', color='lightblue', hovercolor='blue')
        self._btn_next.on_clicked(self._on_next_click)
        
        # Solve All button
        ax_solve = plt.axes([0.1 + 2*(button_width + spacing), button_y, button_width, button_height])
        self._btn_solve_all = Button(ax_solve, 'Solve All', color='lightgreen', hovercolor='green')
        self._btn_solve_all.on_clicked(self._on_solve_all_click)
        
        # Reset button
        ax_reset = plt.axes([0.1 + 3*(button_width + spacing), button_y, button_width, button_height])
        self._btn_reset = Button(ax_reset, 'Reset', color='lightyellow', hovercolor='yellow')
        self._btn_reset.on_clicked(self._on_reset_click)
        
        if self.show_console_in_sidebar:
            ax_console = plt.axes([0.1 + 4*(button_width + spacing), button_y, button_width, button_height])
            self._btn_toggle_console = Button(ax_console, 'Console', color='#FFE4B5', hovercolor='#FFD700')
            self._btn_toggle_console.on_clicked(self._on_toggle_console_click)
        
        self._update_button_states()
    
    def _update_button_states(self) -> None:
        """Update button enabled/disabled states based on current state."""
        if not self._btn_prev:
            return
        
        # Previous button
        self._btn_prev.ax.set_facecolor(
            'lightgray' if self.controller.can_go_prev() else '#E0E0E0'
        )
        
        # Next button
        self._btn_next.ax.set_facecolor(
            'lightblue' if self.controller.can_go_next() else '#E0E0E0'
        )
        
        # Solve All button
        self._btn_solve_all.ax.set_facecolor(
            'lightgreen' if self.controller.can_go_next() else '#E0E0E0'
        )
        
        # Trigger redraw
        if self.visualizer.is_ready():
            plt.gcf().canvas.draw_idle()
    
    def _on_prev_click(self, event) -> None:
        """Handle Previous button click."""
        self.controller.prev_step()
        state = self.controller.get_current_state()
        
        # Show current state (None = initial state before any steps)
        if state is None:
            # Show initial state (empty graph)
            self.visualizer.apply_solution_state(None)
            self.visualizer.set_window_title("Transport Problem Solver - Initial State")
            # Show instructions again
            self.logger.log_instructions()
        else:
            # Replay the log FIRST (before visual update)
            step_num = self.controller.current_step + 1
            self.logger.replay_step_log(step_num)
            
            # Then show the state visually (this will trigger redraw but log is already set)
            self._show_current_state()
        
        self._update_button_states()
    
    def _on_next_click(self, event) -> None:
        """Handle Next button click."""
        self.controller.next_step()
        state = self.controller.get_current_state()
        
        if state:
            # Log the new step
            step_num = self.controller.current_step + 1
            self.logger.log_step(state, step_num)
            
            # Show it visually
            self._show_current_state()
            self._update_button_states()
    
    def _on_solve_all_click(self, event) -> None:
        """Handle Solve All button click."""
        if not self.controller.can_go_next():
            return
        
        self.logger.log_solve_all_start()
        
        initial_step = self.controller.current_step
        
        while self.controller.can_go_next():
            self.controller.next_step()
            state = self.controller.get_current_state()
            if state:
                self.logger.log_step(state, self.controller.current_step + 1)
            
            if self.controller.is_solved():
                break
        
        total_steps = self.controller.current_step - initial_step
        self.logger.log_solve_all_complete(total_steps)
        
        self._show_current_state()
        self._update_button_states()
    
    def _on_reset_click(self, event) -> None:
        """Handle Reset button click."""
        self.logger.log_reset()
        
        # Reset controller
        self.controller.reset()
        
        # Reset visualization to initial state (no solution)
        self.visualizer.apply_solution_state(None)
        
        # Update window title
        self.visualizer.set_window_title("Transport Problem Solver - Ready to Start")
        
        # Update buttons
        self._update_button_states()
    
    def _on_toggle_console_click(self, event) -> None:
        """Handle Console toggle button click."""
        if self.visualizer._sidebar_renderer:  # type: ignore
            current_state = self.visualizer._sidebar_renderer.show_console_log  # type: ignore
            self.visualizer._sidebar_renderer.set_show_console_log(not current_state)  # type: ignore
            
            # Redraw sidebar
            state = self.controller.get_current_state()
            self.visualizer._sidebar_renderer.draw_sidebar(state)  # type: ignore
            
            # Update button color
            if self._btn_toggle_console:
                color = '#90EE90' if not current_state else '#FFE4B5'
                self._btn_toggle_console.ax.set_facecolor(color)
            
            # Trigger redraw
            if self.visualizer.is_ready():
                plt.gcf().canvas.draw_idle()
    
    def _show_current_state(self) -> None:
        """Show the current solver state visually."""
        state = self.controller.get_current_state()
        if not state:
            return
        
        # Update visualization
        self.visualizer.apply_solution_state(state)
        
        # Update window title
        step_num = self.controller.current_step + 1
        total_steps = self.controller.get_step_count()
        step_name = self._get_step_name(state.step_type)
        title = f"Step {step_num}/{total_steps}: {step_name}"
        self.visualizer.set_window_title(title)
    
    def _get_step_name(self, step_type: StepType) -> str:
        """Get human-readable step name."""
        names = {
            StepType.INITIAL_BASIS: "Initial Basis",
            StepType.CALCULATE_POTENTIALS: "Calculate Potentials",
            StepType.CHECK_OPTIMALITY: "Check Optimality",
            StepType.FIND_CYCLE: "Find Cycle",
            StepType.CALCULATE_THETA: "Calculate θ",
            StepType.UPDATE_FLOWS: "Update Flows",
            StepType.OPTIMAL: "Optimal Solution"
        }
        return names.get(step_type, step_type.value)
