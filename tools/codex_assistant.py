#!/usr/bin/env python3
"""
Interactive OpenAI Codex Assistant for Home Assistant Configuration Management.

An interactive AI assistant powered by OpenAI that helps manage Home Assistant
configurations, similar to Claude Code but using OpenAI's API.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI package not installed. Run: pip install openai")
    sys.exit(1)


class CodexAssistant:
    """Interactive OpenAI assistant with function calling capabilities."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        project_root: Path = Path.cwd(),
    ):
        """Initialize the Codex assistant.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            project_root: Root directory of the project
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable."
            )

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4")
        self.project_root = Path(project_root)
        self.client = OpenAI(api_key=self.api_key)
        self.conversation_history: List[Dict[str, Any]] = []

        # Load system instructions from AGENTS.md
        self.system_instructions = self._load_system_instructions()

        # Initialize conversation with system message
        self.conversation_history.append({
            "role": "system",
            "content": self.system_instructions
        })

    def _load_system_instructions(self) -> str:
        """Load system instructions from AGENTS.md file."""
        agents_md_path = self.project_root / "AGENTS.md"

        if agents_md_path.exists():
            with open(agents_md_path, "r") as f:
                return f.read()
        else:
            return "You are a helpful AI assistant for Home Assistant configuration management."

    def _get_function_definitions(self) -> List[Dict]:
        """Define available functions for function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to read (absolute or relative to project root)"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file (creates or overwrites)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to write"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file"
                            }
                        },
                        "required": ["file_path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edit a file by replacing old content with new content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to edit"
                            },
                            "old_content": {
                                "type": "string",
                                "description": "Content to search for and replace"
                            },
                            "new_content": {
                                "type": "string",
                                "description": "New content to replace with"
                            }
                        },
                        "required": ["file_path", "old_content", "new_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_command",
                    "description": "Execute a shell command in the project directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "List contents of a directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "Path to directory (default: project root)"
                            }
                        },
                        "required": []
                    }
                }
            }
        ]

    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to project root."""
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        return (self.project_root / path_obj).resolve()

    def read_file(self, file_path: str) -> str:
        """Read and return file contents."""
        try:
            resolved_path = self._resolve_path(file_path)
            with open(resolved_path, "r") as f:
                content = f.read()
            return f"File: {file_path}\n\n{content}"
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"

    def write_file(self, file_path: str, content: str) -> str:
        """Write content to a file."""
        try:
            resolved_path = self._resolve_path(file_path)
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            with open(resolved_path, "w") as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing to file {file_path}: {str(e)}"

    def edit_file(self, file_path: str, old_content: str, new_content: str) -> str:
        """Edit a file by replacing old content with new content."""
        try:
            resolved_path = self._resolve_path(file_path)
            with open(resolved_path, "r") as f:
                current_content = f.read()

            if old_content not in current_content:
                return f"Error: Could not find specified content in {file_path}"

            updated_content = current_content.replace(old_content, new_content, 1)

            with open(resolved_path, "w") as f:
                f.write(updated_content)

            return f"Successfully edited {file_path}"
        except Exception as e:
            return f"Error editing file {file_path}: {str(e)}"

    def execute_command(self, command: str) -> str:
        """Execute a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            output = []
            if result.stdout:
                output.append(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                output.append(f"STDERR:\n{result.stderr}")
            output.append(f"Exit code: {result.returncode}")

            return "\n\n".join(output)
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 120 seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def list_directory(self, directory_path: str = ".") -> str:
        """List contents of a directory."""
        try:
            resolved_path = self._resolve_path(directory_path)
            if not resolved_path.is_dir():
                return f"Error: {directory_path} is not a directory"

            items = []
            for item in sorted(resolved_path.iterdir()):
                item_type = "DIR" if item.is_dir() else "FILE"
                items.append(f"[{item_type}] {item.name}")

            return f"Contents of {directory_path}:\n" + "\n".join(items)
        except Exception as e:
            return f"Error listing directory {directory_path}: {str(e)}"

    def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a function call."""
        if function_name == "read_file":
            return self.read_file(arguments["file_path"])
        elif function_name == "write_file":
            return self.write_file(arguments["file_path"], arguments["content"])
        elif function_name == "edit_file":
            return self.edit_file(
                arguments["file_path"],
                arguments["old_content"],
                arguments["new_content"]
            )
        elif function_name == "execute_command":
            return self.execute_command(arguments["command"])
        elif function_name == "list_directory":
            return self.list_directory(arguments.get("directory_path", "."))
        else:
            return f"Error: Unknown function {function_name}"

    def chat(self, user_message: str) -> str:
        """Send a message and get a response, handling function calls."""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        try:
            # Call OpenAI API with function calling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                tools=self._get_function_definitions(),
                tool_choice="auto",
                temperature=0.7,
            )

            response_message = response.choices[0].message

            # Handle function calls
            if response_message.tool_calls:
                # Add assistant's response (with function calls) to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                        for tool_call in response_message.tool_calls
                    ]
                })

                # Execute all function calls
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    print(f"  → Executing: {function_name}({json.dumps(function_args)})")

                    function_response = self._execute_function(function_name, function_args)

                    # Add function response to history
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": function_response
                    })

                # Get final response after function calls
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,
                    tools=self._get_function_definitions(),
                    tool_choice="auto",
                    temperature=0.7,
                )

                final_message = second_response.choices[0].message

                # Check if there are more function calls (recursive handling)
                if final_message.tool_calls:
                    # Recursively handle additional function calls
                    return self.chat("")  # Empty message to continue processing

                # Add final response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_message.content
                })

                return final_message.content or "(No response)"

            else:
                # No function calls, just return the response
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_message.content
                })

                return response_message.content or "(No response)"

        except Exception as e:
            error_msg = f"Error calling OpenAI API: {str(e)}"
            print(f"  ✗ {error_msg}")
            return error_msg


def main():
    """Run the interactive Codex assistant."""
    print("=" * 80)
    print("OpenAI Codex Assistant - Home Assistant Configuration Management")
    print("=" * 80)
    print()

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print()
        print("To use this assistant:")
        print("1. Get an API key from https://platform.openai.com/api-keys")
        print("2. Add to your .env file: OPENAI_API_KEY=your-key-here")
        print("3. Or export it: export OPENAI_API_KEY='your-key-here'")
        return

    # Initialize assistant
    try:
        model = os.getenv("OPENAI_MODEL", "gpt-4")
        print(f"Initializing assistant with model: {model}")
        print(f"Project directory: {Path.cwd()}")
        print()

        assistant = CodexAssistant(model=model)
        print("✓ Assistant initialized successfully!")
        print()
        print("Type your questions or commands. Special commands:")
        print("  /help    - Show available commands")
        print("  /history - Show conversation history")
        print("  /clear   - Clear conversation history")
        print("  /quit    - Exit the assistant")
        print()
        print("-" * 80)
        print()

    except ValueError as e:
        print(f"Error: {e}")
        return
    except Exception as e:
        print(f"Error initializing assistant: {e}")
        return

    # REPL loop
    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input == "/quit":
                print("\nGoodbye!")
                break

            elif user_input == "/help":
                print("\nAvailable commands:")
                print("  /help    - Show this help message")
                print("  /history - Show conversation history (message count)")
                print("  /clear   - Clear conversation history")
                print("  /quit    - Exit the assistant")
                print("\nAsk me anything about Home Assistant configuration!")
                print("Examples:")
                print("  - Create an automation to turn on lights at sunset")
                print("  - What entities are available in the kitchen?")
                print("  - Run validation on my configs")
                print("  - Show me the current automations")
                print()
                continue

            elif user_input == "/history":
                msg_count = len([m for m in assistant.conversation_history if m["role"] in ["user", "assistant"]])
                print(f"\nConversation history: {msg_count} messages")
                print()
                continue

            elif user_input == "/clear":
                assistant.conversation_history = [{
                    "role": "system",
                    "content": assistant.system_instructions
                }]
                print("\n✓ Conversation history cleared")
                print()
                continue

            # Get response from assistant
            print()
            response = assistant.chat(user_input)
            print(f"Assistant: {response}")
            print()
            print("-" * 80)
            print()

        except KeyboardInterrupt:
            print("\n\nInterrupted. Type /quit to exit.")
            print()
        except EOFError:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print()


if __name__ == "__main__":
    main()
