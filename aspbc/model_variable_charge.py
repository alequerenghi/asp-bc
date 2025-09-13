from gurobipy import GRB
import numpy as np
import gurobipy as gb
from numpy.typing import NDArray
from aspbc.parser import parse_file
from math import ceil
from .heuristic import BinPackingProblem, BGAPConstrained, BGAPChargeOperations_VC, LocalSearch_VC

class ASPBC_VC:
    def __init__(self, agv_number: int, 
                 job_durations: NDArray[np.int64],
                 battery_capacity: float, 
                 charge_duration: float, 
                 energy_requirements: NDArray[np.float64],
                 tau = 1.0,
                 charging_operations_number = 0
                 ) -> None:
        self.M = agv_number
        self.d = job_durations
        self.b = battery_capacity
        self.e = energy_requirements
        self.R = energy_requirements.shape[0] if charging_operations_number == 0 else charging_operations_number
        self.tau = tau

    @classmethod
    def create_from_file(cls, file_name: str) -> "ASPBC_VC":
        return cls(*parse_file(file_name))

    def solve(self, env=None):
        J = self.e.shape[0]

        model = gb.Model("ASPBC-VC", env=env)
        x = model.addMVar((J, self.M), vtype=GRB.BINARY)
        q = model.addMVar((self.R, self.M), vtype=GRB.BINARY)
        y = model.addMVar((J, self.R, self.M), vtype=GRB.BINARY)
        w = model.addMVar((J, self.R-1, self.M), vtype=GRB.BINARY)
        cmax = model.addVar()

        model.setObjective(cmax, GRB.MINIMIZE)

        model.addConstr(w <= y[:, :-1])
        model.addConstr(w <= q[None, 1:, :])
        model.addConstr(w >= y[:, :-1] + q[None, 1:, :]-1)
        job_part = self.d @ x
        wsum = w.sum(axis=1)
        energy_part = gb.quicksum(self.e[i] * wsum[i] for i in range(J))
        model.addConstr(cmax >= job_part + energy_part * self.tau)
        model.addConstr(x @ np.ones(self.M) == 1)
        model.addConstr(y.sum(axis=1) == x)
        model.addConstr(2 * y <= x[:, None, :] + q[None, :, :])
        model.addConstr((self.e[None, :, None] * y).sum(axis=0) <= self.b)
        model.addConstr(q[1:] <= q[:-1])
        model.addConstr(q[0] == 1)
        model.optimize()

        self.ub = model.ObjBound
        self.time = model.Runtime
        self.lb = self.get_lower_bound()
        self.gap = model.MIPGap

        return self
    
    def solve_matheuristic(self, env=None):
        bpp = BinPackingProblem(self.e, self.b)
        bpp.solve(env)
        self.time = bpp.time

        local_search = None
        # se numero ricariche necessarie <= numero di AGV
        if bpp.zeta <= self.M:
            bgap = BGAPConstrained(self.M, self.e, self.d, self.b)
            bgap.solve(env)
            local_search = LocalSearch_VC.from_constrained(bgap, self.tau, self.R)
        else:
            bgap = BGAPChargeOperations_VC.from_bpp(bpp, self.M, self.d, self.tau)
            bgap.solve(env)
            local_search = LocalSearch_VC.from_charge(bgap, self.e, self.b)

        self.time += bgap.time

        local_search.solve()

        self.ub = local_search.cmax
        self.time += local_search.time
        self.lb = self.get_lower_bound()
        self.gap = (self.ub - self.lb)/self.lb

        return self
    
    def get_lower_bound(self) -> int:
        return ceil(np.sum(self.d + self.tau * self.e) / self.M - self.tau * self.b)