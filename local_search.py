import numpy as np
from bgap_c import BGAPConstrained
from bgap_r import BGAPChargeOperations
# x = transfer job j performed by m
# q = charge jobe r performed by m
# y = transfer job j performed by m after charge job r

# gamma = charge operation r performed
# chi = transfer operation j assigned to charge operation r

# theta = charge operation r assigned to m

# x = chi.T @ theta (J, M)
# y = np.stack([np.outer(chi[r], theta[r]) for r in range(R)], axis = 0) (R, J, M)


class LocalSearch:

    def __init__(self, x: np.ndarray, y: np.ndarray, q: np.ndarray, cmax: float, processing_times: np.ndarray, charge_duration: float, energy_requirement: np.ndarray, battery_capacity: float) -> None:
        self.x = x  # (J, M)
        self.y = y  # (R, J, M)
        self.q = q  # (R, M)
        self.cmax = cmax
        self.d = processing_times
        self.t = charge_duration
        self.e = energy_requirement
        self.b = battery_capacity

    @classmethod
    def from_constrained(cls, bgap: BGAPConstrained, t: float) -> 'LocalSearch':
        x = bgap.x
        y = np.zeros((bgap.J, bgap.J, bgap.M))
        q = np.zeros((bgap.J, bgap.M))
        cmax = bgap.z

        ls = cls(x, y, q, cmax, bgap.d, t, bgap.e, bgap.b)
        return ls

    @classmethod
    def from_charge(cls, bgap: BGAPChargeOperations) -> 'LocalSearch':
        x = bgap.chi.T @ bgap.theta
        y = np.stack([np.outer(bgap.chi[r], bgap.theta[r])
                     for r in range(bgap.R)], axis=0)
        cmax = bgap.z
        ls = cls(x, y, bgap.theta, cmax, bgap.d, bgap.t, bgap.e, bgap.b)
        return ls

    def _compute_cm(self) -> np.ndarray:
        first = self.x @ self.d
        second = (self.t * self.q)[1:].sum(axis=0)
        return first + second

    def _get_best_two(self, cm: np.ndarray, m1: np.int64) -> tuple[np.int64, np.int64]:
        # precompute best cm-s
        cm[m1] = -np.inf
        top1 = cm.argmax()  # second best
        cm[top1] = -np.inf
        top2 = cm.argmax()  # if m2 == top1 use this
        return (top1, top2)

    def saving_add(self, s_star: float) -> tuple[float, tuple]:
        M = self.x.shape[1]
        cm = self._compute_cm()
        m1 = np.argmax(cm)
        J_hat = np.where(self.x[m1] == 1)[0]

        top1, top2 = self._get_best_two(cm, m1)

        update = ()
        for j in J_hat:
            m1_new = cm[m1] - self.d[j]
            for m2 in range(M):
                if m2 == m1:
                    continue
                m2_new = cm[m2] + self.d + self.t
                cm_max = cm[top2] if m2 == top1 else cm[top1]
                s_a = max(0, self.cmax-max(m1_new, m2_new, cm_max))
                if s_a > s_star:
                    s_star = s_a
                    r1 = np.argmax(self.y[:, j, m1] == 1)
                    r2 = (np.where(self.y[:, :, m2] == 1)[0]).max() + 1
                    update = (m1, r1, j, m2, r2, j)
        return (s_star, update)

    def save_swap(self, s_star: float) -> tuple[float, tuple]:
        M = self.x.shape[1]
        cm = self._compute_cm()
        m1 = np.argmax(cm)
        charge_left = self.b - (self.e @ self.y)

        top1, top2 = self._get_best_two(cm, m1)

        update = ()

        for r1 in np.where(self.q == 1)[0]:
            for j1 in np.where(self.y[r1, :, m1] == 1)[0]:
                for m2 in range(M):
                    if m2 == m1:
                        continue
                    for r2 in np.where(self.q[m2] == 1)[0]:
                        for j2 in np.where(self.y[r2, :, m2])[0]:
                            if charge_left[m1] >= self.e[j2]-self.e[j1] and charge_left[m2] >= self.e[j1]-self.e[j2]:

                                m1_new = cm[m1] - self.d[j1] + self.d[j2]
                                m2_new = cm[m2] + self.d[j1] - self.d[j2]
                                cm_max = cm[top2] if m2 == top1 else cm[top1]
                                s_s = max(0, self.cmax -
                                          max(m1_new, m2_new, cm_max))
                                if s_s > s_star:
                                    s_star = s_s
                                    update = (m1, r1, j1, m2, r2, j2)
        return (s_star, update)

    def save_remove(self, s_star: float) -> tuple[float, tuple]:
        M = self.x.shape[1]
        charge_left = self.b - (self.e @ self.y)
        cm = self._compute_cm()
        m1 = cm.argmax()
        J_hat = np.where(self.x[m1] == 1)[0]
        R_hat = [np.flatnonzero(self.q[:, m]) for m in range(M)]
        top1, top2 = self._get_best_two(cm, m1)

        update = ()

        for j in J_hat:
            for m2 in range(M):
                if m2 == m1:
                    continue
                for r2 in R_hat[m2]:
                    if charge_left[m2] >= self.e[j]:
                        m1_new = cm[m1] - self.d[j]
                        m2_new = cm[m2] + self.d[j]
                        cm_max = cm[top2] if m2 == top1 else cm[top1]
                        s_r = max(0, self.cmax-max(m1_new, m2_new, cm_max))
                        if s_r > s_star:
                            s_star = s_r
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

        transport = self.x @ self.d
        charges = self.y[1:].sum(axis=0) * self.t
        self.cmax = transport + charges
        return self

    def solve(self):
        while True:
            s_star = 0.0
            s_a = self.saving_add(s_star)
            s_r = self.save_remove(s_star)
            s_s = self.save_swap(s_star)
            savings = np.array([s_a[0], s_r[0], s_s[0]], dtype=float)
            best = savings.argmax()
            if savings[best] > 0.0:
                update = [s_a[1], s_r[1], s_s[1]][best]
                self.update_best(update)
            else:
                break
