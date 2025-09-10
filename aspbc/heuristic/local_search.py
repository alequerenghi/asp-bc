import time
import numpy as np
from .bgap_c import BGAPConstrained
from .bgap_r import BGAPChargeOperations
from numpy.typing import NDArray
# x = transfer job j performed by m
# q = charge jobe r performed by m
# y = transfer job j performed by m after charge job r

# gamma = charge operation r performed


# x = chi.T @ theta (J, M)
# y = np.stack([np.outer(chi[r], theta[r]) for r in range(R)], axis = 0) (R, J, M)


class LocalSearch:

    def __init__(self, x: NDArray[np.bool_], y: NDArray[np.bool_], q: NDArray[np.bool_], cmax: float, processing_times: NDArray[np.int64], charge_duration: float, energy_requirement: NDArray[np.float64], battery_capacity: float) -> None:
        self.x = x  # (J, M)
        self.y = y  # (R, J, M)
        self.q = q  # (R, M)
        self.cmax = cmax
        self.d = processing_times
        self.t = charge_duration
        self.e = energy_requirement
        self.b = battery_capacity

    @classmethod
    def from_constrained(cls, bgap: BGAPConstrained, t: float, R=0) -> 'LocalSearch':
        J = bgap.x.shape[0]
        R = R if R != 0 else J
        x = bgap.x
        y = np.zeros((R, J, bgap.M), dtype=bool)
        y[0] = x
        q = np.zeros((J, bgap.M), dtype=bool)
        q[0] = 1
        cmax = bgap.z

        ls = cls(x, y, q, cmax, bgap.d, t, bgap.e, bgap.b)
        return ls

    @classmethod
    def from_charge(cls, bgap: BGAPChargeOperations, energy_requirements: NDArray[np.float64], battery_capacity: float) -> 'LocalSearch':
        # chi = transfer operation j assigned to charge operation r
        # theta = charge operation r assigned to m
        x = bgap.chi.T @ bgap.theta
        y = np.stack([np.outer(bgap.chi[r], bgap.theta[r])
                     for r in range(bgap.theta.shape[0])], axis=0)
        ls = cls(x, y, bgap.theta, bgap.z, bgap.d, bgap.t,
                 energy_requirements, battery_capacity)
        # ls.cmax = ls._compute_cm().max()
        return ls

    def _compute_cm(self) -> np.ndarray:
        first = self.d @ self.x
        second = (self.t * self.q).sum(axis=0, dtype=np.float64) - self.t
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

    def saving_add(self, s_star: float, update: tuple) -> tuple[float, tuple]:
        M = self.x.shape[1]
        cm = self._compute_cm()  # duration for each AGV
        critical_machines = np.where(cm == cm.max())[0]
        np.random.shuffle(critical_machines)

        for m1 in critical_machines:
            top1, top2 = self._get_best_two(cm, m1)
            # iterate jobs of most loaded AGV
            for j in np.where(self.x[:, m1] == 1)[0]:
                m1_new = cm[m1] - self.d[j]
                # find another AGV
                for m2 in range(M):
                    if m2 == m1:
                        continue
                    # Consider the cost of doing the job and a new charge
                    m2_new = cm[m2] + self.d[j] + self.t
                    if M <= 2:
                        cm_max = 0
                    else:
                        cm_max = cm[top2] if m2 == top1 else cm[top1]
                    # Compute saving
                    s_a = max(0, self.cmax-max(m1_new, m2_new, cm_max))
                    # If you save time
                    if s_a > s_star:
                        s_star = s_a
                        # Find the respective charge job in m1
                        r1 = np.argmax(self.y[:, j, m1] == 1)
                        # Find a new charge job in m2
                        r2 = (np.where(self.y[:, :, m2] == 1)[0]).max() + 1
                        update = (m1, r1, j, m2, r2, j)
        return (s_star, update)

    def save_swap(self, s_star: float, update: tuple) -> tuple[float, tuple]:
        M = self.x.shape[1]
        cm = self._compute_cm()
        critical_machines = np.where(cm == cm.max())[0]
        np.random.shuffle(critical_machines)
        # Compute the remaining charge (capacity - sum(e[j] * y[r, j, m]))
        charge_left = self.b - (self.e @ self.y)

        for m1 in critical_machines:
            top1, top2 = self._get_best_two(cm, m1)
            # iterate charge jobs of m1
            for r1 in np.where(self.q[:, m1] == 1)[0]:
                # iterate jobs on m1 and r1
                for j1 in np.where(self.y[r1, :, m1] == 1)[0]:
                    # find another agv
                    for m2 in range(M):
                        if m2 == m1:
                            continue
                        # iterate charge jobs of m2
                        for r2 in np.where(self.q[:, m2] == 1)[0]:
                            # iterate jobs of m2 and r2
                            for j2 in np.where(self.y[r2, :, m2])[0]:
                                # if both can accept charge
                                if charge_left[r1, m1] >= self.e[j2]-self.e[j1] and charge_left[r2, m2] >= self.e[j1]-self.e[j2]:
                                    m1_new = cm[m1] - self.d[j1] + self.d[j2]
                                    m2_new = cm[m2] + self.d[j1] - self.d[j2]
                                    if M <= 2:
                                        cm_max = 0
                                    else:
                                        cm_max = cm[top2] if m2 == top1 else cm[top1]
                                    s_s = max(0, self.cmax -
                                              max(m1_new, m2_new, cm_max))
                                    if s_s > s_star:
                                        s_star = s_s
                                        update = (m1, r1, j1, m2, r2, j2)
        return (s_star, update)

    def save_remove(self, s_star: float, update: tuple) -> tuple[float, tuple]:
        M = self.x.shape[1]
        charge_left = self.b - (self.e @ self.y)
        cm = self._compute_cm()
        critical_machines = np.where(cm == cm.max())[0]
        np.random.shuffle(critical_machines)

        for m1 in critical_machines:
            top1, top2 = self._get_best_two(cm, m1)
            # iterate jobs of m1
            for j in np.where(self.x[:, m1] == 1)[0]:
                m1_new = cm[m1] - self.d[j]
                # find new agv
                for m2 in range(M):
                    if m2 == m1:
                        continue
                    m2_new = cm[m2] + self.d[j]
                    # iterate charge jobs of m2
                    for r2 in np.where(self.q[:, m2] == 1)[0]:
                        # check if you can add this job
                        if charge_left[r2, m2] >= self.e[j]:
                            if M <= 2:
                                cm_max = 0
                            else:
                                cm_max = cm[top2] if m2 == top1 else cm[top1]
                            s_r = max(0, self.cmax-max(m1_new, m2_new, cm_max))
                            if s_r > s_star:
                                s_star = s_r
                                # find the charge job
                                r1 = self.y[:, j, m1].argmax()
                                update = (m1, r1, j, m2, r2, j)
        return (s_star, update)

    def update_best(self, update: tuple) -> 'LocalSearch':
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

    def solve(self):
        t0 = time.time()
        while True:
            s_star = (0.0, ())
            s_star = self.saving_add(*s_star)
            s_star = self.save_remove(*s_star)
            s_star = self.save_swap(*s_star)
            if s_star[0] > 0.0:
                update = s_star[1]
                self.update_best(update)
            else:
                break
        self.time = time.time() - t0
        return self
