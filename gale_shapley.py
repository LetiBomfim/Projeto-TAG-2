from collections import deque

class GaleShapley:
    def __init__(self, students, projects):
        self.students = {s.code: s for s in students}
        self.projects = {p.code: p for p in projects}
        self.matching = {}
        self.temporary_matching = {}
        self.rejections = set()
        self.proposals_history = []
        self.free_students = None

        for project_code in self.projects:
            self.matching[project_code] = []

    def match(self, max_iterations=300):
        #Fila de alunos livres
        self.free_students = deque(self.students.keys())

        iteration = 0
        while self.free_students and iteration < max_iterations:
            student_code = self.free_students.popleft()
            student = self.students[student_code]

            #Tenta fazer proposta para próximos projetos na preferência
            while student.proposal_index < len(student.preferences):
                project_code = student.preferences[student.proposal_index]

                #Ignora projetos inexistentes (tenta próximo)
                if project_code not in self.projects:
                    self.rejections.add((student_code, project_code))
                    student.proposal_index += 1
                    continue

                project = self.projects[project_code]

                #Verifica se aluno atende requisitos mínimos
                if student.grade >= project.min_grade:
                    result = self._make_proposal(student_code, project_code)

                    #Se o aluno foi aceito, para de propor
                    if result == "accepted":
                        break
                    elif result == "rejected":
                        self.rejections.add((student_code, project_code))
                        student.proposal_index += 1
                    #Se "waiting", continua para próxima preferência
                
                else:
                    student.proposal_index += 1

            #Se aluno não foi aceito em nenhum projeto, mantém livre
            if student_code not in self.temporary_matching and student.proposal_index >= len(student.preferences):
                #Aluno não conseguiu vaga em nenhuma preferência
                pass

            iteration += 1

        print(f"Algoritmo convergiu em {iteration} iterações")
        self._finalize_matching()
        return self.matching

    def _make_proposal(self, student_code, project_code):
        project = self.projects[project_code]
        current_students = self.matching[project_code]

        #Registra proposta para visualização
        self.proposals_history.append({
            'student': student_code,
            'project': project_code,
            'type': 'active'
        })

        #Verifica se projeto pode aceitar mais alunos
        if len(current_students) < project.max_students:
            #Aceita aluno diretamente
            self._accept_student(student_code, project_code)
            return "accepted"
        else:
            #Verifica se este aluno é melhor que algum atual
            worst_student_code = self._find_worst_student(project_code, current_students)

            if worst_student_code and self._is_better_student(student_code, worst_student_code, project_code):
                #Substitui o pior aluno
                self._replace_student(student_code, worst_student_code, project_code)
                return "accepted"
            else:
                #Rejeita aluno
                return "rejected"

    def _find_worst_student(self, project_code, student_codes):
        if not student_codes:
            return None

        project = self.projects[project_code]
        pref_index = {code: idx for idx, code in enumerate(project.preference_list)}

        sorted_students = sorted(student_codes, key=lambda code: pref_index.get(code, float("inf")))

        return sorted_students[-1] if sorted_students else None

    def _is_better_student(self, student1_code, student2_code, project_code):
        project = self.projects[project_code]

        if student1_code not in project.preference_list:
            return False

        if student2_code not in project.preference_list:
            return True

        pos1 = project.preference_list.index(student1_code)
        pos2 = project.preference_list.index(student2_code)

        return pos1 < pos2

    def _accept_student(self, student_code, project_code):
        self.temporary_matching[student_code] = project_code
        self.matching[project_code].append(student_code)

        self.proposals_history.append({
            'student': student_code,
            'project': project_code,
            'type': 'temporary'
        })

    def _replace_student(self, new_student_code, old_student_code, project_code):
        self.matching[project_code].remove(old_student_code)
        if old_student_code in self.temporary_matching:
            del self.temporary_matching[old_student_code]

        self.free_students.append(old_student_code)
        self.students[old_student_code].proposal_index += 1

        self._accept_student(new_student_code, project_code)
        self.rejections.add((old_student_code, project_code))

    def _finalize_matching(self):
        #Remove projetos que não atingiram o mínimo de alunos
        for project_code, students in list(self.matching.items()):
            if len(students) < self.projects[project_code].min_students:
                #Libera alunos desses projetos
                for student_code in students:
                    if student_code in self.temporary_matching:
                        del self.temporary_matching[student_code]
                self.matching[project_code] = []

    def get_iteration_data(self, iteration):
        if iteration >= len(self.proposals_history):
            return None

        return self.proposals_history[iteration]

    def get_matching_stats(self):
        total_students_matched = sum(len(students) for students in self.matching.values())
        total_projects_active = sum(1 for students in self.matching.values() if len(students) >= 1)

        stats = {
            'total_students': len(self.students),
            'total_students_matched': total_students_matched,
            'total_projects': len(self.projects),
            'total_projects_active': total_projects_active,
            'matching_rate': total_students_matched / len(self.students)
        }

        return stats