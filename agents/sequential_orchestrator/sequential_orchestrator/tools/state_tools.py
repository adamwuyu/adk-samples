"""Tools for managing session state in the sequential orchestrator."""

import typing
from google.adk.tools import ToolContext
import logging

logger = logging.getLogger(__name__)

# 定义常量以便复用
INITIAL_MATERIAL_KEY = "initial_material"
INITIAL_REQUIREMENTS_KEY = "initial_requirements"
INITIAL_SCORING_CRITERIA_KEY = "initial_scoring_criteria"

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