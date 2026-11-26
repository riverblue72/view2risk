"""Export the one public Entry-to-Exit tracking illustration. Requires NumPy."""
import json
from pathlib import Path

import numpy as np

SITE = Path(__file__).resolve().parents[1] / "site"
PUBLIC = SITE / "data/public"
SEED = 20261126


def forward_filter(times, observations, bias, covariance, q):
    # Common exact Entry position. Initial velocity has mean zero and variance 25.
    state = np.r_[observations[0], 0., 0.]
    eye = np.eye(2)
    P = np.diag([0., 0., 25., 25.])
    result = [state[:2].copy()]
    for dt, observation in zip(np.diff(times), observations[1:]):
        F = np.eye(4)
        F[:2, 2:] = dt * eye
        Q = q * np.block([[dt**3 / 3 * eye, dt**2 / 2 * eye],
                          [dt**2 / 2 * eye, dt * eye]])
        state = F @ state
        P = F @ P @ F.T + Q
        gain = np.linalg.solve(P[:2, :2] + covariance, P[:2, :]).T
        state += gain @ (observation - bias - state[:2])
        residual = np.eye(4)
        residual[:, :2] -= gain
        P = residual @ P @ residual.T + gain @ covariance @ gain.T
        result.append(state[:2].copy())
    return np.array(result)


def build():
    case = json.loads((PUBLIC / "cases/public-imptc-01.json").read_text())
    evidence = json.loads((PUBLIC / "demo-evidence.json").read_text())
    gt = next(row["GT"] for row in evidence["cases"] if row["event_id"] == case["event_id"])
    entry, exit_time = np.array([gt["entry_s"], gt["exit_s"]]) - case["origin0_s"]
    times = np.array(case["actual_observations"]["elapsed_s"])
    xy = np.array(case["actual_observations"]["xy"])
    assert times[0] < entry < exit_time < times[-1] and np.all(np.diff(times) > 0)
    t = np.r_[entry, times[(entry < times) & (times < exit_time)], exit_time]
    assert np.diff(t).max() < .061
    reference = np.column_stack([np.interp(t, times, axis) for axis in xy.T])
    proxy = evidence["r_proxy"]["train_fit"]
    covariance, bias = np.array(proxy["covariance_m2"]), np.array(proxy["bias_m"])
    packet = json.loads((PUBLIC / "r/o0008.json").read_text())
    cfg = packet["results"]["iid_1__filtered_mean"]["filter"]
    assert np.allclose(cfg["filter_R"], covariance)
    noisy = reference.copy()
    noisy[1:] += np.random.default_rng(SEED).multivariate_normal(bias, covariance, len(t) - 1)
    q = cfg["filter_q_m2_s3"]
    corrected = forward_filter(t, noisy, bias, covariance, q)
    assert np.array_equal(forward_filter(t[:70], noisy[:70], bias, covariance, q), corrected[:70])
    data = dict(event_id=case["event_id"], seed=SEED, q_m2_s3=q, scenario="iid_1",
                elapsed_s=(t-entry).tolist(), clean=reference.tolist(), noisy=noisy.tolist(),
                filtered_mean=corrected.tolist())
    (SITE / "demo/f2-full-track.json").write_text(json.dumps(data, separators=(",", ":")) + "\n")
    print(f'{len(t)} positions, {t[-1]-t[0]:.6f} seconds, largest interval {np.diff(t).max():.6f} s')


if __name__ == "__main__":
    build()
