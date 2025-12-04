import os
from gale_shapley import GaleShapley
from graph_visualizer import GraphVisualizer
from file_parser import FileParser

class GraphMatching:
    def __init__(self):
        self.projects = []
        self.students = []
        self.matching = None
        self.algorithm = None
        
    def load_data(self, filename):
        parser = FileParser()
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, filename)

        self.projects, self.students = parser.parse_file(path)
        print(f"Carregados {len(self.projects)} projetos e {len(self.students)} alunos")
        
    def run_matching(self):
        self.algorithm = GaleShapley(self.students, self.projects)
        self.matching = self.algorithm.match()
            
        stats = self.algorithm.get_matching_stats()
        print(f"Emparelhamento concluído: {stats['total_students_matched']}/{stats['total_students']} alunos alocados")
        print(f"Projetos ativos: {stats['total_projects_active']}/{stats['total_projects']}")
        
    def visualize_process(self, iterations=10):
        visualizer = GraphVisualizer(self.students, self.projects, self.algorithm)
        visualizer.animate_matching(iterations)
        
    def generate_report(self):
        if self.matching:
            self._print_matching_matrix()
            self._calculate_preference_stats()
            
    def _print_matching_matrix(self):
        print("\n          MATRIZ DE EMPARELHAMENTO")
        print("Aluno\tProjeto\tNota\tRank Aluno\tRank Projeto")
        
        for project_code, student_codes in self.matching.items():
            #Apenas projetos com alunos
            if student_codes:
                project = self.algorithm.projects[project_code]
                
                for student_code in student_codes:
                    student = self.algorithm.students[student_code]
                    
                    #Rank do aluno na preferência do projeto
                    project_rank = "N/A"
                    if student_code in project.preference_list:
                        project_rank = project.preference_list.index(student_code) + 1
                    
                    #Rank do projeto na preferência do aluno
                    student_rank = "N/A"
                    if project_code in student.preferences:
                        student_rank = student.preferences.index(project_code) + 1
                    
                    print(f"{student_code}\t{project_code}\t{student.grade}\t{project_rank}º\t\t{student_rank}º")
    
    def _calculate_preference_stats(self):
        print("\n       ESTATÍSTICAS DE PREFERÊNCIA")
        
        student_satisfaction = []
        project_satisfaction = []
        
        for project_code, student_codes in self.matching.items():
            for student_code in student_codes:
                student = self.algorithm.students[student_code]
                project = self.algorithm.projects[project_code]
                
                #Satisfação do aluno (1 = primeira escolha, 2 = segunda, etc.)
                if project_code in student.preferences:
                    student_rank = student.preferences.index(project_code) + 1
                    student_satisfaction.append(student_rank)
                
                #Satisfação do projeto
                if student_code in project.preference_list:
                    project_rank = project.preference_list.index(student_code) + 1
                    project_satisfaction.append(project_rank)
        
        if student_satisfaction:
            avg_student = sum(student_satisfaction) / len(student_satisfaction)
            print(f"Média de satisfação dos alunos: {avg_student:.2f} (1 = melhor)")
        
        if project_satisfaction:
            avg_project = sum(project_satisfaction) / len(project_satisfaction)
            print(f"Média de satisfação dos projetos: {avg_project:.2f} (1 = melhor)")

if __name__ == "__main__":
    graph = GraphMatching()
    graph.load_data("entradaProj2.25TAG.txt")
    graph.run_matching()
    graph.generate_report()