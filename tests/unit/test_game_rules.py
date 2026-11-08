"""Headless tests for pure game rules: win, lose, score, harvest, speed cap."""

import pytest

from quick_herbalist.game_rules import GameRules


@pytest.fixture
def rules():
    """Fresh run with 100m to win, starting speed 3, cap 15."""
    return GameRules(win_distance=100.0, start_speed=3.0, max_speed=15.0)


def test_fresh_run_state(rules):
    """A new run starts at zero score/distance, at starting speed, alive."""
    assert rules.score == 0
    assert rules.distance == 0.0
    assert rules.game_speed == 3.0
    assert not rules.dead
    assert rules.harvest == {}


def test_win_only_at_threshold():
    """step() returns True exactly when win distance is reached."""
    probe = GameRules(win_distance=float("inf"), start_speed=3.0)
    probe.step(0.1)  # distance after one step, speed grown once
    just_below = GameRules(win_distance=probe.distance + 0.01, start_speed=3.0)
    just_above = GameRules(win_distance=probe.distance - 0.01, start_speed=3.0)
    assert not just_below.step(0.1)
    assert just_above.step(0.1)


def test_long_run_wins(rules):
    """Repeated steps eventually reach the win distance."""
    for _ in range(600):
        if rules.step(1.0 / 60):
            break
    assert rules.distance >= rules.win_distance


def test_damage_loses(rules):
    """A damaging hit marks the run lost."""
    rules.on_damaged()
    assert rules.dead


def test_collect_scores_without_losing(rules):
    """Collecting entities raises score but never loses the run."""
    assert rules.on_collected("flower_sprite") == 1
    assert rules.on_collected("flower_sprite") == 2
    assert not rules.dead


def test_collect_tracks_per_sprite_harvest():
    """Harvest counts collected units per sprite name, for mixed flower types."""
    rules = GameRules(win_distance=100.0, start_speed=3.0)
    rules.on_collected("flower_sprite")
    rules.on_collected("flower2_sprite")
    rules.on_collected("flower_sprite")
    assert rules.score == 3
    assert rules.harvest == {"flower_sprite": 2, "flower2_sprite": 1}


def test_speed_grows_per_step(rules):
    """Speed increases as the run progresses."""
    before = rules.game_speed
    rules.step(1.0)
    assert rules.game_speed > before


def test_speed_never_exceeds_cap():
    """Speed grows toward the cap but never goes past it."""
    capped = GameRules(win_distance=float("inf"), start_speed=3.0, max_speed=5.0)
    for _ in range(600):
        capped.step(1.0)
        assert capped.game_speed <= 5.0
    assert capped.game_speed == 5.0
    # Distance keeps growing at the capped speed.
    distance_at_cap = capped.distance
    capped.step(1.0)
    assert capped.distance > distance_at_cap


def test_fresh_instance_resets_between_runs():
    """A new GameRules instance is a reset run, independent of the previous one."""
    first = GameRules(win_distance=100.0, start_speed=3.0)
    first.step(1.0)
    first.on_collected("flower_sprite")
    first.on_damaged()
    second = GameRules(win_distance=100.0, start_speed=3.0)
    assert second.score == 0
    assert second.distance == 0.0
    assert second.game_speed == 3.0
    assert not second.dead
    assert second.harvest == {}
