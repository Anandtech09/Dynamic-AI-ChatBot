"""
Self-Learning & Adaptive AI — Reinforcement Learning from Human Feedback (RLHF) tracker.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LearningStats:
    total_feedback_count: int = 0
    average_reward: float = 0.0
    positive_rewards: int = 0
    negative_rewards: int = 0
    adaptation_score: float = 0.0
    top_rewarded_intents: List[Dict[str, Any]] = field(default_factory=list)


class SelfLearningService:
    """
    Reinforcement Learning adaptation module.
    Records feedback rewards (R in [-1.0, 1.0]), calculates policy weights
    for intent models, and provides learning telemetry for the dashboard.
    """

    _instance: Optional[SelfLearningService] = None

    def __init__(self, storage_path: str = "./data/learning_state.json", state_file: Optional[str] = None):
        target_path = state_file or storage_path
        self.storage_path = Path(target_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.state: Dict[str, Any] = self._load_state()

    @classmethod
    def get_instance(cls) -> SelfLearningService:
        if cls._instance is None:
            cls._instance = SelfLearningService()
        return cls._instance

    def _load_state(self) -> Dict[str, Any]:
        if self.storage_path.exists():
            try:
                return json.loads(self.storage_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Could not read learning state: %s", e)
        return {
            "total_feedback": 0,
            "rewards": [],
            "intent_rewards": {},
            "cumulative_reward": 0.0,
        }

    def _save_state(self):
        try:
            self.storage_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Could not persist learning state: %s", e)

    def record_interaction(self, intent: Optional[str] = None, sentiment: Optional[str] = None):
        """Track query interaction counts for policy observation."""
        if "interactions" not in self.state:
            self.state["interactions"] = 0
        self.state["interactions"] += 1
        self._save_state()

    def record_feedback(self, rating: int, intent: Optional[str] = None, comment: str = "") -> float:
        """
        Record a reward signal from user feedback (rating 1-5).
        Maps rating to normalized reward R in [-1.0, +1.0]:
        1 -> -1.0, 2 -> -0.5, 3 -> 0.0, 4 -> +0.5, 5 -> +1.0
        """
        reward = (rating - 3) / 2.0  # Normalized: -1.0 to 1.0

        self.state["total_feedback"] += 1
        self.state["cumulative_reward"] += reward

        intent_key = intent or "general_query"
        intent_stats = self.state["intent_rewards"].get(intent_key, {"count": 0, "sum": 0.0, "avg": 0.0})
        intent_stats["count"] += 1
        intent_stats["sum"] += reward
        intent_stats["avg"] = round(intent_stats["sum"] / intent_stats["count"], 3)
        self.state["intent_rewards"][intent_key] = intent_stats

        # Keep last 100 reward records
        self.state.setdefault("rewards", []).append({
            "rating": rating,
            "reward": reward,
            "intent": intent_key,
            "comment": comment[:100],
        })
        if len(self.state["rewards"]) > 100:
            self.state["rewards"] = self.state["rewards"][-100:]

        self._save_state()
        logger.info("Recorded RL feedback reward %+.2f for intent '%s'", reward, intent_key)
        return reward

    def get_intent_adaptation_bias(self, intent: str) -> float:
        """
        Get policy adaptation multiplier based on historical reinforcement.
        Returns value > 1.0 for consistently rewarded intents, < 1.0 for penalized intents.
        """
        stats = self.state["intent_rewards"].get(intent)
        if not stats or stats["count"] < 1:
            return 1.0
        # Bounded between 0.70 and 1.30
        return max(0.70, min(1.30, 1.0 + (stats["avg"] * 0.20)))

    get_intent_weight = get_intent_adaptation_bias

    def get_learning_stats(self) -> LearningStats:
        """Return aggregated RL learning stats for dashboard."""
        total = self.state["total_feedback"]
        cum_reward = self.state["cumulative_reward"]
        avg_reward = round(cum_reward / total, 3) if total > 0 else 0.0

        pos = sum(1 for r in self.state.get("rewards", []) if r["reward"] > 0)
        neg = sum(1 for r in self.state.get("rewards", []) if r["reward"] < 0)

        top_intents = [
            {"intent": k, "avg_reward": v["avg"], "count": v["count"]}
            for k, v in sorted(
                self.state["intent_rewards"].items(),
                key=lambda x: x[1]["avg"],
                reverse=True,
            )
        ]

        # Adaptation score represents learning progress (0.0 to 100.0)
        adaptation_score = min(100.0, round(total * 5.0 + max(0, avg_reward * 30.0), 1))

        return LearningStats(
            total_feedback_count=total,
            average_reward=avg_reward,
            positive_rewards=pos,
            negative_rewards=neg,
            adaptation_score=adaptation_score,
            top_rewarded_intents=top_intents[:5],
        )

    def get_stats(self) -> Dict[str, Any]:
        """Return raw stats dictionary including policy weights."""
        stats = self.get_learning_stats()
        policy_weights = {
            intent: self.get_intent_weight(intent)
            for intent in self.state.get("intent_rewards", {})
        }
        return {
            "total_feedback": stats.total_feedback_count,
            "average_reward": stats.average_reward,
            "positive_rewards": stats.positive_rewards,
            "negative_rewards": stats.negative_rewards,
            "adaptation_score": stats.adaptation_score,
            "top_rewarded_intents": stats.top_rewarded_intents,
            "policy_weights": policy_weights,
        }


_self_learning_service: Optional[SelfLearningService] = None


def get_self_learning_service() -> SelfLearningService:
    """Return singleton SelfLearningService instance."""
    global _self_learning_service
    if _self_learning_service is None:
        _self_learning_service = SelfLearningService()
    return _self_learning_service
