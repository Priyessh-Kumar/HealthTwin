"""
Baseline computation and trend detection engine — pure Python, no AI.

This is the core math behind the Health Twin: personal baselines,
running averages, and deviation alerts based on the individual's own
history (not population norms).
"""

from __future__ import annotations

from models.schemas import BaselineEntry, TrendAlert


def compute_baselines(metrics_by_name: dict[str, list[float]]) -> list[BaselineEntry]:
    """
    Compute the running personal average for each metric.

    Args:
        metrics_by_name: {metric_name: [values ordered by date ascending]}

    Returns:
        List of BaselineEntry with average, latest value, and count.
    """
    baselines: list[BaselineEntry] = []
    for name, values in metrics_by_name.items():
        if not values:
            continue
        avg = sum(values) / len(values)
        baselines.append(
            BaselineEntry(
                metric_name=name,
                average=round(avg, 2),
                latest=values[-1],
                data_points=len(values),
            )
        )
    return baselines


def detect_trends(
    metrics_by_name: dict[str, list[float]],
    consecutive_threshold: int = 5,
    deviation_pct_threshold: float = 5.0,
) -> list[TrendAlert]:
    """
    Flag when a metric deviates from the personal baseline over N consecutive days.

    A trend is detected when the last `consecutive_threshold` readings are ALL
    above (or below) the personal average by at least `deviation_pct_threshold` %.

    Args:
        metrics_by_name: {metric_name: [values ordered by date ascending]}
        consecutive_threshold: how many consecutive days to check
        deviation_pct_threshold: minimum % deviation from average to flag

    Returns:
        List of TrendAlert for metrics that are trending away from baseline.
    """
    alerts: list[TrendAlert] = []
    for name, values in metrics_by_name.items():
        if len(values) < consecutive_threshold:
            continue

        avg = sum(values) / len(values)
        if avg == 0:
            continue

        tail = values[-consecutive_threshold:]

        # Check rising trend
        all_above = all(v > avg for v in tail)
        if all_above:
            max_dev = max((v - avg) / avg * 100 for v in tail)
            if max_dev >= deviation_pct_threshold:
                alerts.append(
                    TrendAlert(
                        metric_name=name,
                        direction="rising",
                        consecutive_days=consecutive_threshold,
                        deviation_pct=round(max_dev, 2),
                        message=(
                            f"{name} has been above your personal average "
                            f"for {consecutive_threshold} consecutive days "
                            f"(up to {round(max_dev, 1)}% above baseline)."
                        ),
                    )
                )
                continue

        # Check falling trend
        all_below = all(v < avg for v in tail)
        if all_below:
            max_dev = max((avg - v) / avg * 100 for v in tail)
            if max_dev >= deviation_pct_threshold:
                alerts.append(
                    TrendAlert(
                        metric_name=name,
                        direction="falling",
                        consecutive_days=consecutive_threshold,
                        deviation_pct=round(max_dev, 2),
                        message=(
                            f"{name} has been below your personal average "
                            f"for {consecutive_threshold} consecutive days "
                            f"(up to {round(max_dev, 1)}% below baseline)."
                        ),
                    )
                )

    return alerts


def deviation_summary(alerts: list[TrendAlert]) -> str:
    """Human-readable one-line summary of all active trend alerts."""
    if not alerts:
        return "All metrics are within your personal normal range."
    parts = [f"{a.metric_name} is {a.direction}" for a in alerts]
    return "Attention needed: " + "; ".join(parts) + "."
