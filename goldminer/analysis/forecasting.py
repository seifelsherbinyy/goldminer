"""Monte Carlo forecasting for income/expense streams and portfolio assumptions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from goldminer.utils import setup_logger


@dataclass
class ForecastResult:
    """Container for forecast outputs and recommendations."""

    percentiles: pd.DataFrame
    allocations: Dict[str, float]
    assumptions: Dict[str, Any]
    savings_summary: Dict[str, Any]


class MonteCarloForecaster:
    """Run Monte Carlo simulations on transaction cashflows."""

    def __init__(self, config=None):
        self.config = config
        self.logger = setup_logger(__name__)
        self.settings = (config.get("analysis.forecasting", {}) if config else {})

    def run_forecast(
        self,
        df: pd.DataFrame,
        horizon_months: Optional[int] = None,
        risk_level: Optional[str] = None,
        simulations: Optional[int] = None,
        initial_balance: float = 0.0,
    ) -> ForecastResult:
        """Run a Monte Carlo forecast from a unified transaction ledger."""
        if df.empty:
            raise ValueError("Cannot run forecast on empty transaction ledger")

        horizon = horizon_months or int(self.settings.get("horizon_months", 36))
        sim_count = simulations or int(self.settings.get("simulations", 500))
        risk = (risk_level or self.settings.get("risk_level", "balanced")).lower()
        risk_profile = self._get_risk_profile(risk)

        income_stats, expense_stats, monthly_net = self._extract_cashflows(df)
        paths = self._simulate_paths(
            horizon,
            sim_count,
            income_stats,
            expense_stats,
            risk_profile,
            initial_balance,
        )
        percentiles = self._build_percentiles(paths, horizon, risk)
        allocations, savings_summary = self._recommend_allocations(
            income_stats, expense_stats, risk_profile, monthly_net
        )

        assumptions = {
            "horizon_months": horizon,
            "simulations": sim_count,
            "risk_level": risk,
            "expected_return": risk_profile.get("expected_return"),
            "volatility": risk_profile.get("volatility"),
            "generated_at": datetime.utcnow().isoformat(),
        }

        return ForecastResult(
            percentiles=percentiles,
            allocations=allocations,
            assumptions=assumptions,
            savings_summary=savings_summary,
        )

    def _extract_cashflows(self, df: pd.DataFrame):
        working = df.copy()
        if "date" in working.columns:
            working["date"] = pd.to_datetime(working["date"], errors="coerce")
            working = working.dropna(subset=["date"])
            working = working.sort_values("date")
            monthly = working.set_index("date").resample("M")["amount"].sum()
        else:
            monthly = working["amount"]

        income_series = monthly[monthly > 0]
        expense_series = monthly[monthly < 0].abs()

        income_stats = {
            "mean": float(income_series.mean()) if not income_series.empty else 0.0,
            "std": float(income_series.std()) if not income_series.empty else 0.0,
        }
        expense_stats = {
            "mean": float(expense_series.mean()) if not expense_series.empty else 0.0,
            "std": float(expense_series.std()) if not expense_series.empty else 0.0,
        }

        monthly_net = float(monthly.mean()) if len(monthly) else 0.0

        self.logger.info(
            "Prepared cashflow stats - income mean: %.2f, expense mean: %.2f", 
            income_stats["mean"],
            expense_stats["mean"],
        )
        return income_stats, expense_stats, monthly_net

    def _simulate_paths(
        self,
        horizon: int,
        simulations: int,
        income_stats: Dict[str, float],
        expense_stats: Dict[str, float],
        risk_profile: Dict[str, Any],
        initial_balance: float,
    ) -> np.ndarray:
        rng = np.random.default_rng()
        paths = np.zeros((simulations, horizon))

        monthly_return = risk_profile.get("expected_return", 0.05) / 12
        monthly_vol = risk_profile.get("volatility", 0.12) / np.sqrt(12)

        for sim in range(simulations):
            balance = initial_balance
            for month in range(horizon):
                income_draw = max(
                    rng.normal(income_stats.get("mean", 0.0), income_stats.get("std", 0.0)), 0.0
                )
                expense_draw = max(
                    rng.normal(expense_stats.get("mean", 0.0), expense_stats.get("std", 0.0)), 0.0
                )
                net = income_draw - expense_draw
                growth = rng.normal(monthly_return, monthly_vol)
                balance = (balance + net) * (1 + growth)
                paths[sim, month] = balance

        self.logger.info("Simulated %s paths over %s months", simulations, horizon)
        return paths

    def _build_percentiles(self, paths: np.ndarray, horizon: int, risk_level: str) -> pd.DataFrame:
        percentiles = {
            "month": list(range(1, horizon + 1)),
            "p5": np.percentile(paths, 5, axis=0),
            "p25": np.percentile(paths, 25, axis=0),
            "p50": np.percentile(paths, 50, axis=0),
            "p75": np.percentile(paths, 75, axis=0),
            "p95": np.percentile(paths, 95, axis=0),
        }
        df = pd.DataFrame(percentiles)
        df["risk_level"] = risk_level
        df["created_at"] = datetime.utcnow()
        return df

    def _recommend_allocations(
        self,
        income_stats: Dict[str, float],
        expense_stats: Dict[str, float],
        risk_profile: Dict[str, Any],
        monthly_net: float,
    ):
        reserve_months = risk_profile.get("reserve_months", 3)
        equity_allocation = risk_profile.get("equity_allocation", 0.6)

        emergency_target = max(expense_stats.get("mean", 0.0) * reserve_months, 0.0)
        monthly_savings_capacity = max(monthly_net, 0.0)
        investment_suggestion = monthly_savings_capacity * equity_allocation
        safety_suggestion = monthly_savings_capacity - investment_suggestion

        allocations = {
            "emergency_fund": round(emergency_target, 2),
            "growth_allocation": round(investment_suggestion * 12, 2),
            "cash_buffer": round(safety_suggestion * 12, 2),
        }

        savings_summary = {
            "reserve_months": reserve_months,
            "monthly_savings_capacity": round(monthly_savings_capacity, 2),
            "investment_split": equity_allocation,
        }

        self.logger.info(
            "Recommended allocations computed with reserve %s months and equity split %.0f%%",
            reserve_months,
            equity_allocation * 100,
        )
        return allocations, savings_summary

    def _get_risk_profile(self, risk_level: str) -> Dict[str, Any]:
        profiles = self.settings.get("risk_profiles", {})
        default_profile = {
            "expected_return": 0.05,
            "volatility": 0.12,
            "reserve_months": 3,
            "equity_allocation": 0.6,
        }
        return profiles.get(risk_level, default_profile)
