"""Shared adapter factory — returns the configured DataSourceAdapter."""

from app.config import settings


def get_adapter():
    """Get the data source adapter (ProfitSword or Mock) based on settings."""
    if settings.environment == "development" and not settings.profitsword_username:
        from app.adapters.mock_adapter import MockAdapter
        return MockAdapter()

    from app.adapters.mapping import MappingEngine
    from app.adapters.profitsword import ProfitSwordAdapter
    mapping = MappingEngine.default()
    return ProfitSwordAdapter(
        base_url=settings.profitsword_base_url,
        username=settings.profitsword_username,
        password=settings.profitsword_password,
        mapping=mapping,
        dataset_actuals=settings.profitsword_dataset_actuals,
        dataset_budget=settings.profitsword_dataset_budget,
        dataset_forecast=settings.profitsword_dataset_forecast,
    )
