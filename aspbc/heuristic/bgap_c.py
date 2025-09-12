import gurobipy as gp
from gurobipy import GRB
import numpy as np
from aspbc.utility import _array_from_var
from numpy.typing import NDArray

class BGAPConstrained:
    def __init__(self, 
                 fleet_size: int, 
                 energy_job_costs: NDArray[np.float64], 
                 job_durations: NDArray[np.int64], 
                 battery_capacity: float
                 ) -> None:
        self.M = fleet_size
        self.e = energy_job_costs
        self.d = job_durations
        self.b = battery_capacity

    def solve(self, env=None) -> 'BGAPConstrained':
        J = self.e.shape[0]
        m = gp.Model("BGAP_C", env)

        # VARIABLES!!!!
        x = m.addMVar((J, self.M), vtype=GRB.BINARY)
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
