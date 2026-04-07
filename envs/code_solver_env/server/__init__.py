"""Server module for Code Solver Environment"""

from .code_solver_environment import CodeSolverEnvironment
from .problems import SOLVE_TASKS, REVIEW_TASKS, DEBUG_TASKS

# Backwards compatibility: PROBLEMS = all tasks
PROBLEMS = SOLVE_TASKS + REVIEW_TASKS + DEBUG_TASKS

__all__ = ["CodeSolverEnvironment", "PROBLEMS", "SOLVE_TASKS", "REVIEW_TASKS", "DEBUG_TASKS"]
