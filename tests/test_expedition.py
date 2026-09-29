"""宠物探险与派遣系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pet.expedition import ExpeditionSystem, ExpeditionSpot, Pet

class TestRewardBySpot:
    def test_different_spots_different_rewards(self):
        es = ExpeditionSystem()
        es.spots["s1"] = ExpeditionSpot("s1", "forest", 1, 10, 60, rewards={"herb": 10})
        es.spots["s2"] = ExpeditionSpot("s2", "dragon_lair", 10, 60, 300, rewards={"gem": 1})
        r1 = es.get_rewards("s1")
        r2 = es.get_rewards("s2")
        assert r1 != r2  # bug1: 都是gold:100

class TestOptimalTime:
    def test_expedition_has_optimal_duration(self):
        es = ExpeditionSystem()
        es.spots["s1"] = ExpeditionSpot("s1", "forest", 1, 10, 60)
        t = es.get_optimal_time("s1")
        assert t < float("inf") and t > 0  # bug2: inf

class TestFailureRate:
    def test_high_difficulty_has_failure_risk(self):
        es = ExpeditionSystem()
        es.spots["s1"] = ExpeditionSpot("s1", "dragon", 10, 60, 300)
        rate = es.get_failure_rate("s1", pet_level=1)
        assert rate > 0  # bug3: 0

class TestSameSpotLimit:
    def test_only_one_pet_per_spot(self):
        es = ExpeditionSystem()
        es.active_expeditions["p1"] = "s1"
        assert es.can_dispatch_same_spot("s1") == False  # bug4: True

class TestFatigueCooldown:
    def test_pet_needs_rest_after_expedition(self):
        es = ExpeditionSystem()
        es.pets["p1"] = Pet("p1", "pet", fatigue=100)
        assert es.can_expedite_again("p1", 0) == False  # bug5: True

class TestPetBonus:
    def test_high_level_pet_gets_bonus(self):
        es = ExpeditionSystem()
        es.pets["p1"] = Pet("p1", "pet", level=1)
        es.pets["p2"] = Pet("p2", "pet", level=100)
        b1 = es.get_pet_bonus("p1", "s1")
        b2 = es.get_pet_bonus("p2", "s1")
        assert b2 > b1  # bug6: 都是1.0

class TestRewardRarity:
    def test_rewards_have_rarity_distribution(self):
        es = ExpeditionSystem()
        es.spots["s1"] = ExpeditionSpot("s1", "dragon", 10, 60, 300)
        rarity = es.get_reward_rarity("s1")
        assert "rare" in rarity or "epic" in rarity  # bug7: 只有common
