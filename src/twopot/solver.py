"""Small numerical helpers, written out so every step can be explained."""

from __future__ import annotations

from collections.abc import Callable, Sequence


def bisect(
    f: Callable[[float], float], lo: float, hi: float, tol: float = 1e-10
) -> float:
    """Find x in [lo, hi] with f(x) = 0, for f that crosses zero once.

    Halve the interval repeatedly, keeping the half where the sign changes.
    Slower than Newton's method but it cannot diverge.
    """
    f_lo, f_hi = f(lo), f(hi)
    if f_lo == 0:
        return lo
    if f_hi == 0:
        return hi
    if (f_lo > 0) == (f_hi > 0):
        raise ValueError("f(lo) and f(hi) must have opposite signs")
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = f(mid)
        if (f_mid > 0) == (f_lo > 0):
            lo, f_lo = mid, f_mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def internal_rate_of_return(cash_flows: Sequence[float], hi: float = 10.0) -> float:
    """Rate per period at which the cash flows have zero present value.

    ``cash_flows[k]`` is the amount at the end of period k; index 0 is today.
    Money received is positive and money paid is negative. Assumes money is
    received first and repaid later, so there is a single solution.
    """

    def present_value(rate: float) -> float:
        return sum(cf / (1 + rate) ** k for k, cf in enumerate(cash_flows))

    if sum(cash_flows) >= 0:
        return 0.0  # repaid no more than was received: no interest was charged
    return bisect(present_value, 0.0, hi)
