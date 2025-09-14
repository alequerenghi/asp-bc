import time
import numpy as np
from .bgap_c import BGAPConstrained
from .bgap_r_variable_charge import BGAPChargeOperations_VC
from numpy.typing import NDArray
# x = transfer job j performed by m
# q = charge jobe r performed by m
# y = transfer job j performed by m after charge job r

# gamma = charge operation r performed


# x = chi.T @ theta (J, M)
# y = np.stack([np.outer(chi[r], theta[r]) for r in range(R)], axis = 0) (R, J, M)

class LocalSearch_VC:
    def __init__(self,
                 x: NDArray[np.bool_],
                 y: NDArray[np.bool_],
                 q: NDArray[np.bool_],
                 cmax: float,
                 job_durations: NDArray[np.int64],
                 energy_job_costs: NDArray[np.float64],
                 time_per_charge_unit: float,
                 battery_capacity: float
                 ) -> None:
        self.x = x  # (J, M)
        self.y = y  # (R, J, M)
        self.q = q  # (R, M)
        self.cmax = cmax
        self.d = job_durations
        self.tau = time_per_charge_unit
        self.e = energy_job_costs
        self.b = battery_capacity

    @classmethod
    def from_constrained(cls,
                         bgap: BGAPConstrained,
                         time_per_charge_unit: float,
                         charging_operations_number=0
                         ) -> 'LocalSearch_VC':
        J = bgap.x.shape[0]
        R = charging_operations_number if charging_operations_number != 0 else J
        x = bgap.x
        y = np.zeros((R, J, bgap.M), dtype=bool)
        y[0, :, :] = x
        q = np.zeros((J, bgap.M), dtype=bool)
        q[0, :] = 1
        cmax = bgap.z

        ls = cls(x, y, q, cmax, bgap.d, bgap.e, time_per_charge_unit, bgap.b)
        return ls

    @classmethod
    def from_charge(cls,
                    bgap: BGAPChargeOperations_VC,
                    energy_job_costs: NDArray[np.float64],
                    battery_capacity: float
                    ) -> 'LocalSearch_VC':
        # chi = transfer operation j assigned to charge operation r
        # theta = charge operation r assigned to m
        x = bgap.chi.T @ bgap.theta
        q = np.zeros(bgap.theta.shape, dtype=bool)
        y = np.stack([np.outer(bgap.chi[r], bgap.theta[r])
                     for r in range(bgap.theta.shape[0])], axis=0)
        for m in range(bgap.M):
            rs = np.where(bgap.theta[:, m])[0]
            for i, r in enumerate(rs):
                q[i, m] = 1
                if i != r:
                    y[i] += y[r]
                    y[r] = 0

        ls = cls(x, y, q, bgap.z, bgap.d, energy_job_costs,
                 bgap.tau, battery_capacity)
        return ls

    def solve(self):
        t0 = time.time()
        while True:
            s_star, update = self.iterations()
            if s_star > 0.0:
                self.update_best(update)
            else:
                break
        self.time = time.time() - t0
        return self

    def iterations(self) -> tuple[float, tuple]:
        s_star = (0.0, ())  # saving time
        c_m = self._compute_cm()  # duration for all AGVs
        critical_machines = np.where(c_m == c_m.max())[0]

        for m in critical_machines:
            for r in np.where(self.q[:, m])[0]:
                # iterate jobs of most loaded AGV
                for j in np.where(self.y[r, :, m])[0]:
                    # Find the respective charge job in m1
                    idxs = (m, r, j)
                    s_star = self.save_swap(*idxs, c_m, *s_star)
                    s_star = self.save_remove(*idxs, c_m, *s_star)
                    s_star = self.saving_add(*idxs, c_m, *s_star)
        return s_star

    def _compute_cm(self) -> NDArray[np.float64]:
        # quanto tempo impiega ogni AGV a svolgere il suo lavoro
        first = self.d @ self.x
        second = self.tau * \
            (np.sum((self.e @ self.y)[:-1] * self.q[1:], axis=0))
        return first + second

    def _get_best_two(self, cm: NDArray[np.float64], m1: np.int64) -> tuple[np.int64, np.int64]:
        # precompute best cm-s
        m1_val = cm[m1]
        cm[m1] = -np.inf
        top1 = cm.argmax()  # second best
        top1_val = cm[top1]
        cm[top1] = -np.inf
        top2 = cm.argmax()  # if m2 == top1 use this
        cm[m1] = m1_val
        cm[top1] = top1_val
        return (top1, top2)

    def saving_add(self, m1: np.int64, r1: np.int64, j: np.int64, c_m: NDArray[np.float64], s_star: float, update: tuple) -> tuple[float, tuple]:
        M = self.x.shape[1]
        critical_machines = np.sum(c_m == c_m.max()) > 1
        top1, top2 = self._get_best_two(c_m, m1)
        cond = r1 < self.q[:, m1].sum() - 1
        m1_without_j = c_m[m1] - self.d[j] - cond * self.tau * self.e[j]
        # find another AGV
        for m2 in range(M):
            if m2 == m1:
                continue
            # Find a new charge job in m2
            r2 = self.q[:, m2].sum(initial=1)
            # Consider the cost of doing the job and a new charge
            m2_with_j = c_m[m2] + self.d[j] + \
                self.tau * (self.e @ self.y[r2-1, :, m2])
            if M <= 2 or critical_machines:
                cm_max = 0  # cm più alto che non è ne m1 ne m2
            else:
                cm_max = c_m[top1] if m2 != top1 else c_m[top2]
                # Compute saving
            s_a = max(0, self.cmax - max(m1_without_j, m2_with_j, cm_max))
            # If you save time
            if s_a > s_star:
                s_star = s_a
                update = (m1, r1, j, m2, r2, j)
        return (s_star, update)

    def save_swap(self, m1: np.int64, r1: np.int64, j1: np.int64, c_m: NDArray[np.float64], s_star: float, update: tuple) -> tuple[float, tuple]:
        M = self.x.shape[1]
        top1, top2 = self._get_best_two(c_m, m1)
        critical_machines = np.sum(c_m == c_m.max()) > 1
        # find another agv
        for m2 in range(M):
            if m2 == m1:
                continue
            # iterate charge jobs of m2
            for r2 in np.where(self.q[:, m2] == 1)[0]:
                # iterate jobs of m2 and r2
                for j2 in np.where(self.y[r2, :, m2])[0]:
                    # if both can accept charge
                    charge_left_r1 = self.b - (self.e @ self.y[r1, :, m1])
                    charge_left_r2 = self.b - (self.e @ self.y[r2, :, m2])
                    if charge_left_r1 >= - self.e[j1] + self.e[j2] and charge_left_r2 >= self.e[j1] - self.e[j2]:
                        cond = r1 < self.q[:, m1].sum() - 1
                        cond2 = r2 < self.q[:, m2].sum() - 1
                        m1_new = c_m[m1] - self.d[j1] + self.d[j2] + \
                            self.tau * (- self.e[j1] + self.e[j2]) * cond
                        m2_new = c_m[m2] + self.d[j1] - self.d[j2] - \
                            self.tau * (self.e[j1] - self.e[j2]) * cond2
                        if M <= 2 or critical_machines:
                            cm_max = 0
                        else:
                            cm_max = c_m[top2] if m2 == top1 else c_m[top1]
                        s_s = max(0, self.cmax - max(m1_new, m2_new, cm_max))
                        if s_s > s_star:
                            s_star = s_s
                            update = (m1, r1, j1, m2, r2, j2)
        return (s_star, update)

    def save_remove(self, m1: np.int64, r1: np.int64, j: np.int64, c_m: NDArray[np.float64], s_star: float, update: tuple) -> tuple[float, tuple]:
        M = self.x.shape[1]
        top1, top2 = self._get_best_two(c_m, m1)
        critical_machines = np.sum(c_m == c_m.max()) > 1
        # iterate jobs of m1
        cond = r1 < self.q[:, m1].sum() - 1
        m1_new = c_m[m1] - self.d[j] - cond * self.tau * self.e[j]
        # find new agv
        for m2 in range(M):
            if m2 == m1:
                continue
            # iterate charge jobs of m2
            for r2 in np.where(self.q[:, m2] == 1)[0]:
                # check if you can add this job
                charge_left = self.b - (self.e @ self.y[r2, :, m2])
                if charge_left >= self.e[j]:
                    cond = r2 < self.q[:, m2].sum() - 1
                    m2_new = c_m[m2] + self.d[j] + \
                        cond * self.tau * self.e[j]
                    if M <= 2 or critical_machines:
                        cm_max = 0
                    else:
                        cm_max = c_m[top2] if m2 == top1 else c_m[top1]
                    s_r = max(0, self.cmax-max(m1_new, m2_new, cm_max))
                    if s_r > s_star:
                        s_star = s_r
                        # find the charge job
                        update = (m1, r1, j, m2, r2, j)
        return (s_star, update)

    def update_best(self, update: tuple) -> 'LocalSearch_VC':
        m1, r1, j1, m2, r2, j2 = update

        # can use the same code to update either for add, remove and swap
        self.x[j2, m1] = 1
        self.x[j1, m1] = 0
        self.x[j2, m2] = 0
        self.x[j1, m2] = 1
        self.y[r1, j2, m1] = 1
        self.y[r1, j1, m1] = 0
        self.y[r2, j2, m2] = 0
        self.y[r2, j1, m2] = 1
        self.q[r1, m1] = self.y[r1, :, m1].max()
        self.q[r2, m2] = self.y[r2, :, m2].max()

        self.cmax = self._compute_cm().max()
        return self
