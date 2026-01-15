# Home Assistant Configuration Management

This repository manages Home Assistant configuration files with automated validation, testing, and deployment.

## Project Structure

- `config/` - Contains all Home Assistant configuration files (synced from HA instance)
- `tools/` - Validation and testing scripts
- `venv/` - Python virtual environment with dependencies
- `temp/` - Temporary directory for Claude to write and test code before moving to final locations
- `Makefile` - Commands for pulling/pushing configuration
- `.claude-code/` - Project-specific Claude Code settings and hooks
  - `hooks/` - Validation hooks that run automatically
  - `settings.json` - Project configuration

## Available Commands

### Configuration Management
- `make pull` - Pull latest config from Home Assistant instance
- `make push` - Push local config to Home Assistant (with validation)
- `make backup` - Create backup of current config
- `make validate` - Run all validation tests

### Validation Tools
- `python tools/run_tests.py` - Run complete validation suite
- `python tools/yaml_validator.py` - YAML syntax validation only
- `python tools/reference_validator.py` - Entity/device reference validation
- `python tools/ha_official_validator.py` - Official HA configuration validation

### Entity Discovery Tools
- `make entities` - Explore available Home Assistant entities
- `python tools/entity_explorer.py` - Entity registry parser and explorer
  - `--search TERM` - Search entities by name, ID, or device class
  - `--domain DOMAIN` - Show entities from specific domain (e.g., climate, sensor)
  - `--area AREA` - Show entities from specific area
  - `--full` - Show complete detailed output

### AI-Powered Automation Generation
- `make codex` - Generate automations using OpenAI (interactive mode)
- `make generate-automation DESC='...'` - Generate automation from description
  - `DESC='description'` - Natural language description (required)
  - `SAVE=yes` - Automatically save to automations.yaml
  - `MODEL=gpt-3.5-turbo` - Specify OpenAI model (default: gpt-4)
- `python tools/codex_automation_generator.py` - Direct tool access with full options
  - `--description "..."` - Automation description
  - `--save` - Save generated automation
  - `--output file.yaml` - Custom output file
  - `--model MODEL` - OpenAI model to use
  - `--temperature 0.7` - Sampling temperature (0.0-2.0)

**Setup Requirements:**
1. Get OpenAI API key from https://platform.openai.com/api-keys
2. Add to `.env` file: `OPENAI_API_KEY=your-key-here`
3. Optionally set model: `OPENAI_MODEL=gpt-4` (default)

**Usage Examples:**
```bash
# Interactive mode (prompts for description)
make codex

# Quick generation
make generate-automation DESC='Turn on living room lights at sunset'

# Generate and save
make generate-automation DESC='Motion activated basement lights' SAVE=yes

# Use GPT-3.5 for faster/cheaper generation
make generate-automation DESC='Close garage at 10pm' MODEL=gpt-3.5-turbo SAVE=yes

# Advanced usage with Python tool
source venv/bin/activate && python tools/codex_automation_generator.py \
  --description "Turn on kitchen lights when motion detected between sunset and 11pm" \
  --save \
  --temperature 0.5
```

**Features:**
- Context-aware generation using your entity registry
- Follows Home Assistant naming conventions
- Automatic validation of generated YAML
- Integration with existing validation pipeline
- Supports all OpenAI models (GPT-4, GPT-3.5-turbo, etc.)

## Validation System

This project includes comprehensive validation to prevent invalid configurations:

1. **YAML Syntax Validation** - Ensures proper YAML syntax with HA-specific tags
2. **Entity Reference Validation** - Checks that all referenced entities/devices exist
3. **Official HA Validation** - Uses Home Assistant's own validation tools

### Automated Validation Hooks

- **Post-Edit Hook**: Runs validation after editing any YAML files in `config/`
- **Pre-Push Hook**: Validates configuration before pushing to Home Assistant
- **Blocks invalid pushes**: Prevents uploading broken configurations

## Home Assistant Instance Details

- **Host**: Configure in Makefile `HA_HOST` variable
- **User**: Configure SSH access as needed
- **SSH Key**: Configure SSH key authentication
- **Config Path**: /config/ (standard HA path)
- **Version**: Compatible with Home Assistant Core 2024.x+

## Entity Registry

The system tracks entities across these domains:
- alarm_control_panel, binary_sensor, button, camera, climate
- device_tracker, event, image, light, lock, media_player
- number, person, scene, select, sensor, siren, switch
- time, tts, update, vacuum, water_heater, weather, zone

## Development Workflow

1. **Pull Latest**: `make pull` to sync from HA
2. **Edit Locally**: Modify files in `config/` directory
3. **Auto-Validation**: Hooks automatically validate on edits
4. **Test Changes**: `make validate` for full test suite
5. **Deploy**: `make push` to upload (blocked if validation fails)

## Key Features

- ✅ **Safe Deployments**: Pre-push validation prevents broken configs
- ✅ **Entity Validation**: Ensures all references point to real entities
- ✅ **Entity Discovery**: Advanced tools to explore and search available entities
- ✅ **AI-Powered Automation**: Generate automations using OpenAI (Claude Code or Codex)
- ✅ **Official HA Tools**: Uses Home Assistant's own validation
- ✅ **YAML Support**: Handles HA-specific tags (!include, !secret, !input)
- ✅ **Comprehensive Testing**: Multiple validation layers
- ✅ **Automated Hooks**: Validation runs automatically on file changes

## Important Notes

- **Never push without validation**: The hooks prevent this, but be aware
- **Blueprint files** use `!input` tags which are normal and expected
- **Secrets are skipped** during validation for security
- **SSH access required** for pull/push operations
- **Python venv required** for validation tools

## Troubleshooting

### Validation Fails
1. Check YAML syntax errors first
2. Verify entity references exist in `.storage/` files
3. Run individual validators to isolate issues
4. Check HA logs if official validation fails

### SSH Issues
1. Verify SSH key permissions: `chmod 600 ~/.ssh/your_key`
2. Test connection: `ssh your_homeassistant_host`
3. Check SSH config in `~/.ssh/config`

### Missing Dependencies
1. Activate venv: `source venv/bin/activate`
2. Install requirements: `pip install homeassistant voluptuous pyyaml`

## Security

- **SSH keys** are used for secure access
- **Secrets.yaml** is excluded from validation (contains sensitive data)
- **No credentials** are stored in this repository
- **Access tokens** in config are for authorized integrations

This system ensures you can confidently manage Home Assistant configurations with Claude while maintaining safety and reliability.

## Entity Naming Convention

This Home Assistant setup uses a **standardized entity naming convention** for multi-location deployments:

### **Format: `location_room_device_sensor`**

**Structure:**
- **location**: `home`, `office`, `cabin`, etc.
- **room**: `basement`, `kitchen`, `living_room`, `main_bedroom`, `guest_bedroom`, `driveway`, etc.
- **device**: `motion`, `heatpump`, `sonos`, `lock`, `vacuum`, `water_heater`, `alarm`, etc.
- **sensor**: `battery`, `tamper`, `status`, `temperature`, `humidity`, `door`, `running`, etc.

### **Examples:**
```
binary_sensor.home_basement_motion_battery
binary_sensor.home_basement_motion_tamper
media_player.home_kitchen_sonos
media_player.office_main_bedroom_sonos
climate.home_living_room_heatpump
climate.office_living_room_thermostat
lock.home_front_door_august
sensor.office_driveway_camera_battery
vacuum.home_roborock
vacuum.office_roborock
```

### **Benefits:**
- **Clear location identification** - no ambiguity between properties
- **Consistent structure** - easy to predict entity names
- **Automation-friendly** - simple to target location-specific devices
- **Scalable** - supports additional locations or rooms

### **Implementation:**
- All location-based entities follow this convention
- Legacy entities have been systematically renamed
- New entities should follow this pattern
- Vendor prefixes (aquanta_, august_, etc.) are replaced with descriptive device names

### **AI-Powered Automation:**

This project supports two AI assistants for managing your Home Assistant configuration:

**1. Claude Code (Interactive Assistant)** - You're using this now!
- Run `claude` in this directory
- Reads CLAUDE.md for project-specific instructions
- Full codebase awareness and integration
- Handles any task: automations, validation, exploration, troubleshooting
- Best for: Interactive development, complex multi-step tasks, code review

**2. OpenAI Codex (Interactive Assistant)** - Alternative AI assistant
- Run `codex` in this directory (requires OpenAI Codex CLI installed)
- Reads AGENTS.md (standard format for AI agents)
- Full project awareness through function calling
- Handles any task like Claude Code
- Best for: Using OpenAI models, teams preferring OpenAI

**Quick Reference:**
```bash
# Interactive AI assistants
claude                                    # Claude Code (you're using this)
codex                                     # OpenAI Codex (if installed)
```

**Both assistants:**
- Ask for clarification when multiple entity choices exist
- Use entity explorer tools to discover available entities
- Follow naming convention: location_room_device_sensor
- Run validation after changes: `make validate`
- Integrate with the same validation pipeline
- Generate valid Home Assistant YAML

- All python tools need to be run with  `source venv/bin/activate && python <tool_path>`
