"""Bounds on the mix contribution compatible with the precision of EPA Table 3.2."""

from itertools import product
from math import fsum


def extreme_mean(rates, percentages, *, maximize):
    """Allocate shares within rounding bins, exhausting the best rates first."""
    lower = [max(0.0, (p - 0.05) / 100) for p in percentages]
    upper = [min(1.0, (p + 0.05) / 100) for p in percentages]
    remaining = 1.0 - fsum(lower)
    if remaining < -1e-12 or fsum(upper) < 1 - 1e-12:
        raise ValueError("Printed percentages are inconsistent with shares totaling 100%.")
    shares = lower.copy()
    for i in sorted(range(len(rates)), key=rates.__getitem__, reverse=maximize):
        add = min(max(remaining, 0.0), upper[i] - lower[i])
        shares[i] += add
        remaining -= add
    return fsum(s * r for s, r in zip(shares, rates, strict=True))


def mix_bounds(start_pct, end_pct, start_rates, end_rates):
    """Bound the symmetric mix term over all compatible true shares and rates.

    For fixed shares the term is linear in each midpoint rate, so check both
    endpoints of each rate interval. At fixed rates, the two years' shares
    can be optimized separately with a single adding-up constraint per year.
    """
    midpoints = [(a + b) / 2 for a, b in zip(start_rates, end_rates, strict=True)]
    low, high = float("inf"), float("-inf")
    for errors in product((-0.5, 0.5), repeat=len(midpoints)):
        rates = [m + err for m, err in zip(midpoints, errors, strict=True)]
        lower = extreme_mean(rates, end_pct, maximize=False) - extreme_mean(
            rates, start_pct, maximize=True
        )
        upper = extreme_mean(rates, end_pct, maximize=True) - extreme_mean(
            rates, start_pct, maximize=False
        )
        low, high = min(low, lower), max(high, upper)
    return low, high
