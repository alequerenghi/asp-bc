import gurobipy as gp
from gurobipy import GRB
import numpy as np
from numpy.typing import NDArray
from aspbc.utility import _array_from_var


class BinPackingProblem:

    def __init__(self, job_costs: NDArray[np.float64],
                 battery_capacity: float,
                 number_of_charges: int = 0
                 ) -> None:
        self.R = number_of_charges if number_of_charges != 0 else job_costs.shape[0]
        self.e = job_costs
        self.b = battery_capacity

    def solve(self, env=None) -> 'BinPackingProblem':
        J = self.e.shape[0]
        m = gp.Model("BPP", env=env)

        # Binary variables!!!!
        gamma = m.addMVar(self.R, vtype=GRB.BINARY)  # numero di bin
        # job j asseganto a bin r
        chi = m.addMVar((self.R, J), vtype=GRB.BINARY)

        # Objective
        # uguale a m.setObjective(gamma.sum(), GRB.MINIMIZE)
        m.setObjective(gamma @ np.ones(self.R), GRB.MINIMIZE)

        # Constraints!!!
        # Assign each job to a charging operation aka ogni job usato una ed un'unica volta
        # uguale a m.addConstr(chi.sum(axis=0) == 1)
        m.addConstr(np.ones(self.R) @ chi == 1)
        # If charge used, then sum of jobs must be lower than capacity aka non riempire i bin più della loro capacità
        m.addConstr((chi @ self.e) <= (self.b * gamma))
        m.addConstrs(gamma[r] <= gamma[r-1] for r in range(1, self.R))

        m.optimize()

        self.gamma = _array_from_var(gamma)
        self.chi = _array_from_var(chi)
        self.zeta = m.ObjVal
        self.time = m.Runtime

        return self
