import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import numpy as np

class GraphVisualizer:
    def __init__(self, students, projects, algorithm=None):
        self.students = students
        self.projects = projects
        self.algorithm = algorithm
        self.iteration = 0
        self.max_iterations = 10
        self.matching_history = []
        self.proposals_history = []
        self.rejections_history = []

        #Cores para cada tipo de estado
        self.color_active = "#128118"
        self.color_temporary = "#00A79B"
        self.color_rejection = "#DF0707"

    def create_bipartite_graph(self):
        G = nx.Graph()

        students_nodes = [f"S{student.code}" for student in self.students]
        project_nodes = [f"P{project.code}" for project in self.projects]

        G.add_nodes_from(students_nodes, bipartite=0)
        G.add_nodes_from(project_nodes, bipartite=1)

        for student in self.students:
            s_code = student.code
            prefs = getattr(student, "preferences", []) or []
            for project_id in prefs:
                G.add_edge(f"S{s_code}", f"P{project_id}")
        
        return G, students_nodes, project_nodes

    def animate_matching(self, matching_data, samples=10):
        if not matching_data:
            raise ValueError("matching_data vazio")

        G, students_nodes, project_nodes = self.create_bipartite_graph()

        pos = nx.bipartite_layout(G, students_nodes, scale=2)

        fig = plt.figure(figsize=(14, 9))
        gs = fig.add_gridspec(2, 2, width_ratios=[3, 1], height_ratios=[3, 1], hspace=0.35, wspace=0.25)
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[1, 0])
        ax4 = fig.add_subplot(gs[1, 1])

        fig.suptitle("Visualização do Emparelhamento Estável", fontsize=16, fontweight="bold")

        n = len(matching_data)
        samples = max(1, min(samples, n))
        indices = np.unique(np.linspace(0, n - 1, samples, dtype=int)).tolist()

        legend_elements = [
            mpatches.Patch(color=self.color_active, label="Proposta Ativa"),
            mpatches.Patch(color=self.color_temporary, label="Emparelhamento Temporário"),
            mpatches.Patch(color=self.color_rejection, label="Rejeição"),
        ]

        def update(frame_index):
            data = matching_data[frame_index]
            iteration = data.get("iteration", frame_index)
            proposals = set(data.get("proposals", []))
            temp_matches = set(data.get("temporary_matches", []))
            rejections = set(data.get("rejections", []))

            active_edges = proposals | temp_matches | rejections

            for ax in (ax1, ax2, ax3, ax4):
                ax.clear()

            ax1.set_title(f"Iteração {iteration+1} (mostrar {indices.index(frame_index)+1}/{len(indices)})", fontweight="bold")

            nx.draw_networkx_nodes(G, pos, nodelist=students_nodes, node_color="#FFD93D", node_size=900, ax=ax1)
            nx.draw_networkx_nodes(G, pos, nodelist=project_nodes, node_color="#83006D", node_size=900, ax=ax1)

            #Desenha apenas arestas com interação
            edge_colors = []
            edge_widths = []
            edges_to_draw = []
            
            for edge in G.edges():
                if edge in active_edges or (edge[1], edge[0]) in active_edges:
                    edges_to_draw.append(edge)
                    
                    if edge in proposals or (edge[1], edge[0]) in proposals:
                        edge_colors.append(self.color_active)
                        edge_widths.append(3.5)
                    elif edge in temp_matches or (edge[1], edge[0]) in temp_matches:
                        edge_colors.append(self.color_temporary)
                        edge_widths.append(3.0)
                    elif edge in rejections or (edge[1], edge[0]) in rejections:
                        edge_colors.append(self.color_rejection)
                        edge_widths.append(2.0)

            nx.draw_networkx_edges(G, pos, edgelist=edges_to_draw, edge_color=edge_colors, 
                                   width=edge_widths, ax=ax1, alpha=0.9)

            nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold", ax=ax1)
            
            ax1.axis("off")
            ax1.legend(handles=legend_elements, loc="upper left", fontsize=8)
            
            ax2.set_title("Histórico de Propostas", fontweight="bold")
            ax2.axis("off")
            history_lines = []
            
            for i, idx in enumerate(indices):
                snap = matching_data[idx]
                history_lines.append(f"{i+1}. it {snap.get('iteration', idx)+1}: {len(snap.get('proposals', []))} propostas")
            
            ax2.text(0.02, 0.98, "\n".join(history_lines), transform=ax2.transAxes,
                     fontsize=10, verticalalignment="top", family="monospace",
                     bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.6))

            ax3.set_title("Estatísticas", fontweight="bold")
            ax3.axis("off")
            stats_text = (f"Propostas ativas: {len(proposals)}\n"
                          f"Emparelhamentos temporários: {len(temp_matches)}\n"
                          f"Rejeições: {len(rejections)}")
            ax3.text(0.02, 0.98, stats_text, transform=ax3.transAxes,
                     fontsize=11, verticalalignment="top", family="monospace",
                     bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.6))

            ax4.set_title("Emparelhamentos Atuais", fontweight="bold")
            ax4.axis("off")

            current_matching = data.get("final_matching", {})
            matching_lines = [f"{s} → {p}" for s, p in sorted(current_matching.items())]
            
            if not matching_lines:
                matching_lines = ["(Nenhum emparelhamento confirmado)"]
            
            ax4.text(0.02, 0.98, "\n".join(matching_lines), transform=ax4.transAxes,
                     fontsize=10, verticalalignment="top", family="monospace",
                     bbox=dict(boxstyle="round", facecolor="lightgreen", alpha=0.6))

        anim = FuncAnimation(fig, update, frames=indices, repeat=True, interval=1000)
        
        plt.tight_layout()
        plt.show()
        
        return anim
