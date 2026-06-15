from scripts.agent_efficiency import calculate_rotation, ProviderQuota


def test_rotation_allocates_daily_capacity():
    providers = [
        ProviderQuota(name="a", model="m", enabled=True, rpm=10, daily_requests=100, cost_tier="free"),
        ProviderQuota(name="b", model="m", enabled=True, rpm=5, daily_requests=50, cost_tier="free"),
    ]
    result = calculate_rotation(providers, desired_rpm=0.05, desired_daily_requests=120)
    assert result["known_total_daily_requests"] == 150
    assert result["uncovered_daily_requests"] == 0
    assert len(result["plan"]) == 2
