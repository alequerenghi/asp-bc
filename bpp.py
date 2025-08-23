import gurobipy as gp
from gurobipy import GRB
import numpy as np
from math import ceil


class BinPackingProblem:

    def __init__(self, J: int, e: np.ndarray, b: float) -> None:
        self.J = J  # Number of jobs
        self.e = e  # energy requirements
        self.b = b  # battery limit
        self.m = None

    def solve(self) -> 'BinPackingProblem':
        m = gp.Model("bpp")

        # Binary variables!!!!
        # charging operations
        gamma = m.addMVar(shape=self.J, vtype=GRB.BINARY)
        chi = m.addMVar(shape=(self.J, self.J),
                        vtype=GRB.BINARY)  # transfer jobs

        # Objective
        m.setObjective(gamma.sum(), GRB.MINIMIZE)

        # Constraints!!!
        # Assign each job to a charging operation
        m.addConstr(chi.sum(axis=0) == 1)
        # If charge used, then sum of jobs is lower than capacity
        m.addConstr((chi @ self.e) <= (self.b*gamma))
        m.addConstrs(gamma[r] <= gamma[r-1]
                     for r in range(1, self.J))  # Symmetry breaking
        m.optimize()
        self.m = m

        return self

    def get_lower_bound(self, M: int, t: float, d: np.ndarray) -> float:
        if self.m is not None:
            first = ceil((max(0, self.m.ObjVal-M)*t+d.sum())/M)
            second = ceil(max(0, self.m.ObjVal-M)/M)*t
            return max(first, second)
        else:
            raise RuntimeError("Forgot to solve first!!!")
