from matchlens.limits import ModelBudget


def test_model_budget_limits_bursts_and_total_session_work():
    budget = ModelBudget(per_minute=2, total=3)
    assert budget.acquire(0)
    assert budget.acquire(1)
    assert not budget.acquire(2)
    assert budget.acquire(61)
    assert not budget.acquire(122)


def test_zero_budget_disables_model_work():
    assert not ModelBudget(per_minute=5, total=0).acquire(0)
