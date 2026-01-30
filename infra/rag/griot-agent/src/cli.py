#!/usr/bin/env python3
"""CLI chat interface for the Griot Agent."""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from .agent import GriotAgent
from .config import get_settings
from .mcp_client import RetrievalMCPClient

app = typer.Typer(help="Griot Agent - AI oral historian for the Griot & Grits collection")
console = Console()


def print_welcome():
    """Print welcome message."""
    welcome = """
# Welcome to the Griot

I am the Griot, an AI oral historian for the Griot & Grits collection.

I can help you explore African American history, oral histories, and cultural
artifacts preserved in this archive. Ask me about:

- Historical events like the Great Migration
- Stories and experiences from oral history interviews
- Cultural traditions and community history
- Artifacts and documents in the collection

Type **quit** or **exit** to end the conversation.
Type **clear** to start a new conversation.
Type **sources** to list available sources in the collection.
"""
    console.print(Panel(Markdown(welcome), title="[bold blue]The Griot[/bold blue]", border_style="blue"))


def print_response(response: str):
    """Print the agent's response."""
    console.print()
    console.print(Panel(Markdown(response), title="[bold green]Griot[/bold green]", border_style="green"))
    console.print()


def print_error(message: str):
    """Print an error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


async def interactive_chat():
    """Run the interactive chat loop."""
    print_welcome()

    settings = get_settings()

    # Check if API key is configured
    if not settings.llm_api_key:
        print_error("LLM API key not configured. Set LLAMA_API_KEY in .env.local")
        console.print("Looking for .env.local in:", Path.cwd())
        return

    try:
        async with GriotAgent() as agent:
            console.print("[dim]Connected to retrieval service.[/dim]\n")

            while True:
                try:
                    user_input = Prompt.ask("[bold cyan]You[/bold cyan]")

                    if not user_input.strip():
                        continue

                    lower_input = user_input.lower().strip()

                    if lower_input in ("quit", "exit", "q"):
                        console.print("\n[dim]Thank you for exploring history with me. Goodbye![/dim]")
                        break

                    if lower_input == "clear":
                        agent.clear_history()
                        console.print("[dim]Conversation cleared. Starting fresh.[/dim]\n")
                        continue

                    if lower_input == "sources":
                        console.print("[dim]Fetching sources from collection...[/dim]")
                        try:
                            sources = await agent._mcp_client.list_sources()
                            console.print(Panel(str(sources), title="[bold]Sources in Collection[/bold]"))
                        except Exception as e:
                            print_error(f"Could not fetch sources: {e}")
                        continue

                    if lower_input == "tools":
                        console.print("[dim]Fetching available tools...[/dim]")
                        try:
                            tools = await agent._mcp_client.list_tools()
                            for tool in tools:
                                console.print(f"  - [bold]{tool['name']}[/bold]: {tool['description']}")
                        except Exception as e:
                            print_error(f"Could not fetch tools: {e}")
                        continue

                    # Get response from agent
                    with console.status("[bold green]Searching the collection...[/bold green]"):
                        response = await agent.chat(user_input)

                    print_response(response)

                except KeyboardInterrupt:
                    console.print("\n[dim]Interrupted. Type 'quit' to exit.[/dim]")
                    continue

    except Exception as e:
        print_error(f"Failed to connect: {e}")
        console.print("[dim]Make sure the retrieval-mcp service is running.[/dim]")
        raise


@app.command()
def chat():
    """Start an interactive chat session with the Griot."""
    asyncio.run(interactive_chat())


@app.command()
def search(query: str, top_k: int = 5):
    """Search the collection directly."""

    async def do_search():
        settings = get_settings()
        async with RetrievalMCPClient(settings.retrieval_mcp_url) as client:
            results = await client.search(query, top_k=top_k)
            console.print(Panel(str(results), title=f"[bold]Search: {query}[/bold]"))

    asyncio.run(do_search())


@app.command()
def list_tools():
    """List available MCP tools."""

    async def do_list():
        settings = get_settings()
        async with RetrievalMCPClient(settings.retrieval_mcp_url) as client:
            tools = await client.list_tools()
            console.print("[bold]Available Tools:[/bold]")
            for tool in tools:
                console.print(f"  - [bold]{tool['name']}[/bold]: {tool['description']}")

    asyncio.run(do_list())


@app.command()
def config():
    """Show current configuration."""
    settings = get_settings()
    console.print("[bold]Current Configuration:[/bold]")
    console.print(f"  LLM URL: {settings.llm_api_url}")
    console.print(f"  LLM Model: {settings.llm_model}")
    console.print(f"  LLM API Key: {'[set]' if settings.llm_api_key else '[not set]'}")
    console.print(f"  Retrieval MCP: {settings.retrieval_mcp_url}")
    console.print(f"  Default Collection: {settings.default_collection}")


def main():
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
