from ..tools.check_initial_data import check_initial_data
from ..tools.save_draft_result import save_draft_result
from ..tools.save_score import save_score
from ..tools.check_progress import check_progress
from ..tools.get_final_draft import get_final_draft
from .agents_registry import make_tool_agent

check_initial_data_agent = make_tool_agent("check_initial_data", check_initial_data)
save_draft_result_agent = make_tool_agent("save_draft_result", save_draft_result)
save_score_agent = make_tool_agent("save_score", save_score)
check_progress_agent = make_tool_agent("check_progress", check_progress)
get_final_draft_agent = make_tool_agent("get_final_draft", get_final_draft) 