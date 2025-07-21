import asyncio
import logging
from src.graph import build_graph
from src.config.report_style import ReportStyle
import langchain
langchain.debug = True  # Enable debug mode for LangChain


# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Default level is INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def enable_debug_logging():
    """Enable debug level logging for more detailed execution information."""
    logging.getLogger("src").setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)

# Create the graph
graph = build_graph()
thread_id = "123"
resources = []
max_plan_iterations = 1
max_step_num = 3
max_search_results = 3
auto_accepted_plan = True
interrupt_feedback = ""
mcp_settings = {
    "servers": {
        "corp_valuation": {
            "transport": "sse",
            "url": "http://localhost:8005/mcp",
            "enabled_tools": ["corp_valuation", "fetch_a_stock_data", "fetch_hk_stock_data", "data_analysis"],
            "add_to_agents": ["researcher"],
        }
    }
}
enable_background_investigation = True
report_style = ReportStyle.ACADEMIC
enable_deep_thinking = True

async def run_agent_workflow_async(
    user_input: str,
    debug: bool = False,
    max_plan_iterations: int = 1,
    max_step_num: int = 3,
    enable_background_investigation: bool = True,
):
    """Run the agent workflow asynchronously with the given user input.

    Args:
        user_input: The user's query or request
        debug: If True, enables debug level logging
        max_plan_iterations: Maximum number of plan iterations
        max_step_num: Maximum number of steps in a plan
        enable_background_investigation: If True, performs web search before planning to enhance context

    Returns:
        The final state after the workflow completes
    """
    if not user_input:
        raise ValueError("Input could not be empty")

    if debug:
        enable_debug_logging()

    logger.info(f"Starting async workflow with user input: {user_input}")
    initial_state = {
        # Runtime Variables
        "messages": [{"role": "user", "content": user_input}],
        "auto_accepted_plan": True,
        "enable_background_investigation": enable_background_investigation,
    }
    config = {
        "configurable": {
            "thread_id": "default",
            "max_plan_iterations": max_plan_iterations,
            "max_step_num": max_step_num,
            "mcp_settings": mcp_settings,
            "report_style": report_style.value,
            "enable_deep_thinking": enable_deep_thinking,
        },
        "recursion_limit": 100,
    }
    last_message_cnt = 0
    async for s in graph.astream(
        input=initial_state, config=config, stream_mode="values"
    ):
        try:
            if isinstance(s, dict) and "messages" in s:
                if len(s["messages"]) <= last_message_cnt:
                    continue
                last_message_cnt = len(s["messages"])
                message = s["messages"][-1]
                if isinstance(message, tuple):
                    print(message)
                else:
                    message.pretty_print()
            else:
                # For any other output format
                print(f"Output: {s}")
        except Exception as e:
            logger.error(f"Error processing stream output: {e}")
            print(f"Error processing output: {str(e)}")
    if s.get("final_report"):
        with open("result/final_report.md", "w", encoding="utf-8") as f:
            f.write(s["final_report"])
    logger.info("Async workflow completed successfully")


if __name__ == "__main__":  
    asyncio.run(run_agent_workflow_async("写一份关于生成式AI基建与算力投资趋势（2023-2026）的宏观分析报告"))
