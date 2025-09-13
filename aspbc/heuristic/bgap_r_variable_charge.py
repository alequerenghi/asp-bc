import gurobipy as gp
from gurobipy import GRB
import numpy as np
from .bpp import BinPackingProblem
from numpy.typing import NDArray
from aspbc.utility import _array_from_var

class BGAPChargeOperations_VC:
    def __init__(self,
                 fleet_size: int,
                 job_durations: NDArray[np.int64],
                 energy_job_costs: NDArray[np.float64],
                 gamma: NDArray[np.bool_],
                 chi: NDArray[np.bool_],
                 time_per_charge_unit: float,
                 charging_operations_number=0
                 ) -> None:
        self.M = fleet_size
        self.d = job_durations
        self.e = energy_job_costs
        self.gamma = gamma
        self.chi = chi
        self.tau = time_per_charge_unit
        self.R = charging_operations_number if charging_operations_number != 0 else job_durations.shape[0]

    @classmethod
    def from_bpp(cls,
                 bpp: BinPackingProblem,
                 fleet_size: int,
                 job_durations: np.ndarray,
                 time_per_charge_unit: float
                 ) -> 'BGAPChargeOperations_VC':
        gamma = bpp.gamma  # (J, )
        chi = bpp.chi      # (R, J)
        bgap_r = cls(fleet_size, job_durations, bpp.e, gamma, chi, time_per_charge_unit, bpp.R)
        return bgap_r

    def solve(self, env=None) -> 'BGAPChargeOperations_VC':
        m = gp.Model("BGAP_R", env)

        q = m.addMVar((self.R, self.M))

        # VARIABLES!!!!
        theta = m.addMVar((self.R, self.M), vtype=GRB.BINARY)
        cmax = m.addVar()

        # OBJECTIVE!!!
        m.setObjective(cmax, GRB.MINIMIZE)
        # CONSTRAINTS!!!
        m.addConstr(q[:-1] >= theta[1:])
        m.addConstr(q[-1] == 0)

        job_part = self.chi @ self.d
        energy_part = self.tau * ((self.e @ self.chi)[:,None] * q * theta).sum()
        m.addConstr(cmax >= job_part + energy_part)
        # uguale a m.addConstr(theta.sum(axis=1) == 1)
        m.addConstr(theta @ np.ones(self.M) == 1)

        m.optimize()

        self.theta = _array_from_var(theta)
        self.z = m.ObjVal
        self.time = m.Runtime

        return self
