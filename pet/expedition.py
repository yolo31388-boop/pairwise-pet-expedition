"""宠物探险与派遣系统"""
import random
from dataclasses import dataclass, field

FATIGUE_LIMIT = 50.0          # 疲劳达到该值后必须休息
FATIGUE_RECOVER_RATE = 5.0    # 每单位时间恢复的疲劳
RARITY_PITY_THRESHOLD = 10    # 保底：连续未出稀有达到该次数必出稀有


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
    fatigue: float = 0
    skills: dict = field(default_factory=dict)   # 技能名 -> 等级
    intimacy: int = 0                            # 亲密度 0-100


class ExpeditionSystem:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.spots: dict[str, ExpeditionSpot] = {}
        self.pets: dict[str, Pet] = {}
        self.active_expeditions: dict = {}  # pet_id -> spot_id
        self.last_return_time: dict = {}    # pet_id -> 返回时刻
        self._pity_counters: dict = {}      # spot_id -> 连续未出稀有次数

    # ---- bug1 修复：奖励按地点难度与类型区分 ----
    def get_rewards(self, spot_id: str) -> dict:
        spot = self.spots.get(spot_id)
        if spot is None:
            return {}
        if not spot.rewards:
            return {"gold": 10 * spot.difficulty}
        scale = 1.0 + 0.1 * (spot.difficulty - 1)
        return {item: max(1, round(amount * scale))
                for item, amount in spot.rewards.items()}

    # ---- bug2 修复：存在最优派遣时长，超时收益递减 ----
    def get_optimal_time(self, spot_id: str) -> float:
        spot = self.spots.get(spot_id)
        if spot is None:
            return 0.0
        return spot.min_time + (spot.max_time - spot.min_time) * 0.5

    def get_time_efficiency(self, spot_id: str, duration: float) -> float:
        """收益效率：低于min_time不足额，最优区间全额，超过最优时间递减。"""
        spot = self.spots.get(spot_id)
        if spot is None or duration <= 0:
            return 0.0
        if duration < spot.min_time:
            return duration / spot.min_time
        optimal = self.get_optimal_time(spot_id)
        if duration <= optimal:
            return 1.0
        # 超过最优时间后收益递减，最低保留 20%
        decay = optimal / duration
        return max(0.2, decay)

    # ---- bug3 修复：失败概率与随机事件 ----
    def get_failure_rate(self, spot_id: str, pet_level: int) -> float:
        spot = self.spots.get(spot_id)
        difficulty = spot.difficulty if spot else 1
        rate = 0.05 + difficulty * 0.06 - pet_level * 0.004
        return min(0.9, max(0.01, rate))

    def roll_event(self, spot_id: str, pet_level: int = 1) -> str:
        """随机事件：failure / battle / treasure / normal。"""
        roll = self.rng.random()
        failure = self.get_failure_rate(spot_id, pet_level)
        if roll < failure:
            return "failure"
        if roll < failure + 0.15:
            return "battle"
        if roll < failure + 0.15 + 0.10:
            return "treasure"
        return "normal"

    # ---- bug4 修复：同一地点同时只能派一只宠物 ----
    def can_dispatch_same_spot(self, spot_id: str) -> bool:
        return spot_id not in self.active_expeditions.values()

    def dispatch(self, pid: str, spot_id: str, current_time: float = 0.0) -> bool:
        if pid in self.active_expeditions:
            return False
        if not self.can_dispatch_same_spot(spot_id):
            return False
        if not self.can_expedite_again(pid, current_time):
            return False
        self.active_expeditions[pid] = spot_id
        return True

    # ---- bug5 修复：返回后疲劳冷却 ----
    def can_expedite_again(self, pid: str, current_time: float) -> bool:
        pet = self.pets.get(pid)
        if pet is None:
            return False
        if pid in self.active_expeditions:
            return False
        last = self.last_return_time.get(pid)
        if last is not None:
            rested = (current_time - last) * FATIGUE_RECOVER_RATE
            effective_fatigue = max(0.0, pet.fatigue - rested)
        else:
            effective_fatigue = pet.fatigue
        return effective_fatigue < FATIGUE_LIMIT

    def complete_expedition(self, pid: str, current_time: float,
                            duration: float = 0.0) -> dict:
        """结算探险：累积疲劳、掷随机事件、按稀有度发奖励。"""
        spot_id = self.active_expeditions.pop(pid, None)
        if spot_id is None:
            return {}
        pet = self.pets.get(pid)
        if pet is not None:
            pet.fatigue = min(100.0, pet.fatigue + 20.0 + duration * 0.1)
        self.last_return_time[pid] = current_time
        level = pet.level if pet else 1
        event = self.roll_event(spot_id, level)
        if event == "failure":
            return {"event": event, "rewards": {}}
        rewards = self.get_rewards(spot_id)
        bonus = self.get_pet_bonus(pid, spot_id)
        efficiency = self.get_time_efficiency(spot_id, duration) if duration else 1.0
        multiplier = bonus * efficiency
        if event == "treasure":
            multiplier *= 2.0
        elif event == "battle":
            multiplier *= 1.5
        rewards = {item: max(1, round(amount * multiplier))
                   for item, amount in rewards.items()}
        rarity = self.roll_rarity(spot_id)
        return {"event": event, "rarity": rarity, "rewards": rewards}

    # ---- bug6 修复：宠物属性影响成功率与奖励 ----
    def get_pet_bonus(self, pid: str, spot_id: str) -> float:
        pet = self.pets.get(pid)
        if pet is None:
            return 1.0
        level_bonus = 1.0 + pet.level * 0.01
        skill_bonus = 1.0 + sum(getattr(pet, "skills", {}).values()) * 0.02
        intimacy_bonus = 1.0 + getattr(pet, "intimacy", 0) * 0.002
        return level_bonus * skill_bonus * intimacy_bonus

    # ---- bug7 修复：奖励稀有度分级 + 保底 ----
    def get_reward_rarity(self, spot_id: str) -> dict:
        spot = self.spots.get(spot_id)
        difficulty = spot.difficulty if spot else 1
        epic = min(0.30, 0.01 * difficulty)
        rare = min(0.50, 0.05 * difficulty)
        common = max(0.0, 1.0 - rare - epic)
        return {"common": common, "rare": rare, "epic": epic}

    def roll_rarity(self, spot_id: str) -> str:
        """按概率掷稀有度，连续未出稀有达到保底次数必出 rare+。"""
        dist = self.get_reward_rarity(spot_id)
        pity = self._pity_counters.get(spot_id, 0)
        if pity >= RARITY_PITY_THRESHOLD:
            rarity = "epic" if self.rng.random() < 0.3 else "rare"
        else:
            roll = self.rng.random()
            if roll < dist["epic"]:
                rarity = "epic"
            elif roll < dist["epic"] + dist["rare"]:
                rarity = "rare"
            else:
                rarity = "common"
        if rarity == "common":
            self._pity_counters[spot_id] = pity + 1
        else:
            self._pity_counters[spot_id] = 0
        return rarity
