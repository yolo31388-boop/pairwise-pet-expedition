"""宠物探险与派遣系统"""
from dataclasses import dataclass, field

RARITY_TIERS = ("common", "uncommon", "rare", "epic", "legendary")

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
    skill: float = 0
    intimacy: float = 0

class ExpeditionSystem:
    def __init__(self, seed=42):
        import random
        self.rng = random.Random(seed)
        self.spots: dict[str, ExpeditionSpot] = {}
        self.pets: dict[str, Pet] = {}
        self.active_expeditions: dict = {}  # pet_id -> spot_id
        self._rare_pity: dict[str, int] = {}  # spot_id -> 距上次稀有奖励的次数

    def get_rewards(self, spot_id: str) -> dict:
        """按地点难度和类型区分奖励，高级地点给稀有奖励。"""
        spot = self.spots[spot_id]
        if spot.rewards:
            scale = 1.0 + 0.1 * (spot.difficulty - 1)
            return {k: max(1, round(v * scale)) for k, v in spot.rewards.items()}
        return {"gold": 50 * spot.difficulty, "exp": 20 * spot.difficulty}

    def get_optimal_time(self, spot_id: str) -> float:
        """最优派遣时长：取地点时间区间中点，超过后收益递减。"""
        spot = self.spots[spot_id]
        return (spot.min_time + spot.max_time) / 2

    def get_time_efficiency(self, spot_id: str, duration: float) -> float:
        """时长收益系数：最优区间内为1，超过最优时间收益递减。"""
        spot = self.spots[spot_id]
        optimal = self.get_optimal_time(spot_id)
        if duration <= 0:
            return 0.0
        if duration < spot.min_time:
            return duration / spot.min_time
        if duration <= optimal:
            return 1.0
        return max(0.2, optimal / duration)

    def get_failure_rate(self, spot_id: str, pet_level: int) -> float:
        """失败概率：随地点难度上升，随宠物等级下降。"""
        spot = self.spots[spot_id]
        rate = 0.05 * spot.difficulty - 0.005 * pet_level
        return min(0.9, max(0.0, rate))

    def roll_event(self, spot_id: str, pet_level: int) -> str:
        """随机事件：failure / battle / treasure / normal。"""
        spot = self.spots[spot_id]
        roll = self.rng.random()
        failure = self.get_failure_rate(spot_id, pet_level)
        if roll < failure:
            return "failure"
        if roll < failure + 0.1 + 0.02 * spot.difficulty:
            return "battle"
        if roll > 1.0 - 0.05 - 0.01 * spot.difficulty:
            return "treasure"
        return "normal"

    def can_dispatch_same_spot(self, spot_id: str) -> bool:
        """同一地点同时只能派一只宠物。"""
        return spot_id not in self.active_expeditions.values()

    def dispatch(self, pid: str, spot_id: str) -> bool:
        """派遣宠物：需通过地点占用与疲劳检查。"""
        pet = self.pets.get(pid)
        if pet is None or not self.can_dispatch_same_spot(spot_id):
            return False
        if not self.can_expedite_again(pid, 0):
            return False
        self.active_expeditions[pid] = spot_id
        return True

    def can_expedite_again(self, pid: str, current_time: float) -> bool:
        """探险返回后宠物有疲劳，需休息恢复才能再派。"""
        pet = self.pets.get(pid)
        if pet is None:
            return False
        return pet.fatigue <= 0

    def rest(self, pid: str, hours: float) -> None:
        """休息恢复疲劳。"""
        pet = self.pets.get(pid)
        if pet is not None:
            pet.fatigue = max(0.0, pet.fatigue - hours * 10)

    def get_pet_bonus(self, pid: str, spot_id: str) -> float:
        """宠物属性（等级/技能/亲密度）影响奖励加成。"""
        pet = self.pets.get(pid)
        if pet is None:
            return 1.0
        return 1.0 + 0.01 * pet.level + 0.005 * pet.skill + 0.005 * pet.intimacy

    def get_reward_rarity(self, spot_id: str) -> dict:
        """奖励稀有度分布：难度越高稀有奖励概率越大。"""
        spot = self.spots[spot_id]
        d = spot.difficulty
        epic = min(0.15, 0.01 * d)
        rare = min(0.30, 0.03 * d)
        uncommon = min(0.40, 0.05 * d)
        common = max(0.0, 1.0 - uncommon - rare - epic)
        return {"common": common, "uncommon": uncommon, "rare": rare, "epic": epic}

    def roll_rarity(self, spot_id: str) -> str:
        """按分布roll稀有度，连续未出稀有有保底（10次必出rare以上）。"""
        dist = self.get_reward_rarity(spot_id)
        pity = self._rare_pity.get(spot_id, 0)
        if pity >= 9:
            result = "rare" if self.rng.random() < 0.8 else "epic"
        else:
            roll = self.rng.random()
            result = "common"
            acc = 0.0
            for tier in ("common", "uncommon", "rare", "epic"):
                acc += dist.get(tier, 0.0)
                if roll < acc:
                    result = tier
                    break
        if result in ("rare", "epic"):
            self._rare_pity[spot_id] = 0
        else:
            self._rare_pity[spot_id] = pity + 1
        return result
