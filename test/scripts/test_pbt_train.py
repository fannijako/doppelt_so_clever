from unittest.mock import patch

import pytest
import torch

from scripts.pbt_train_rl import (
    ExploitConfig,
    PBTConfig,
    _compute_pbt_state_size,
    _create_agent,
    _evaluate_population,
    _exploit_and_explore,
    _fitness,
    _load_warm_start_state,
)


def _population(size: int, config: PBTConfig):
    return [_create_agent(i, config) for i in range(size)]


class TestFitnessMetric:
    def test_mean_metric(self):
        assert _fitness([100, 200], "mean") == 150.0

    def test_p10_metric_picks_low_quantile(self):
        assert _fitness(list(range(1, 101)), "p10") == 11.0


class TestEvaluatePopulationFitness:
    def test_p10_metric_sets_fitness(self):
        config = PBTConfig(population_size=1, exploit=ExploitConfig(metric="p10"))
        population = _population(1, config)
        with patch("scripts.pbt_train_rl.collect_batch", return_value=([], list(range(1, 101)))):
            _evaluate_population(population, config)
        assert population[0].fitness == 11.0


class TestExploitRanksByFitness:
    def test_weak_fitness_agent_overwritten_by_strong(self):
        config = PBTConfig(population_size=2)
        population = _population(2, config)
        population[0].fitness, population[0].mean_score = 200.0, 10.0
        population[1].fitness, population[1].mean_score = 10.0, 200.0
        _exploit_and_explore(population, config)
        key = next(iter(population[0].policy.state_dict()))
        assert torch.equal(
            population[1].policy.state_dict()[key],
            population[0].policy.state_dict()[key],
        )


class TestWarmStartValidation:
    def test_raises_on_state_size_mismatch(self):
        config = PBTConfig(warm_start="dummy.pt")
        checkpoint = {"policy_state_dict": {}, "state_size": _compute_pbt_state_size(config.shared) - 1}
        with patch("scripts.pbt_train_rl.torch.load", return_value=checkpoint):
            with pytest.raises(ValueError):
                _load_warm_start_state(config)

    def test_returns_state_dict_on_match(self):
        config = PBTConfig(warm_start="dummy.pt")
        state = {"trunk.0.weight": torch.zeros(1)}
        checkpoint = {
            "policy_state_dict": state,
            "state_size": _compute_pbt_state_size(config.shared),
            "best_eval_score": 166.0,
        }
        with patch("scripts.pbt_train_rl.torch.load", return_value=checkpoint):
            assert _load_warm_start_state(config) is state
