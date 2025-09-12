import gurobipy as gp
from gurobipy import GRB
import numpy as np
from .bpp import BinPackingProblem
from numpy.typing import NDArray
from utility import _array_from_var


class BGAPChargeOperations:
    def __init__(self,
                 fleet_size: int,
                 job_durations: NDArray[np.int64],
                 gamma: NDArray[np.bool_],
                 chi: NDArray[np.bool_],
                 charge_duration: float,
                 charging_operations_number=0
                 ) -> None:
        self.M = fleet_size
        self.d = job_durations
        self.gamma = gamma
        self.chi = chi
        self.t = charge_duration
        self.R = charging_operations_number if charging_operations_number != 0 else job_durations.shape[
            0]

    @classmethod
    def from_bpp(cls,
                 bpp: BinPackingProblem,
                 fleet_size: int,
                 job_durations: np.ndarray,
                 charge_duration: float
                 ) -> 'BGAPChargeOperations':
        gamma = bpp.gamma  # (J, )
        chi = bpp.chi      # (R, J)
        bgap_r = cls(fleet_size, job_durations, gamma,
                     chi, charge_duration, bpp.R)
        return bgap_r

    def solve(self, env=None) -> 'BGAPChargeOperations':
        m = gp.Model("BGAP_R", env)

        R_bar = np.where(self.gamma == 1)[0]
        # per ogni ricarica, il tempo di esecuzione dei jobs
        D = (self.chi @ self.d)[R_bar] + self.t

        # VARIABLES!!!!
        theta = m.addMVar((R_bar.shape[0], self.M), vtype=GRB.BINARY)
        cmax = m.addVar()

        # OBJECTIVE!!!
        m.setObjective(cmax, GRB.MINIMIZE)

        # CONSTRAINTS!!!
        m.addConstr(cmax >= (D @ theta) - self.t)
        # uguale a m.addConstr(theta.sum(axis=1) == 1)
        m.addConstr(theta @ np.ones(self.M) == 1)

        m.optimize()

        self.theta = np.zeros((self.R, self.M), dtype=bool)
        self.theta[R_bar] = _array_from_var(theta)
        self.z = m.ObjVal
        self.time = m.Runtime

        return self
