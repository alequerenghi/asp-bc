import gurobipy as gp
from gurobipy import GRB
import numpy as np


class BGAPConstrained:
    def __init__(self, M: int, energy_requirements: np.ndarray, processing_times: np.ndarray, battery_capacity: float, J: int = 0) -> None:
        self.M = M
        self.e = energy_requirements
        self.d = processing_times
        self.b = battery_capacity
        self.J = energy_requirements.shape[0] if J == 0 else J

    def solve(self) -> 'BGAPConstrained':
        m = gp.Model("bgap_c")

        # VARIABLES!!!!
        x = m.addMVar(shape=(self.M, self.J), vtype=GRB.BINARY)
        cmax = m.addVar()

        # OBJECTIVE!!!
        m.setObjective(cmax, GRB.MINIMIZE)

        # CONSTRAINTS!!!
        m.addConstr(cmax >= self.d @ x)
        m.addConstr(x.sum(axis=0) == 1)
        m.addConstr((x @ self.e) <= self.b)

        m.setParam('OutputFlag', 0)
        m.optimize()

        self.m = m
        return self
