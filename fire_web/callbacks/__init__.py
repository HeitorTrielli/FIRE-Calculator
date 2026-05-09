"""Dash callbacks split by UI area; importing registers them with the active Dash app."""


def register_callbacks() -> None:
    import fire_web.callbacks.life_event_ui  # noqa: F401
    import fire_web.callbacks.scenario_ui  # noqa: F401
    import fire_web.callbacks.simulation_ui  # noqa: F401
