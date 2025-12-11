from collections import deque
import random

class GaleShapley:
    def __init__(self, students, projects):
        self.students = {s.code: s for s in students}
        self.projects = {p.code: p for p in projects}
        
        # Inicializa o estado pela primeira vez
        self.reset_state()

    def reset_state(self):
        """
        Reinicia todas as estruturas de dados para permitir uma nova execução
        do algoritmo (limpa matches anteriores).
        """
        self.matching = {}          # {projeto_code: [lista_alunos]}
        self.temporary_matching = {} # {aluno_code: projeto_code} (Para busca rápida)
        self.rejections = set()
        self.proposals_history = []
        self.free_students = None   # Usado no Student-Optimal
        
        # Garante que todo projeto comece com lista vazia no matching
        for project_code in self.projects:
            self.matching[project_code] = []
            # Reinicia índice de proposta dos projetos (para o modo Project-Optimal)
            self.projects[project_code].proposal_index = 0

        # Reinicia índice de proposta dos alunos
        for student in self.students.values():
            student.proposal_index = 0
            student.matched_project = None

    def match(self, proposer_type="student", random_order=False, max_iterations=500, collect_history=False):
        """
        Método principal que direciona para a variação correta do algoritmo.
        :param proposer_type: 'student' (Orientado a Aluno) ou 'project' (Orientado a Projeto)
        :param random_order: Se True, escolhe o proponente aleatoriamente da fila.
        """
        # Limpa o estado antes de começar uma nova execução
        self.reset_state()
        
        if proposer_type == "student":
            result = self._match_student_optimal(random_order, max_iterations, collect_history)
        elif proposer_type == "project":
            result = self._match_project_optimal(random_order, max_iterations, collect_history)
        else:
            raise ValueError("Tipo de proponente desconhecido. Use 'student' ou 'project'.")

        #Para visualização
        if collect_history:
            return result
        else:
            return result

    # =========================================================================
    # VARIAÇÃO 1: STUDENT-OPTIMAL (O código original, adaptado)
    # =========================================================================
    def _match_student_optimal(self, random_order, max_iterations, collect_history=False):
        # Fila de alunos livres (convertido para lista para permitir random.choice)
        self.free_students = list(self.students.keys())

        iteration = 0
        matching_data = []
        while self.free_students and iteration < max_iterations:
            
            start_proposals_len = len(self.proposals_history)

            # --- Lógica de Seleção (Sequencial ou Aleatória) ---
            if random_order:
                # Escolhe um aleatório da lista e remove
                student_code = random.choice(self.free_students)
                self.free_students.remove(student_code)
            else:
                # Pega o primeiro (comportamento de fila/deque original)
                student_code = self.free_students.pop(0)

            student = self.students[student_code]

            # Tenta fazer proposta para próximos projetos na preferência
            # (Mantido while original para processar rejeições imediatas sem gastar iteração do loop principal)
            while student.proposal_index < len(student.preferences):
                project_code = student.preferences[student.proposal_index]

                # Ignora projetos inexistentes (tenta próximo)
                if project_code not in self.projects:
                    self.rejections.add((student_code, project_code))
                    student.proposal_index += 1
                    continue

                project = self.projects[project_code]

                # Verifica se aluno atende requisitos mínimos
                if student.grade >= project.min_grade:
                    result = self._make_proposal(student_code, project_code)

                    # Se o aluno foi aceito, para de propor
                    if result == "accepted":
                        break
                    elif result == "rejected":
                        self.rejections.add((student_code, project_code))
                        student.proposal_index += 1
                    # Se "waiting" (logica customizada), continua para próxima preferência
                
                else:
                    # Nota insuficiente
                    self.rejections.add((student_code, project_code))
                    student.proposal_index += 1

            # Se aluno não foi aceito em nenhum projeto nesta rodada,
            # verifica se ele ainda tem opções. Se tiver, volta para a fila de livres.
            if student_code not in self.temporary_matching:
                if student.proposal_index < len(student.preferences):
                    self.free_students.append(student_code)
                else:
                    # Aluno não conseguiu vaga em nenhuma preferência (esgotou lista)
                    pass

            if collect_history:
                new_proposals = self.proposals_history[start_proposals_len:]
                proposals_edges = [(f"S{str(p["student"])}", f"P{str(p["project"])}") for p in new_proposals if p.get("type") == "active"]
                temp_matches_edges = [(f"S{str(s)}", f"P{str(p)}") for s, p in self.temporary_matching.items()]
                rejections_edges = [(f"S{str(s)}", f"P{str(p)}") for s, p in self.rejections]
                final_matching_map = {f"S{str(s)}": f"P{str(p)}" for s, p in self.temporary_matching.items()}

                matching_data.append({
                    "iteration": iteration,
                    "proposals": proposals_edges,
                    "temporary_matches": temp_matches_edges,
                    "rejections": rejections_edges,
                    "final_matching": final_matching_map
                })

            iteration += 1

        print(f"Algoritmo (Student-Optimal | Random={random_order}) convergiu em {iteration} iterações")
        self._finalize_matching()

        if collect_history:
            final_temp = {f"S{str(s)}": f"P{str(p)}" for s, p in self.temporary_matching.items()}
            matching_data.append({
                "iteration": iteration,
                "proposals": [(f"S{str(p["student"])}", f"P{str(p["project"])}") for p in self.proposals_history if p.get("type")=="active"],
                "temporary_matches": [(f"S{str(s)}", f"P{str(p)}") for s, p in self.temporary_matching.items()],
                "rejections": [(f"S{str(s)}", f"P{str(p)}") for s, p in self.rejections],
                "final_matching": final_temp
            })
            return self.matching, matching_data

        return self.matching

    # =========================================================================
    # VARIAÇÃO 2: PROJECT-OPTIMAL (Nova implementação)
    # =========================================================================
    def _match_project_optimal(self, random_order, max_iterations, collect_history=False):
        """
        Nesta versão, os PROJETOS propõem vagas aos alunos.
        """
        iteration = 0
        matching_data = []
        
        # Função auxiliar para identificar projetos que ainda querem propor:
        # 1. Ainda têm vagas livres.
        # 2. Ainda têm alunos na lista de preferência para convidar.
        def get_active_projects():
            active = []
            for p in self.projects.values():
                if len(self.matching[p.code]) < p.max_students and p.proposal_index < len(p.preference_list):
                    active.append(p.code)
            return active

        active_projects = get_active_projects()

        while active_projects and iteration < max_iterations:
            start_proposals_len = len(self.proposals_history)

            # Seleção do Projeto Proponente
            if random_order:
                project_code = random.choice(active_projects)
            else:
                project_code = active_projects[0]

            project = self.projects[project_code]

            # Projeto pega o próximo aluno da sua lista de preferência (gerada baseada em Nota)
            student_code = project.preference_list[project.proposal_index]
            project.proposal_index += 1 # Avança para não propor pro mesmo aluno de novo
            
            student = self.students[student_code]

            # Registra proposta para visualização
            self.proposals_history.append({
                'student': student_code,
                'project': project_code,
                'type': 'active' # Projeto propondo ativamente
            })

            current_matched_project = self.temporary_matching.get(student_code)

            # --- Cenário 1: Aluno está livre ---
            if current_matched_project is None:
                # Aluno aceita (temporariamente)
                self._accept_student_logic(student_code, project_code)
            
            # --- Cenário 2: Aluno já tem um projeto, decide se troca ---
            else:
                # Aluno verifica se prefere o NOVO projeto ao ATUAL
                if self._does_student_prefer(student, new_project=project_code, current_project=current_matched_project):
                    # Aluno aceita o novo e rejeita o antigo
                    
                    # Remove do antigo
                    self.matching[current_matched_project].remove(student_code)
                    del self.temporary_matching[student_code]
                    self.rejections.add((student_code, current_matched_project)) # Rejeição tardia

                    # Adiciona no novo
                    self._accept_student_logic(student_code, project_code)
                else:
                    # Aluno rejeita a proposta do projeto atual
                    self.rejections.add((student_code, project_code))

            # Atualiza lista de projetos ativos para a próxima iteração
            active_projects = get_active_projects()

            if collect_history:
                new_proposals = self.proposals_history[start_proposals_len:]
                proposals_edges = [(f"S{str(p["student"])}", f"P{str(p["project"])}") for p in new_proposals if p.get("type") == "active"]
                temp_matches_edges = [(f"S{str(s)}", f"P{str(p)}") for s, p in self.temporary_matching.items()]
                rejections_edges = [(f"S{str(s)}", f"P{str(p)}") for s, p in self.rejections]
                final_matching_map = {f"S{str(s)}": f"P{str(p)}" for s, p in self.temporary_matching.items()}

                matching_data.append({
                    "iteration": iteration,
                    "proposals": proposals_edges,
                    "temporary_matches": temp_matches_edges,
                    "rejections": rejections_edges,
                    "final_matching": final_matching_map
                })

            iteration += 1

        print(f"Algoritmo (Project-Optimal | Random={random_order}) convergiu em {iteration} iterações")
        self._finalize_matching()

        if collect_history:
            final_temp = {f"S{str(s)}": f"P{str(p)}" for s, p in self.temporary_matching.items()}
            matching_data.append({
                "iteration": iteration,
                "proposals": [(f"S{str(p["student"])}", f"P{str(p["project"])}") for p in self.proposals_history if p.get("type")=="active"],
                "temporary_matches": [(f"S{str(s)}", f"P{str(p)}") for s, p in self.temporary_matching.items()],
                "rejections": [(f"S{str(s)}", f"P{str(p)}") for s, p in self.rejections],
                "final_matching": final_temp
            })
            return self.matching, matching_data

        return self.matching

    # =========================================================================
    # MÉTODOS AUXILIARES (Originais + Novos Helpers)
    # =========================================================================

    def _make_proposal(self, student_code, project_code):
        # Lógica original usada pelo Student-Optimal
        project = self.projects[project_code]
        current_students = self.matching[project_code]

        # Registra proposta para visualização
        self.proposals_history.append({
            'student': student_code,
            'project': project_code,
            'type': 'active'
        })

        # Verifica se projeto pode aceitar mais alunos
        if len(current_students) < project.max_students:
            # Aceita aluno diretamente
            self._accept_student(student_code, project_code)
            return "accepted"
        else:
            # Verifica se este aluno é melhor que algum atual
            worst_student_code = self._find_worst_student(project_code, current_students)

            if worst_student_code and self._is_better_student(student_code, worst_student_code, project_code):
                # Substitui o pior aluno
                self._replace_student(student_code, worst_student_code, project_code)
                return "accepted"
            else:
                # Rejeita aluno
                return "rejected"

    def _find_worst_student(self, project_code, student_codes):
        if not student_codes:
            return None

        project = self.projects[project_code]
        # Cria mapa de indice para performance
        pref_index = {code: idx for idx, code in enumerate(project.preference_list)}

        # Ordena alunos pelos índices (maior índice = pior preferência)
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

        return pos1 < pos2 # Menor índice é melhor

    def _accept_student(self, student_code, project_code):
        # Usado pelo Student-Optimal (mantido original)
        self.temporary_matching[student_code] = project_code
        self.matching[project_code].append(student_code)

        self.proposals_history.append({
            'student': student_code,
            'project': project_code,
            'type': 'temporary'
        })

    def _accept_student_logic(self, student_code, project_code):
        # Helper simplificado para o Project-Optimal (evita duplicação de logica de append)
        self.temporary_matching[student_code] = project_code
        self.matching[project_code].append(student_code)
        
        # Histórico
        self.proposals_history.append({
            'student': student_code,
            'project': project_code,
            'type': 'temporary'
        })

    def _replace_student(self, new_student_code, old_student_code, project_code):
        # Usado pelo Student-Optimal
        self.matching[project_code].remove(old_student_code)
        if old_student_code in self.temporary_matching:
            del self.temporary_matching[old_student_code]

        # Devolve o aluno expulso para a lista de livres (se estiver rodando student optimal)
        if self.free_students is not None:
            self.free_students.append(old_student_code)
        
        self.students[old_student_code].proposal_index += 1

        self._accept_student(new_student_code, project_code)
        self.rejections.add((old_student_code, project_code))

    def _does_student_prefer(self, student, new_project, current_project):
        """Helper novo para o Project-Optimal: verifica se aluno prefere o novo projeto."""
        if new_project not in student.preferences:
            return False # Não está na lista de desejo, recusa
        
        if current_project not in student.preferences:
            return True # O atual nem estava na lista (caso raro), então aceita o novo

        # Compara índices (menor índice = maior preferência)
        return student.preferences.index(new_project) < student.preferences.index(current_project)

    def _finalize_matching(self):
        # Remove projetos que não atingiram o mínimo de alunos
        for project_code, students in list(self.matching.items()):
            if len(students) < self.projects[project_code].min_students:
                # Libera alunos desses projetos (projeto cancelado por falta de quorum)
                for student_code in students:
                    if student_code in self.temporary_matching:
                        del self.temporary_matching[student_code]
                    self.rejections.add((student_code, project_code)) # Marca rejeição final
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
            'matching_rate': total_students_matched / len(self.students) if len(self.students) > 0 else 0
        }

        return stats
