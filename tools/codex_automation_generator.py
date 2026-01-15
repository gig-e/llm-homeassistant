#!/usr/bin/env python3
"""
OpenAI Codex Home Assistant Automation Generator.

Generate Home Assistant automations using OpenAI's API (GPT-4/GPT-3.5).
Integrates with entity registry for context-aware generation and validates
output using existing validation tools.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI package not installed. Run: pip install openai")
    sys.exit(1)

# Import local tools
try:
    from entity_explorer import (
        categorize_entities,
        load_area_registry,
        load_entity_registry,
    )
    from yaml_validator import validate_yaml_content
except ImportError:
    print("Error: Could not import local tools. Make sure you're in the right directory.")
    sys.exit(1)


class CodexAutomationGenerator:
    """Generate Home Assistant automations using OpenAI's API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        config_path: Path = Path("config"),
    ):
        """Initialize the generator.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use (gpt-4, gpt-3.5-turbo, etc.)
            config_path: Path to Home Assistant config directory
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4")
        self.config_path = config_path
        self.client = OpenAI(api_key=self.api_key)

        # Load entity context
        self.entity_context = self._load_entity_context()

    def _load_entity_context(self) -> Dict:
        """Load entity registry and area information for context."""
        registry = load_entity_registry(self.config_path)
        if not registry:
            print("Warning: Could not load entity registry. Context will be limited.")
            return {}

        area_names = load_area_registry(self.config_path)
        entities = registry.get("data", {}).get("entities", [])
        categorized = categorize_entities(entities, area_names)

        return {
            "areas": list(categorized["by_area"].keys()),
            "domains": list(categorized["by_domain"].keys()),
            "automation_relevant": categorized["automation_relevant"],
            "total_entities": sum(
                len(ents) for ents in categorized["by_domain"].values()
            ),
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt with Home Assistant context."""
        prompt = """You are an expert Home Assistant automation generator. Your task is to generate valid Home Assistant automation YAML based on user descriptions.

## Key Requirements:
1. Generate ONLY valid Home Assistant automation YAML
2. Use proper YAML syntax with correct indentation
3. Follow Home Assistant automation schema exactly
4. Include id, alias, and description fields
5. Use realistic entity_ids that match the naming convention
6. Include appropriate triggers, conditions (if needed), and actions
7. Add helpful comments for complex logic

## Home Assistant Automation Structure:
```yaml
- id: 'unique_automation_id'
  alias: 'Human Readable Name'
  description: 'Brief description of what this does'
  trigger:
    - platform: state|time|sun|etc
      entity_id: sensor.example  # if applicable
      # ... trigger-specific fields
  condition:  # optional
    - condition: state|time|numeric_state|etc
      # ... condition fields
  action:
    - service: light.turn_on|switch.turn_off|etc
      target:
        entity_id: light.example
      data:  # optional
        brightness_pct: 75
```

## Entity Naming Convention:
This Home Assistant instance uses: `location_room_device_sensor`
Examples:
- binary_sensor.home_basement_motion
- climate.home_living_room_heatpump
- light.office_kitchen_main
- media_player.home_bedroom_sonos
- lock.home_front_door

"""

        # Add available context
        if self.entity_context:
            prompt += f"\n## Available Context:\n"
            prompt += f"- Total Entities: {self.entity_context.get('total_entities', 'unknown')}\n"
            prompt += f"- Areas: {', '.join(self.entity_context.get('areas', [])[:10])}\n"
            prompt += f"- Domains: {', '.join(self.entity_context.get('domains', []))}\n"

            # Add examples of automation-relevant entities
            automation_relevant = self.entity_context.get("automation_relevant", {})
            if automation_relevant:
                prompt += "\n## Example Available Entities:\n"
                for domain, entities in list(automation_relevant.items())[:5]:
                    entity_ids = [e["entity_id"] for e in entities[:3]]
                    prompt += f"- {domain}: {', '.join(entity_ids)}\n"

        prompt += """
## Important Guidelines:
- Use entity_ids that follow the naming convention shown above
- Generate complete, working automations
- Include error handling when appropriate
- Use descriptive aliases and add comments
- Validate trigger platforms (state, time, sun, numeric_state, etc.)
- Ensure service calls match entity domains
- Use proper YAML formatting (2-space indentation)

Generate ONLY the YAML automation(s). Do NOT include explanations, markdown code blocks, or additional text.
"""

        return prompt

    def generate_automation(
        self,
        description: str,
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> Optional[str]:
        """Generate an automation from a natural language description.

        Args:
            description: Natural language description of the automation
            temperature: Sampling temperature (0.0-2.0, lower = more deterministic)
            max_tokens: Maximum tokens in response

        Returns:
            Generated YAML automation string, or None if generation failed
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {
                        "role": "user",
                        "content": f"Generate a Home Assistant automation for: {description}",
                    },
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            generated = response.choices[0].message.content.strip()

            # Clean up markdown code blocks if present
            if generated.startswith("```yaml"):
                generated = generated[7:]
            if generated.startswith("```"):
                generated = generated[3:]
            if generated.endswith("```"):
                generated = generated[:-3]

            return generated.strip()

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None

    def validate_automation(self, yaml_content: str) -> tuple[bool, List[str]]:
        """Validate the generated automation YAML.

        Args:
            yaml_content: YAML content to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Validate YAML syntax
        try:
            yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {e}")
            return False, errors

        # Validate Home Assistant specific requirements
        try:
            automations = yaml.safe_load(yaml_content)
            if not isinstance(automations, list):
                automations = [automations]

            for i, automation in enumerate(automations):
                if not isinstance(automation, dict):
                    errors.append(f"Automation {i+1}: Not a valid dictionary")
                    continue

                # Check required fields
                if "id" not in automation:
                    errors.append(f"Automation {i+1}: Missing required 'id' field")
                if "alias" not in automation:
                    errors.append(f"Automation {i+1}: Missing required 'alias' field")
                if "trigger" not in automation:
                    errors.append(f"Automation {i+1}: Missing required 'trigger' field")
                if "action" not in automation:
                    errors.append(f"Automation {i+1}: Missing required 'action' field")

                # Validate trigger structure
                if "trigger" in automation:
                    triggers = automation["trigger"]
                    if not isinstance(triggers, list):
                        errors.append(
                            f"Automation {i+1}: 'trigger' must be a list"
                        )
                    else:
                        for j, trigger in enumerate(triggers):
                            if "platform" not in trigger:
                                errors.append(
                                    f"Automation {i+1}, Trigger {j+1}: Missing 'platform'"
                                )

                # Validate action structure
                if "action" in automation:
                    actions = automation["action"]
                    if not isinstance(actions, list):
                        errors.append(
                            f"Automation {i+1}: 'action' must be a list"
                        )

        except Exception as e:
            errors.append(f"Validation error: {e}")

        return len(errors) == 0, errors

    def save_automation(
        self,
        yaml_content: str,
        output_file: Optional[Path] = None,
        append: bool = True,
    ) -> bool:
        """Save the generated automation to a file.

        Args:
            yaml_content: YAML content to save
            output_file: Output file path (defaults to config/automations.yaml)
            append: If True, append to existing file; if False, overwrite

        Returns:
            True if save was successful
        """
        if output_file is None:
            output_file = self.config_path / "automations.yaml"

        try:
            if append and output_file.exists():
                # Load existing automations
                with open(output_file, "r") as f:
                    existing = f.read()

                # Parse new automation
                new_automations = yaml.safe_load(yaml_content)
                if not isinstance(new_automations, list):
                    new_automations = [new_automations]

                # Append with proper formatting
                with open(output_file, "a") as f:
                    f.write("\n")
                    yaml.dump(
                        new_automations,
                        f,
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                    )
            else:
                # Write new file
                with open(output_file, "w") as f:
                    f.write(yaml_content)

            print(f"✅ Automation saved to: {output_file}")
            return True

        except Exception as e:
            print(f"Error saving automation: {e}")
            return False


def main():
    """Main entry point for the automation generator."""
    parser = argparse.ArgumentParser(
        description="Generate Home Assistant automations using OpenAI Codex",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate automation interactively
  python codex_automation_generator.py

  # Generate from description
  python codex_automation_generator.py -d "Turn on living room lights at sunset"

  # Generate and save to file
  python codex_automation_generator.py -d "Motion lights in basement" -s

  # Use specific model
  python codex_automation_generator.py -d "Close garage at 10pm" -m gpt-3.5-turbo

  # Save to custom file (overwrite)
  python codex_automation_generator.py -d "Morning routine" -s -o new_automations.yaml --no-append
        """,
    )

    parser.add_argument(
        "-d",
        "--description",
        help="Natural language description of the automation to generate",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-4"),
        help="OpenAI model to use (default: gpt-4)",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config"),
        help="Path to Home Assistant config directory (default: config/)",
    )
    parser.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save the generated automation to automations.yaml",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (default: config/automations.yaml)",
    )
    parser.add_argument(
        "--no-append",
        action="store_true",
        help="Overwrite output file instead of appending",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature 0.0-2.0 (default: 0.7)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate, don't generate new automation",
    )

    args = parser.parse_args()

    # Interactive mode if no description provided
    if not args.description and not args.validate_only:
        print("=" * 80)
        print("OpenAI Codex Home Assistant Automation Generator")
        print("=" * 80)
        print("\nDescribe the automation you want to create in plain English.")
        print("Example: 'Turn on living room lights when motion is detected after sunset'\n")

        try:
            description = input("Automation description: ").strip()
            if not description:
                print("No description provided. Exiting.")
                return
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return
    else:
        description = args.description

    # Initialize generator
    try:
        generator = CodexAutomationGenerator(
            model=args.model,
            config_path=args.config,
        )
    except ValueError as e:
        print(f"Error: {e}")
        print("\nTo use this tool, you need to:")
        print("1. Get an API key from https://platform.openai.com/api-keys")
        print("2. Set it in your environment: export OPENAI_API_KEY='your-key-here'")
        print("3. Or add it to your .env file: OPENAI_API_KEY=your-key-here")
        return

    print(f"\n🤖 Generating automation using {args.model}...")
    print(f"   Description: {description}\n")

    # Generate automation
    yaml_content = generator.generate_automation(
        description,
        temperature=args.temperature,
    )

    if not yaml_content:
        print("❌ Failed to generate automation.")
        return

    print("=" * 80)
    print("Generated Automation:")
    print("=" * 80)
    print(yaml_content)
    print("=" * 80)

    # Validate
    print("\n🔍 Validating automation...")
    is_valid, errors = generator.validate_automation(yaml_content)

    if is_valid:
        print("✅ Automation is valid!")
    else:
        print("❌ Validation errors found:")
        for error in errors:
            print(f"   • {error}")
        print("\nYou may need to edit the automation manually.")

    # Save if requested
    if args.save:
        if not is_valid:
            response = input("\n⚠️  Automation has errors. Save anyway? [y/N]: ")
            if response.lower() != "y":
                print("Not saved.")
                return

        output_file = args.output if args.output else None
        success = generator.save_automation(
            yaml_content,
            output_file=output_file,
            append=not args.no_append,
        )

        if success and is_valid:
            print("\n💡 Next steps:")
            print("   1. Review the automation in your editor")
            print("   2. Run: make validate")
            print("   3. Run: make push")


if __name__ == "__main__":
    main()
