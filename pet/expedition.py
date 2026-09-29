"""宠物探险与派遣系统 - 含7个bug"""
from dataclasses import dataclass, field

@dataclass
class ExpeditionSpot:
    sid: str
    name: str
    difficulty: int
    min_time: float
    max_time: float
    rewards: dict = field(default_factory=dict)

@dataclass
class Pet:
    pid: str
    name: str
    level: int = 1
    fatigue: float = 0  # bug5: 无疲劳

class ExpeditionSystem:
    def __init__(self, seed=42):
        import random
        self.rng = random.Random(seed)
        self.spots: dict[str, ExpeditionSpot] = {}
        self.pets: dict[str, Pet] = {}
        self.active_expeditions: dict = {}  # pet_id -> spot_id

    def get_rewards(self, spot_id: str) -> dict:
        # bug1: 固定奖励
        return {"gold": 100}

    def get_optimal_time(self, spot_id: str) -> float:
        # bug2: 无最优时间
        return float("inf")

    def get_failure_rate(self, spot_id: str, pet_level: int) -> float:
        # bug3: 无风险
        return 0.0

    def can_dispatch_same_spot(self, spot_id: str) -> bool:
        # bug4: 可同时多宠
        return True

    def can_expedite_again(self, pid: str, current_time: float) -> bool:
        # bug5: 无冷却
        return True

    def get_pet_bonus(self, pid: str, spot_id: str) -> float:
        # bug6: 属性不影响
        return 1.0

    def get_reward_rarity(self, spot_id: str) -> dict:
        # bug7: 无稀有度
        return {"common": 1.0}
