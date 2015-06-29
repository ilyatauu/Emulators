class ScheduleResult(object):
    def __init__(self):
        self.feasible = None
        self.optimal = None
        self.objective_value = None
        self.total_penalty = None
        self.total_tardiness = None
        self.jobs_info = []
        self.total_solve_time = None
        self.relative_gap = None
        self.model_build_time = None
        self.model_solution_time = None

class ScheduledJobInfo(object):
    def __init__(self):
        self.job_id = None
        self.start_time = None
        self.finish_time = None
        self.first_board = None
        self.finish_board = None
        self.tardiness = None

class JobInfo(object):
    def __init__(self):
        self.job_id = None
        self.processtime = None
        self.duedate = None
        self.size = None
        self.readytime = None

class EmulatorsData(object):
    def __init__(self):
        self.jobs_info = []
        self.boards_number = None

class FormulationModel(object):
    def __init__(self):
        self.cplex_class = None
        self.vars_map = None
        self.model_build_time = None
        self.solve_time = None
