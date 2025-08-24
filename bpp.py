import gurobipy as gp
from gurobipy import GRB
import numpy as np
from math import ceil


class BinPackingProblem:

    def __init__(self, energy_requirement: np.ndarray, battery_limit: float, J: int = 0) -> None:
        self.J = energy_requirement.shape[0] if J == 0 else J  # Number of jobs
        self.R = self.J
        self.e = energy_requirement  # energy requirements
        self.b = battery_limit  # battery limit

    def solve(self) -> 'BinPackingProblem':
        m = gp.Model("bpp")

        # Binary variables!!!!
        # charging operations
        gamma = m.addMVar(shape=self.J, vtype=GRB.BINARY)
        chi = m.addMVar(shape=(self.R, self.J),
                        vtype=GRB.BINARY)  # transfer jobs

        # Objective
        # uguale a m.setObjective(gamma.sum(), GRB.MINIMIZE)
        m.setObjective(gamma @ np.ones(self.J), GRB.MINIMIZE)

        # Constraints!!!
        # Assign each job to a charging operation
        # uguale a m.addConstr(chi.sum(axis=0) == 1)
        m.addConstr(np.ones(self.R) @ chi == 1)
        # If charge used, then sum of jobs is lower than capacity
        m.addConstr((chi @ self.e) <= (self.b*gamma))
        m.addConstrs(gamma[r] <= gamma[r-1]
                     for r in range(1, self.J))  # Symmetry breaking

        m.setParam('OutputFlag', 0)
        m.optimize()

        self.gamma = gamma
        self.chi = chi
        self.zeta = m.ObjVal

        return self

    def get_lower_bound(self, M: int, t: float, d: np.ndarray) -> float:
        first = ceil((max(0, self.zeta-M)*t+d.sum())/M)
        second = ceil(max(0, self.zeta-M)/M)*t
        return max(first, second)


# e = np.array([50, 3, 48, 53, 53, 4, 3, 41, 23, 20, 52, 49])
# c = 100
# n = 12

# bpp = BinPackingProblem(energy_requirement=e, battery_limit=c)
# bpp.solve()
# print(bpp.m.ObjVal)
