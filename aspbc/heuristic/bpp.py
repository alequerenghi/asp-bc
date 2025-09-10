import gurobipy as gp
from gurobipy import GRB
import numpy as np
from math import ceil
from numpy.typing import NDArray

from aspbc.utility import _array_from_var


class BinPackingProblem:

    def __init__(self, energy_requirement: NDArray[np.float64], battery_limit: float, R: int = 0) -> None:
        self.R = R if R != 0 else energy_requirement.shape[0]
        self.e = energy_requirement  # energy requirements
        self.b = battery_limit  # battery limit

    def solve(self, env=None) -> 'BinPackingProblem':
        J = self.e.shape[0]
        m = gp.Model("bpp", env=env)

        # Binary variables!!!!
        # charging operations
        gamma = m.addMVar(shape=self.R, vtype=GRB.BINARY)
        chi = m.addMVar(shape=(self.R, J),
                        vtype=GRB.BINARY)  # transfer jobs

        # Objective
        # uguale a m.setObjective(gamma.sum(), GRB.MINIMIZE)
        m.setObjective(gamma @ np.ones(self.R), GRB.MINIMIZE)

        # Constraints!!!
        # Assign each job to a charging operation
        # uguale a m.addConstr(chi.sum(axis=0) == 1)
        m.addConstr(np.ones(self.R) @ chi == 1)
        # If charge used, then sum of jobs is lower than capacity
        m.addConstr((chi @ self.e) <= (self.b*gamma))
        m.addConstrs(gamma[r] <= gamma[r-1]
                     for r in range(1, self.R))  # Symmetry breaking

        m.optimize()

        self.gamma = _array_from_var(gamma)
        self.chi = _array_from_var(chi)
        self.zeta = m.ObjVal
        self.time = m.Runtime

        return self

    def get_lower_bound(self, M: int, t: float, d: np.ndarray) -> float:
        first = ceil((max(0, self.zeta-M)*t+d.sum())/M)
        second = ceil(max(0, self.zeta-M)/M)*t
        return max(first, second)
