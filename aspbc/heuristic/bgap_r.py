import gurobipy as gp
from gurobipy import GRB
import numpy as np
from .bpp import BinPackingProblem
from numpy.typing import NDArray

from aspbc.utility import _array_from_var


class BGAPChargeOperations:
    def __init__(self, M: int, processing_times: NDArray[np.int64], gamma: NDArray[np.bool_], chi: NDArray[np.bool_], charge_duration: float, R=0) -> None:
        self.M = M
        self.d = processing_times
        self.gamma = gamma
        self.chi = chi
        self.t = charge_duration
        self.R = R if R != 0 else processing_times.shape[0]

    @classmethod
    def from_bpp(cls, bpp: BinPackingProblem, M: int, processing_times: np.ndarray, charge_duration: float) -> 'BGAPChargeOperations':
        gamma = bpp.gamma  # (J, )
        chi = bpp.chi      # (R, J)
        bgap_r = cls(M, processing_times, gamma, chi, charge_duration, bpp.R)
        return bgap_r

    def solve(self, env=None) -> 'BGAPChargeOperations':
        m = gp.Model("bgap_r", env)

        R_bar = np.where(self.gamma == 1)[0]
        D = (self.chi @ self.d)[R_bar] + self.t

        # VARIABLES!!!!
        theta = m.addMVar(shape=(R_bar.shape[0], self.M), vtype=GRB.BINARY)
        cmax = m.addVar()

        # OBJECTIVE!!!
        m.setObjective(cmax, GRB.MINIMIZE)

        # CONSTRAINTS!!!
        m.addConstr(cmax >= (D @ theta)-self.t)
        # uguale a m.addConstr(theta.sum(axis=1) == 1)
        m.addConstr(theta @ np.ones(self.M) == 1)

        m.optimize()

        self.theta = np.zeros((self.R, self.M), dtype=bool)
        self.theta[R_bar] = _array_from_var(theta)
        self.z = m.ObjVal
        self.time = m.Runtime

        return self
