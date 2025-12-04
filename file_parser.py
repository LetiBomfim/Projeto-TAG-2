import re

class Project:
    def __init__(self, code, max_students, min_grade):
        self.code = code
        self.max_students = max_students
        self.min_grade = min_grade
        self.min_students = 1
        self.preference_list = []
        
class Student:
    def __init__(self, code, preferences, grade):
        self.code = code
        self.preferences = preferences
        self.grade = grade
        self.matched_project = None
        self.proposal_index = 0

class FileParser:
    def parse_file(self, filename):
        projects = []
        students = []
        
        try:
            with open(filename, 'r') as file:
                content = file.read()

            #Remove linhas de comentário que começam com '//' para facilitar o parse
            cleaned = "\n".join(line for line in content.splitlines() if not line.strip().startswith("//"))

            #Tenta extrair projetos e estudantes do conteúdo
            projects = self.parse_projects(cleaned)
            students = self.parse_students(cleaned)

            #Gera preferências dos projetos a partir das notas dos alunos
            self.generate_project_preferences(projects, students)
            
        except FileNotFoundError:
            print(f"Arquivo {filename} não encontrado!")
            projects, students = self.generate_sample_data()
            
        return projects, students
    
    def parse_projects(self, projects_section):
        projects = []
        #Padrão: (P1, 2, 5)
        pattern = r'\(\s*([A-Za-z0-9_]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)'
        matches = re.findall(pattern, projects_section)
        for match in matches:
            code, max_students, min_grade = match
            projects.append(Project(code=code.strip(), max_students=int(max_students), min_grade=int(min_grade)))
        return projects

    def parse_students(self, students_section):
        students = []
        #Padrão: (A1):(P1, P3, P50)(5)
        pattern = r'\(\s*([A-Za-z0-9_]+)\s*\)\s*:\s*\(\s*([^)]+?)\s*\)\s*\(?\s*(\d+)\s*\)?'
        matches = re.findall(pattern, students_section)
        for match in matches:
            code, prefs_str, grade = match
            preferences = [p.strip() for p in prefs_str.split(',') if p.strip()]
            students.append(Student(code=code.strip(), preferences=preferences, grade=int(grade)))
        return students
    
    def generate_project_preferences(self, projects, students):
        project_dict = {p.code: p for p in projects}
        
        for project in projects:
            #Filtra alunos que atendem ao requisito mínimo de nota
            eligible_students = [s for s in students if s.grade >= project.min_grade]
            
            #Ordena alunos por nota (decrescente) e depois por código
            eligible_students.sort(key=lambda s: (-s.grade, s.code))
            
            #Define a lista de preferência do projeto
            project.preference_list = [s.code for s in eligible_students]