import gurobipy as gp
from gurobipy import GRB
import numpy as np
from utility import _array_from_var
from numpy.typing import NDArray


class BGAPConstrained:
    def __init__(self, M: int, energy_requirements: NDArray[np.float64], processing_times: NDArray[np.int64], battery_capacity: float) -> None:
        self.M = M
        self.e = energy_requirements
        self.d = processing_times
        self.b = battery_capacity

    def solve(self, env=None) -> 'BGAPConstrained':
        J = self.e.shape[0]
        m = gp.Model("bgap_c", env)

        # VARIABLES!!!!
        x = m.addMVar(shape=(J, self.M), vtype=GRB.BINARY)
        cmax = m.addVar()

        # OBJECTIVE!!!
        m.setObjective(cmax, GRB.MINIMIZE)

        # CONSTRAINTS!!!
        m.addConstr(cmax >= self.d @ x)
        # uguale a m.addConstr(x.sum(axis=0) == 1)
        m.addConstr(x @ np.ones(self.M) == 1)
        m.addConstr(self.e @ x <= self.b)

        m.optimize()

        self.x = _array_from_var(x)
        self.z = m.ObjVal
        self.time = m.Runtime

        return self
