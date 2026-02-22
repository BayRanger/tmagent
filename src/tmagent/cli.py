"""TinyAgent CLI - Simple command-line interface."""

import argparse
import asyncio
from pathlib import Path

from .agent import Agent
from .llm import LLMClient
from .schema import LLMProvider
from .tools import BashTool, EditTool, ReadTool, WriteTool


DEFAULT_SYSTEM_PROMPT = """You are TinyAgent, an AI assistant that can help users complete tasks.

You have access to tools to:
- read_file: Read file contents
- write_file: Write content to files
- edit_file: Edit files by replacing text
- bash: Execute shell commands

Use these tools to help users with their tasks."""


async def run_agent(workspace_dir: Path, api_key: str, model: str, provider: str, task: str = None):
    """Run the agent."""

    # Determine provider
    llm_provider = LLMProvider.ANTHROPIC if provider.lower() == "anthropic" else LLMProvider.OPENAI

    # Create LLM client
    llm_client = LLMClient(
        api_key=api_key,
        provider=llm_provider,
        api_base="https://api.minimaxi.com",
        model=model,
    )

    # Create tools
    tools = [
        ReadTool(workspace_dir=str(workspace_dir)),
        WriteTool(workspace_dir=str(workspace_dir)),
        EditTool(workspace_dir=str(workspace_dir)),
        BashTool(workspace_dir=str(workspace_dir)),
    ]

    # Create agent
    agent = Agent(
        llm_client=llm_client,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        tools=tools,
        workspace_dir=str(workspace_dir),
    )

    if task:
        # Non-interactive mode: execute single task
        print(f"Executing task: {task}\n")
        agent.add_user_message(task)
        result = await agent.run()
        print(f"\n=== Final Result ===\n{result}")
    else:
        # Interactive mode
        print("TinyAgent - Interactive Mode")
        print("Type 'exit' to quit\n")

        while True:
            try:
                user_input = input("You › ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break

                agent.add_user_message(user_input)
                result = await agent.run()
                print(f"\n=== Result ===\n{result}\n")

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="TinyAgent - Minimal AI Agent")
    parser.add_argument("--workspace", "-w", type=str, default="./workspace", help="Workspace directory")
    parser.add_argument("--api-key", type=str, required=True, help="API key for LLM")
    parser.add_argument("--model", type=str, default="MiniMax-M2.5", help="Model name")
    parser.add_argument("--provider", type=str, default="anthropic", choices=["anthropic", "openai"], help="LLM provider")
    parser.add_argument("--task", "-t", type=str, help="Execute a single task and exit")

    args = parser.parse_args()

    workspace_dir = Path(args.workspace).absolute()
    workspace_dir.mkdir(parents=True, exist_ok=True)

    asyncio.run(run_agent(workspace_dir, args.api_key, args.model, args.provider, args.task))


if __name__ == "__main__":
    main()
