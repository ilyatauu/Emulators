import time
import cplex
def get_feasibility_and_optimality(cplex_solver):
    """
    :param cplex_solver: object of type cplex.Cplex
    :return: A tuple of boolean values (feasible, optimal)
    """
    # if infeasible
    if cplex_solver.solution.get_status() == 103:
        return False, True
    elif cplex_solver.solution.get_status() == 108:
        return False, False
    elif cplex_solver.solution.get_status() == 107:
        return True, False
    elif cplex_solver.solution.get_status() == 101 or cplex_solver.solution.get_status() == 102:
        return True, True

def get_cplex_class(timelimit=1800):
    cplex_class = cplex.Cplex()

    cplex_class.parameters.timelimit.set(timelimit)
    cplex_class.parameters.parallel.set(1)
    cplex_class.parameters.threads.set(4)
    # cplex_class.parameters.read.datacheck.set(1)
    # set node log interval to 10
    cplex_class.parameters.mip.interval.set(10)

    return cplex_class

def get_formulation_builder(formulation_type, problem_type):
    if formulation_type == "guan" and problem_type == "tardy_jobs":
        import guan.tardyjobs
        return guan.tardyjobs.get_formulation
    elif formulation_type == "tbasedw" and problem_type == "tardy_jobs":
        import tbasedw.tardyjobs
        return tbasedw.tardyjobs.get_formulation
    elif formulation_type == "tbasedu" and problem_type == "tardy_jobs":
        import tbasedu.tardyjobs
        return tbasedu.tardyjobs.get_formulation


def get_results_reader(formulation_type):
    if formulation_type == "guan":
        import guan.results_reader
        return guan.results_reader.read
    elif formulation_type == "tbasedw":
        import tbasedw.results_reader
        return tbasedw.results_reader.read
    elif formulation_type == "tbasedu":
        import tbasedu.results_reader
        return tbasedu.results_reader.read


def solve(emulators_data, formulation_builder, results_reader, timelimit=1800, custom_builder_steps=[]):
    start_time = time.time()
    cplex_class = get_cplex_class(timelimit=timelimit)
    formulation_model = formulation_builder(cplex_class, emulators_data)

    for step in custom_builder_steps:
        step(formulation_model)

    # formulation_model.cplex_class.write("formulation.lp")
    start_solve = time.time()
    formulation_model.cplex_class.solve()
    end_solve = time.time()

    formulation_model.solve_time = end_solve - start_solve
    schedule = results_reader(formulation_model, emulators_data)
    end_time = time.time()

    schedule.total_solve_time = end_time - start_time

    return schedule



