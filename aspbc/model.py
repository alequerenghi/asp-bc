import numpy as np
from numpy.typing import NDArray
import gurobipy as gb
from gurobipy import GRB, quicksum
from .heuristic import BinPackingProblem, BGAPConstrained, BGAPChargeOperations, LocalSearch
from aspbc.parser import parse_file
from math import ceil

class ASPBC:
    def __init__(self,
                 fleet_size: int,
                 job_durations: NDArray[np.int64],
                 battery_capacity: float,
                 charge_duration: float,
                 energy_job_costs: NDArray[np.float64],
                 charging_operations_number: int = 0
                 ) -> None:
        self.M = fleet_size
        self.d = job_durations
        self.b = battery_capacity
        self.t = charge_duration
        self.e = energy_job_costs
        self.R = energy_job_costs.shape[0] if charging_operations_number == 0 else charging_operations_number

    @classmethod
    def create_from_file(cls, file_name: str) -> "ASPBC":
        return cls(*parse_file(file_name))

    def solve(self, env=None) -> 'ASPBC':
        J = self.e.shape[0]
        aspbc = gb.Model("ASP-BC", env=env)

        x = aspbc.addVars(J, self.M, vtype=GRB.BINARY)
        q = aspbc.addVars(self.R, self.M, vtype=GRB.BINARY)
        y = aspbc.addVars(J, self.R, self.M, vtype=GRB.BINARY)
        cmax = aspbc.addVar()

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
        self.lb = self.get_bpp_lower_bound(bpp)

        local_search = None
        # se numero ricariche necessarie <= numero di AGV
        if bpp.zeta <= self.M: 
            bgap = BGAPConstrained(self.M, self.e, self.d, self.b)
            bgap.solve(env)
            local_search = LocalSearch.from_constrained(bgap, self.t, self.R)
        else:
            bgap = BGAPChargeOperations.from_bpp(bpp, self.M, self.d, self.t)
            bgap.solve(env)
            local_search = LocalSearch.from_charge(bgap, self.e, self.b)

        self.time_2 = bgap.time
        self.initial_ub = bgap.z # l'upper bound iniziale è l'ottimo del BGAP

        local_search.solve()
        self.ub = local_search.cmax
        self.time_3 = local_search.time

        return self
    
    def get_bpp_lower_bound(self, bpp: BinPackingProblem) -> float:
        first = ceil((max(0, bpp.zeta - self.M) * self.t + self.d.sum()) / self.M)
        second = ceil(max(0, bpp.zeta - self.M) / self.M) * self.t
        return max(first, second)
