import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import numpy as np

class GraphVisualizer:
    def __init__(self, students, projects):
        self.students = students
        self.projects = projects
        self.iteration = 0
        self.max_iterations = 10
        self.matching_history = []
        self.proposals_history = []
        self.rejections_history = []

        #Cores para cada tipo de estado
        self.color_active = "#128118"
        self.color_temporary = "#00A79B"
        self.color_rejection = "#DF0707"
        self.color_neutral = "#ACABAB"

    def create_bipartite_graph(self):
        G = nx.Graph()

        students_nodes = [f"S{i}" for i in range(len(self.students))]
        project_nodes = [f"P{i}" for i in range(len(self.projects))]

        G.add_nodes_from(students_nodes, bipartite=0)
        G.add_nodes_from(project_nodes, bipartite=1)

        for student in self.students:
            student_id = student["id"]
            for project_id in student["preferences"]:
                G.add_edge(f"S{student_id}", f"P{project_id}")
        
        return G, students_nodes, project_nodes

    def animate_matching(self, matching_data):
        G, students_nodes, project_nodes = self.create_bipartite_graph

        pos = nx.bipartite_layout(G, students_nodes, scale=2)

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("Visuzalização do Emparelhamento Estável", fontsize=16, fontweight="bold")

        def update(frame):
            for ax in axes.flat:
                ax.clear()

                if frame >= len(matching_data):
                    return
                
                data = matching_data[frame]
                iteration = data["iteration"]
                proposals = data.get("proposals", [])
                temp_matches = data.get("temporary_matches", [])
                rejections = data.get("rejections", [])

                ax1 = axes[0, 0]
                ax1.set_title(f"Iteração {iteration+1}/10", fontweight="bold")

                nx.draw_networkx_nodes(G, pos, nodelist=students_nodes, node_color="#FFD93D", node_size=800, label="Estudantes", ax=ax1)
                nx.draw_networkx_nodes(G, pos, nodelist=project_nodes, node_color="#83006D", node_size=800, label="Projetos", ax=ax1)

                edge_colors = []
                edge_widths = []

                for edge in G.edges():
                    if edge in proposals or (edge[1], edge[0]) in proposals:
                        edge_colors.append(self.color_active)
                        edge_widths.append(3)
                    elif edge in temp_matches or (edge[1], edge[0]) in temp_matches:
                        edge_colors.append(self.color_temporary)
                        edge_widths.append(3)
                    elif edge in rejections or (edge[1], edge[0]) in rejections:
                        edge_colors.append(self.color_rejection)
                        edge_widths.append(2)
                    else:
                        edge_colors.append(self.color_neutral)
                        edge_widths.append(1)

                nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=edge_widths, ax=ax1, alpha=0.7)
                nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold", ax=ax1)

            legend_elements = [
                mpatches.Patch(color=self.color_active, label="Proposta Ativa"),
                mpatches.Patch(color=self.color_temporary, label="Emparelhamento Temporário"),
                mpatches.Patch(color=self.color_rejection, label="Rejeição"),
                mpatches.Patch(color=self.color_neutral, label="Sem Interação")
            ]

            ax1.legend(handles=legend_elements, loc="upper left", fontsize=9)
            ax1.axis("off")

            ax2 = axes[0, 1]
            ax2.set_title("Histórico de Propostas", fontweight="bold")
            ax2.axis("off")
            
            history_text = "Iterações Anteriores:\n"
            for i, prev_data in enumerate(matching_data[:iteration+1]):
                history_text += f"Iteração {i+1}: {len(prev_data.get("proposals", []))} propostas\n"
            
            ax2.text(0.05, 0.95, history_text, transform=ax2.transAxes, fontsize=10, verticalalignment="top", family="monospace",
                    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
            
            ax3 = axes[1, 0]
            ax3.set_title(f"Estatísticas - Iteração {iteration + 1}", fontweight="bold")
            ax3.axis("off")
            
            stats_text = f"""
            Propostas ativas: {len(proposals)}
            Emparelhamentos temporários: {len(temp_matches)}
            Rejeições: {len(rejections)}"""
            
            ax3.text(0.05, 0.95, stats_text, transform=ax3.transAxes, 
                    fontsize=11, verticalalignment="top", family="monospace",
                    bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.5))
            
            ax4 = axes[1, 1]
            ax4.set_title("Emparelhamentos Atuais", fontweight="bold")
            ax4.axis("off")
            
            current_matching = data.get("final_matching", {})
            matching_text = "Emparelhamentos Confirmados:\n"
            for student_id, project_id in sorted(current_matching.items()):
                matching_text += f"Estudante {student_id} → Projeto {project_id}\n"
            
            ax4.text(0.05, 0.95, matching_text, transform=ax4.transAxes, fontsize=10, verticalalignment="top", family="monospace", bbox=dict(boxstyle="round", facecolor="lightgreen", alpha=0.5))
        
        anim = FuncAnimation(fig, update, frames=len(matching_data), repeat=True, interval=1000)
        
        plt.tight_layout()
        plt.show()
        
        return anim
