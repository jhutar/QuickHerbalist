"""Headless tests for pure game rules: win, lose, speed cap, fresh-run reset."""

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


def test_stone_hit_loses(rules):
    """A stone collision marks the run lost."""
    rules.on_stone_hit()
    assert rules.dead


def test_flower_hit_scores_without_losing(rules):
    """Collecting flowers raises score but never loses the run."""
    assert rules.on_flower_hit() == 1
    assert rules.on_flower_hit() == 2
    assert not rules.dead


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
    first.on_flower_hit()
    first.on_stone_hit()
    second = GameRules(win_distance=100.0, start_speed=3.0)
    assert second.score == 0
    assert second.distance == 0.0
    assert second.game_speed == 3.0
    assert not second.dead


def test_next_stone_interval_first_call_returns_start_interval():
    """The first stone spawn waits the full starting interval."""
    rules = GameRules(win_distance=100.0, start_speed=3.0, stone_interval=3.0)
    assert rules.next_stone_interval() == 3.0


def test_stone_interval_ramps_down_to_floor():
    """Repeated calls decay the interval toward stone_interval_min, never below."""
    rules = GameRules(
        win_distance=100.0,
        start_speed=3.0,
        stone_interval=3.0,
        stone_interval_min=0.05,
    )
    for _ in range(1000):
        delay = rules.next_stone_interval()
        assert delay >= 0.05
    assert rules.stone_interval == 0.05


def test_stone_interval_never_increases():
    """Ramping only shrinks the interval; it never grows back."""
    rules = GameRules(
        win_distance=100.0,
        start_speed=3.0,
        stone_interval=3.0,
        stone_interval_min=0.05,
    )
    previous = 3.0
    for _ in range(200):
        delay = rules.next_stone_interval()
        assert delay <= previous
        previous = delay


def test_no_ramp_when_min_absent():
    """Without stone_interval_min the interval stays constant (no ramp)."""
    rules = GameRules(win_distance=100.0, start_speed=3.0, stone_interval=2.5)
    for _ in range(50):
        assert rules.next_stone_interval() == 2.5
    assert rules.stone_interval == 2.5
