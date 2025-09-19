"""Blueprint generator module for Nova Blueprints.

Provides functions to generate agent blueprints and list available blueprints.
"""

# Predefined blueprint templates for different agent roles
BLUEPRINTS = {
    "planner": {
        "description": "Plans tasks and coordinates sub-agents",
        "parameters": {},
    },
    "coder": {
        "description": "Writes code based on specifications",
        "parameters": {},
    },
    "tester": {
        "description": "Tests the code for bugs and issues",
        "parameters": {},
    },
    "ops": {
        "description": "Handles deployment and operations tasks",
        "parameters": {},
    },
}


def generate_blueprint(agent_type: str) -> dict:
    """Return a blueprint dictionary for the specified agent type.

    If the agent type is not recognized, returns a default blueprint with an
    unknown description.

    Args:
        agent_type: The type of agent for which to generate a blueprint.

    Returns:
        A dictionary containing the blueprint definition.
    """
    return BLUEPRINTS.get(
        agent_type,
        {"description": "Unknown agent type", "parameters": {}},
    )


def list_blueprints() -> list:
    """List available blueprint names.

    Returns:
        A list of keys representing available blueprint types.
    """
    return list(BLUEPRINTS.keys())
