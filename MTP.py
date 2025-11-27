import math
from typing import List, Optional, Any, Tuple
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.widgets import Button

from network_transport.models import Graph
from network_transport.solver import SolverController, SolutionState
from network_transport.ui import InteractiveSession

def create_graph_from_matrix(
    costs: List[List[float]], 
    supplies: List[float], 
    demands: List[float],
    capacities: Optional[List[List[float]]]
) -> Graph:
    graph = Graph()
    num_suppliers = len(supplies)
    num_consumers = len(demands)

    total_supply = sum(supplies)
    total_demand = sum(demands)
    if not math.isclose(total_supply, total_demand):
        raise ValueError(f"Задача несбалансирована: Запас ({total_supply}) != Спрос ({total_demand})")

    for i in range(num_suppliers):
        graph.add_node(f"A{i+1}", balance=supplies[i])
    for j in range(num_consumers):
        graph.add_node(f"B{j+1}", balance=-demands[j])
    for i in range(num_suppliers):
        for j in range(num_consumers):
            if capacities is not None:
                graph.add_edge(f"A{i+1}", f"B{j+1}", cost=costs[i][j], capacity=capacities[i][j])
            else :
                graph.add_edge(f"A{i+1}", f"B{j+1}", cost=costs[i][j])

            
    return graph

class MatrixVisualizer:
    def __init__(self, graph: Graph, costs: List[List[float]], supplies: List[float], demands: List[float]):
        self.graph = graph
        self.costs = costs
        self.supplies = supplies
        self.demands = demands
        self.num_suppliers = len(supplies)
        self.num_consumers = len(demands)
        
        self._fig, self.ax = None, None
        self.cell_artists: List[Any] = []

        self._sidebar_renderer = None

    @property
    def fig(self):
        return self._fig

    def setup_figure(self):
        fig_width = self.num_consumers * 2.5 + 4
        fig_height = self.num_suppliers * 1.5 + 3
        self._fig = plt.figure(figsize=(fig_width, fig_height)) # type: ignore
        
        self.ax = self._fig.add_axes([0.05, 0.2, 0.9, 0.70]) # type: ignore

        self.ax.axis('off') # type: ignore
        self.ax.invert_yaxis() # type: ignore
        self.ax.set_aspect('equal') # type: ignore
        
        self.draw_grid_and_headers()
        self._fig.subplots_adjust(bottom=0.15)
    
    def draw_grid_and_headers(self):
        ax = self.ax # type: ignore

        for j in range(self.num_consumers): 
            ax.text(j + 1.5, 0.5, f"B{j+1}", ha='center', va='center', fontweight='bold') # type: ignore

        ax.text(self.num_consumers + 1.5, 0.5, "Запасы", ha='center', va='center', fontweight='bold') # type: ignore
        for i in range(self.num_suppliers): 
            ax.text(0.5, i + 1.5, f"A{i+1}", ha='center', va='center', fontweight='bold') # type: ignore

        for i, supply in enumerate(self.supplies): 
            ax.text(self.num_consumers + 1.5, i + 1.5, f"{supply:.0f}", ha='center', va='center', color='blue', fontsize=14) # type: ignore

        for j, demand in enumerate(self.demands): 
            ax.text(j + 1.5, self.num_suppliers + 1.5, f"{demand:.0f}", ha='center', va='center', color='red', fontsize=14) # type: ignore

        ax.text(0.5, self.num_suppliers + 1.5, "Спрос", ha='center', va='center', fontweight='bold') # type: ignore
        for i in range(self.num_suppliers + 2): 
            ax.axhline(i + 1, color='lightgray', lw=1, zorder=-10) # type: ignore

        for j in range(self.num_consumers + 2): 
            ax.axvline(j + 1, color='lightgray', lw=1, zorder=-10) # type: ignore
        
        for j in range(self.num_consumers + 2): 
            ax.axvline(j + 1, color='lightgray', lw=1, zorder=-10) # type: ignore
        ax.text(self.num_consumers + 2.5, 0.5, "Потенц. u", ha='center', va='center', fontweight='bold', color='darkgreen') # type: ignore
        ax.text(0.5, self.num_suppliers + 2.5, "Потенц. v", ha='center', va='center', fontweight='bold', color='darkgreen') # type: ignore
    
    def apply_solution_state(self, state: Optional[SolutionState]):
        if self.ax is None:  # type: ignore
            return
        for artist in self.cell_artists: 
            artist.remove()
        self.cell_artists.clear()
        if state is None or state.flows is None:
            self._redraw()
            return
        cycle_signs: dict[Tuple[str, str], str] = {}
        if state and state.cycle:
            for cycle_edge in state.cycle:
                cycle_signs[cycle_edge.edge.edge_id] = cycle_edge.sign
        ax = self.ax # type: ignore
        for i in range(self.num_suppliers):
            for j in range(self.num_consumers):
                edge_id = (f"A{i+1}", f"B{j+1}")
                edge = self.graph.get_edge(*edge_id)
                if not edge: 
                    continue
                flow, cost, capacity = state.flows.get(edge_id, 0.0), self.costs[i][j], edge.capacity
                cap_str = "∞" if capacity == float('inf') else f"{capacity:.0f}"
                face_color, edge_color, lw = ('white', 'lightgray', 1)
                if state.basis_edges and edge_id in state.basis_edges: 
                    face_color, edge_color, lw = ('#FFFFE0', 'orange', 2)
                if state.entering_edge == edge_id: 
                    face_color, edge_color, lw = ('#D4EDDA', 'green', 2.5)
                if state.leaving_edge == edge_id: 
                    face_color, edge_color, lw = ('#F8D7DA', 'red', 2.5)
                rect = Rectangle((j + 1, i + 1), 1, 1, facecolor=face_color, edgecolor=edge_color, linewidth=lw, zorder=-1)
                ax.add_patch(rect) # type: ignore
                self.cell_artists.append(rect)
                self.cell_artists.append(ax.text(j + 1.05, i + 1.05, cap_str, ha='left', va='top', fontsize=16, color='purple')) # type: ignore
                self.cell_artists.append(ax.text(j + 1.95, i + 1.05, f"{cost:.0f}", ha='right', va='top', fontsize=16, color='black', bbox=dict(facecolor='yellow', edgecolor='orange', pad=0.1, boxstyle='round,pad=0.2'))) # type: ignore
                self.cell_artists.append(ax.text(j + 1.05, i + 1.95, f"{flow:.0f}", ha='left', va='bottom', fontsize=16, color='darkcyan', fontweight='bold')) # type: ignore
                if state.deltas and edge_id not in state.basis_edges and state.deltas.get(edge_id) is not None: # type: ignore
                    self.cell_artists.append(ax.text(j + 1.95, i + 1.95, f"Δ={state.deltas.get(edge_id):+.1f}", ha='right', va='bottom', fontsize=12, color='dimgray')) # type: ignore
                if edge_id in cycle_signs:
                    sign = cycle_signs[edge_id]
                    color = 'green' if sign == '+' else 'red'
                    
                    sign_artist = ax.text(j + 1.5, i + 1.5, f"{sign}", # type: ignore
                                        ha='center', va='center', fontsize=30, color=color,
                                        fontweight='bold',
                                        bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', boxstyle='circle,pad=0.3'))
                    self.cell_artists.append(sign_artist)
        if state.potentials:
            for i in range(self.num_suppliers):
                node_id = f"A{i+1}"
                potential = state.potentials.get(node_id)
                if potential is not None:
                    p_artist = ax.text(self.num_consumers + 2.5, i + 1.5, f"{potential:.1f}", # type: ignore
                                       ha='center', va='center', fontsize=14, color='darkgreen',
                                       fontstyle='italic')
                    self.cell_artists.append(p_artist)

            for j in range(self.num_consumers):
                node_id = f"B{j+1}"
                potential = state.potentials.get(node_id)
                if potential is not None:
                    p_artist = ax.text(j + 1.5, self.num_suppliers + 2.5, f"{potential:.1f}", # type: ignore
                                       ha='center', va='center', fontsize=14, color='darkgreen',
                                       fontstyle='italic')
                    self.cell_artists.append(p_artist)
            
        self._redraw()

    def _redraw(self):
        if self._fig: self._fig.canvas.draw_idle() # type: ignore
    
    def set_window_title(self, title: str):
        if self._fig: self._fig.canvas.manager.set_window_title(title) # type: ignore

class MatrixInteractiveSession(InteractiveSession):
    def __init__(self, graph: Graph, costs: List[List[float]], supplies: List[float], demands: List[float]):
        super().__init__(graph=graph, controller=SolverController(graph))
        self.matrix_visualizer = MatrixVisualizer(graph, costs, supplies, demands)
        self.visualizer = self.matrix_visualizer

    def setup_and_run(self) -> None:
        print("Запуск визуализатора... Используйте кнопки для пошагового решения.")
        self.visualizer.setup_figure()
        self._create_navigation_buttons()
        self._show_current_state()
        plt.show() # type: ignore

    def _create_navigation_buttons(self) -> None:
        fig = self.visualizer.fig
        if not fig: return
        btn_props = {  # type: ignore
            '< Prev': (0.15, self._on_prev_click, 'lightgray'), # type: ignore
            'Next >': (0.32, self._on_next_click, 'lightblue'), # type: ignore
            'Solve All': (0.49, self._on_solve_all_click, 'lightgreen'),  # type: ignore
            'Reset': (0.66, self._on_reset_click, 'lightyellow'),  # type: ignore
        }
        self._buttons = [] 
        for label, (x, func, color) in btn_props.items(): # type: ignore
            ax = fig.add_axes([x, 0.02, 0.15, 0.05]) # type: ignore
            btn = Button(ax, label, color=color, hovercolor=color.replace('light', '')) # type: ignore
            btn.on_clicked(func) # type: ignore
            self._buttons.append(btn) # type: ignore
        

if __name__ == "__main__":
    C: List[List[float]] = [
    [10 , 3 , 8 , 11 , 2],
    [ 8 , 7 , 6 , 10 , 5],
    [11 , 10 , 12 , 9 , 10],
    [ 12 , 14 , 10 , 14 , 8]
    ]
    A: List[float] = [10, 10, 8, 11]
    B: List[float] = [12, 5, 8, 6, 8]

    D: Optional[List[List[float]]] = [
        [14, 11, 16, 18, 14],
        [15, 24, 13, 15, 16],
        [15, 15, 14, 14, 19],
        [16, 14, 14, 13, 16]
    ] # make None if there are no upper bounds
    D = None

    try:
        transport_graph = create_graph_from_matrix(costs=C, supplies=A, demands=B, capacities=D)
        session = MatrixInteractiveSession(
            graph=transport_graph,
            costs=C,
            supplies=A,
            demands=B
        )
        session.setup_and_run()
    except ValueError as e:
        print(f"[ОШИБКА] Невозможно запустить: {e}")