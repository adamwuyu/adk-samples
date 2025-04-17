"""Tools for managing session state in the sequential orchestrator."""

import typing
from google.adk.tools import ToolContext
import logging

logger = logging.getLogger(__name__)

# 定义常量以便复用
INITIAL_MATERIAL_KEY = "initial_material"
INITIAL_REQUIREMENTS_KEY = "initial_requirements"
INITIAL_SCORING_CRITERIA_KEY = "initial_scoring_criteria"

def check_initial_data(tool_context: ToolContext) -> dict[str, str]:
    """Checks if initial_material, initial_requirements, and initial_scoring_criteria are present in the session state.

    Args:
        tool_context: The ADK tool context providing access to session state.

    Returns:
        A dict with 'status': 'ready' if all required keys are present and non-empty,
        'missing_data' otherwise.
    """
    logger.info("Checking for initial data in session state...")
    state = tool_context.state
    material = state.get(INITIAL_MATERIAL_KEY)
    requirements = state.get(INITIAL_REQUIREMENTS_KEY)
    criteria = state.get(INITIAL_SCORING_CRITERIA_KEY)

    if material and requirements and criteria:
        logger.info("Initial data found in session state.")
        return {"status": "ready"}
    else:
        missing_keys = []
        if not material: missing_keys.append(INITIAL_MATERIAL_KEY)
        if not requirements: missing_keys.append(INITIAL_REQUIREMENTS_KEY)
        if not criteria: missing_keys.append(INITIAL_SCORING_CRITERIA_KEY)
        logger.warning(f"Initial data missing in session state. Missing keys: {missing_keys}")
        return {"status": "missing_data"}

def store_initial_data(
    initial_material: str,
    initial_requirements: str,
    initial_scoring_criteria: str,
    tool_context: ToolContext
) -> dict[str, str]:
    """Stores the necessary initial data provided by the user into the session state.

    Args:
        initial_material: The initial material for writing.
        initial_requirements: The requirements for the writing task.
        initial_scoring_criteria: The criteria for scoring the draft.
        tool_context: The ADK tool context, used to access session state.

    Returns:
        A dict with a status message.
    """
    try:
        logger.info(f"Storing initial data into session state: Material='{initial_material[:50]}...', Requirements='{initial_requirements[:50]}...', Criteria='{initial_scoring_criteria[:50]}...'")
        tool_context.state.update({
            INITIAL_MATERIAL_KEY: initial_material,
            INITIAL_REQUIREMENTS_KEY: initial_requirements,
            INITIAL_SCORING_CRITERIA_KEY: initial_scoring_criteria,
        })
        logger.info("Successfully updated session state with initial data.")
        return {"status": "Initial data successfully stored in session state."}
    except Exception as e:
        logger.error(f"Error storing initial data in session state: {e}", exc_info=True)
        return {"status": f"Failed to store initial data due to an error: {e}"} 