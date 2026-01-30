"""LangGraph-based Griot Agent with tool calling."""

import json
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from .config import get_settings
from .mcp_client import RetrievalMCPClient
from .prompts import GRIOT_SYSTEM_PROMPT, SEARCH_TOOL_DESCRIPTION


class AgentState(TypedDict):
    """State for the agent graph."""

    messages: Annotated[list, add_messages]
    mcp_client: RetrievalMCPClient | None


# Define the search tool schema for the LLM
SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_collection",
        "description": SEARCH_TOOL_DESCRIPTION,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant documents",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}


def create_llm():
    """Create the LLM instance configured for Llama-4-Scout."""
    settings = get_settings()
    return ChatOpenAI(
        base_url=settings.llm_api_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )


async def call_model(state: AgentState) -> AgentState:
    """Call the LLM with the current messages."""
    llm = create_llm()
    llm_with_tools = llm.bind_tools([SEARCH_TOOL_SCHEMA])

    messages = state["messages"]

    # Add system message if not present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=GRIOT_SYSTEM_PROMPT)] + messages

    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


async def execute_tools(state: AgentState) -> AgentState:
    """Execute any tool calls from the LLM response."""
    messages = state["messages"]
    last_message = messages[-1]

    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    tool_messages = []
    mcp_client = state.get("mcp_client")

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        if tool_name == "search_collection":
            try:
                if mcp_client:
                    # Use the MCP client to search
                    result = await mcp_client.search(
                        query=tool_args.get("query", ""),
                        top_k=tool_args.get("top_k", 5),
                    )
                    # Format the result for the LLM
                    if isinstance(result, list):
                        formatted = format_search_results(result)
                    else:
                        formatted = str(result)
                else:
                    formatted = "Error: MCP client not connected. Cannot search collection."
            except Exception as e:
                formatted = f"Error searching collection: {str(e)}"

            tool_messages.append(
                ToolMessage(
                    content=formatted,
                    tool_call_id=tool_id,
                    name=tool_name,
                )
            )
        else:
            tool_messages.append(
                ToolMessage(
                    content=f"Unknown tool: {tool_name}",
                    tool_call_id=tool_id,
                    name=tool_name,
                )
            )

    return {"messages": tool_messages}


def format_search_results(results: list) -> str:
    """Format search results for the LLM."""
    if not results:
        return "No results found in the collection for this query."

    formatted_parts = ["Search Results:\n"]

    for i, result in enumerate(results, 1):
        # Handle different result formats
        if isinstance(result, dict):
            text = result.get("text", result.get("content", str(result)))
            source = result.get("source", result.get("document_id", "Unknown source"))
            score = result.get("score", result.get("similarity", None))

            formatted_parts.append(f"[{i}] Source: {source}")
            if score is not None:
                formatted_parts.append(f"    Relevance: {score:.2f}")
            formatted_parts.append(f"    Content: {text[:500]}...")
            formatted_parts.append("")
        else:
            formatted_parts.append(f"[{i}] {str(result)[:500]}")
            formatted_parts.append("")

    return "\n".join(formatted_parts)


def should_continue(state: AgentState) -> str:
    """Determine if we should continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END


def create_agent_graph():
    """Create the LangGraph agent."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", execute_tools)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()


class GriotAgent:
    """High-level interface for the Griot agent."""

    def __init__(self):
        """Initialize the agent."""
        self.graph = create_agent_graph()
        self.conversation_history: list = []
        self._mcp_client: RetrievalMCPClient | None = None

    async def __aenter__(self):
        """Enter async context and connect MCP client."""
        settings = get_settings()
        self._mcp_client = RetrievalMCPClient(settings.retrieval_mcp_url)
        await self._mcp_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self._mcp_client:
            await self._mcp_client.__aexit__(exc_type, exc_val, exc_tb)

    async def chat(self, user_message: str) -> str:
        """Send a message and get a response.

        Args:
            user_message: The user's message

        Returns:
            The agent's response
        """
        # Add user message to history
        self.conversation_history.append(HumanMessage(content=user_message))

        # Create initial state
        state = {
            "messages": self.conversation_history.copy(),
            "mcp_client": self._mcp_client,
        }

        # Run the graph
        result = await self.graph.ainvoke(state)

        # Extract the final response
        final_messages = result["messages"]
        for msg in reversed(final_messages):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                self.conversation_history.append(msg)
                return msg.content

        # Fallback if no clean response found
        last_ai = [m for m in final_messages if isinstance(m, AIMessage)]
        if last_ai:
            response = last_ai[-1].content or "I apologize, but I couldn't formulate a response."
            self.conversation_history.append(last_ai[-1])
            return response

        return "I apologize, but I encountered an issue processing your request."

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []


async def test_agent():
    """Test the agent with a sample query."""
    async with GriotAgent() as agent:
        response = await agent.chat("What can you tell me about the Great Migration?")
        print(f"Griot: {response}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_agent())
