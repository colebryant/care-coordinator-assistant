import json
import logging
import re
from typing import Any, Dict, Optional

from config import settings
from IPython.display import Image
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from tools import tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_agent():
    """Agent graph using ReAct pattern."""
    llm = ChatOpenAI(model=settings.MODEL_NAME, temperature=settings.MODEL_TEMPERATURE)
    llm_with_tools = llm.bind_tools(tools)
    system_prompt = SystemMessage(content=settings.SYSTEM_PROMPT)

    def call_model(state: MessagesState):
        response = llm_with_tools.invoke([system_prompt] + state["messages"])
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition)
    graph.add_edge("tools", "model")
    graph.add_edge("model", END)

    memory = MemorySaver()
    agent = graph.compile(checkpointer=memory)

    img = Image(agent.get_graph().draw_mermaid_png())
    with open("workflow.png", "wb") as f:
        f.write(img.data)

    return agent


agent = build_agent()


def set_patient_context(thread_id: str, data: dict, reset: bool = True) -> bool:
    """Inject patient context as a SystemMessage into the given thread. Optionally reset thread first."""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        if reset:
            agent.update_state(config, MessagesState(messages=[]))
        note = {"patient_context": data}
        agent.update_state(
            config,
            MessagesState(messages=[SystemMessage(content=json.dumps(note))]),
        )
        return True
    except Exception as e:
        logger.error(f"Failed to set patient context for thread {thread_id}: {e}")
        return False


def run_message(
    message: str, thread_id: Optional[str] = None, reset: bool = False
) -> Dict[str, Any]:
    if thread_id is None:
        thread_id = "default"

    config = {"configurable": {"thread_id": thread_id}}

    # Hard reset thread memory
    if reset:
        try:
            agent.update_state(config, MessagesState(messages=[]))
            logger.info(f"Reset thread: {thread_id}")
        except Exception as e:
            logger.error(f"Error resetting thread {thread_id}: {e}")

    initial_state = MessagesState(messages=[HumanMessage(content=message)])
    result = agent.invoke(initial_state, config=config)

    reply = ""
    for msg in reversed(result["messages"]):
        if msg.type == "ai":
            reply = msg.content
            break
    return {"reply": reply}


def run_message_stream(
    message: str, thread_id: Optional[str] = None, reset: bool = False
):
    result = run_message(message, thread_id, reset)
    response = result["reply"]

    # Simulate streaming for client
    tokens = re.split(r"(\s+)", response)
    for i, token in enumerate(tokens):
        if i == 0:
            yield token
        else:
            yield token
