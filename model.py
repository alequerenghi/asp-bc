import numpy as np
import os
from numpy.typing import NDArray
import gurobipy as gb
from gurobipy import GRB, quicksum
from bgap_c import BGAPConstrained
from bgap_r import BGAPChargeOperations
from bpp import BinPackingProblem
from local_search import LocalSearch
from parser import parse_file
from csv import writer


class ASPBC:
    def __init__(self,
                 agv_number: int,
                 job_durations: NDArray[np.int64],
                 battery_capacity: float,
                 charge_duration: float,
                 energy_requirements: NDArray[np.float64],
                 charging_operations_number: int = 0
                 ) -> None:
        self.M = agv_number
        self.d = job_durations
        self.b = battery_capacity
        self.t = charge_duration
        self.e = energy_requirements
        self.R = energy_requirements.shape[0] if charging_operations_number == 0 else charging_operations_number

    def solve(self, env=None) -> "ASPBC":
        J = self.e.shape[0]
        aspbc = gb.Model("ASP-BC", env=env)

        x = aspbc.addVars([(j, m) for j in range(J)
                          for m in range(self.M)], vtype=GRB.BINARY)
        q = aspbc.addVars([(r, m) for r in range(self.R)
                          for m in range(self.M)], vtype=GRB.BINARY)
        y = aspbc.addVars([(j, r, m) for j in range(J) for r in range(
            self.R) for m in range(self.M)], vtype=GRB.BINARY)

        cmax = aspbc.addVar(vtype=GRB.CONTINUOUS, lb=0.0)

        aspbc.setObjective(cmax, GRB.MINIMIZE)

        aspbc.addConstrs(cmax >= quicksum(self.d[j] * x[j, m] for j in range(J)) + quicksum(self.t * q[r, m] for r in range(1, self.R))
                         for m in range(self.M)
                         )
        aspbc.addConstrs(quicksum(x[j, m] for m in range(self.M)) == 1
                         for j in range(J)
                         )
        aspbc.addConstrs(quicksum(y[j, r, m] for r in range(self.R)) == x[j, m]
                         for j in range(J)
                         for m in range(self.M)
                         )
        aspbc.addConstrs(2 * y[j, r, m] <= x[j, m] + q[r, m]
                         for j in range(J)
                         for r in range(self.R)
                         for m in range(self.M)
                         )
        aspbc.addConstrs(quicksum(self.e[j] * y[j, r, m] for j in range(J)) <= self.b
                         for r in range(self.R)
                         for m in range(self.M)
                         )
        aspbc.addConstrs(q[r, m] <= q[r-1, m]
                         for r in range(1, self.R)
                         for m in range(self.M)
                         )
        aspbc.addConstrs(q[0, m] == 1
                         for m in range(self.M)
                         )
        aspbc.optimize()

        self.aspbc = aspbc

        return self

    def solve_matheuristic(self, env=None):
        bpp = BinPackingProblem(self.e, self.b)
        bpp.solve(env)
        self.time_1 = bpp.time
        self.lb = bpp.get_lower_bound(self.M, self.t, self.d)
        ls = None
        if bpp.zeta <= self.M:
            bgap = BGAPConstrained(self.M, self.e, self.d, self.b)
            bgap.solve(env)
            ls = LocalSearch.from_constrained(bgap, self.t)
        else:
            bgap = BGAPChargeOperations.from_bpp(bpp, self.M, self.d, self.t)
            bgap.solve(env)
            ls = LocalSearch.from_charge(bgap, self.e, self.b)
        self.time_2 = bgap.time
        self.initial_ub = bgap.z
        ls.solve()
        self.ub = ls.cmax
        self.time_3 = ls.time
        return self

    @classmethod
    def create_from_file(cls, file_name: str) -> "ASPBC":
        return cls(*parse_file(
            file_name))
