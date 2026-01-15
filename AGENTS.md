# Home Assistant Configuration Management

## Your Role

You're helping manage Home Assistant configurations with automated validation, testing, and safe deployment. When the user asks you to create automations, validate configs, explore entities, or troubleshoot issues - use the commands and workflows below.

**Working Directory**: `/home/user/llm-homeassistant`

## Getting Started

When asked to work on this project:
1. **Read files first** - Always read `config/automations.yaml` or relevant files before editing
2. **Discover entities** - Use `make entities ARGS='--search keyword'` to find available devices
3. **Follow naming convention** - Entity IDs use `location_room_device_sensor` format
4. **Validate everything** - Run `make validate` after any config changes
5. **Ask when unclear** - If multiple entity options exist, ask the user which one

## Quick Commands

### Configuration Management
```bash
make pull          # Pull config from Home Assistant
make push          # Push config to HA (validates first)
make backup        # Create timestamped backup
make validate      # Run all validations
```

### Entity Discovery
```bash
make entities                          # Show all entities
make entities ARGS='--domain climate'  # Filter by domain
make entities ARGS='--search motion'   # Search entities
make entities ARGS='--area kitchen'    # Filter by area
```

### Testing & Validation
```bash
make validate      # Run all validations (ALWAYS do this after edits)

# Individual validators (if needed):
source venv/bin/activate && python tools/run_tests.py              # Full suite
source venv/bin/activate && python tools/yaml_validator.py         # YAML syntax only
source venv/bin/activate && python tools/reference_validator.py    # Entity refs only
source venv/bin/activate && python tools/ha_official_validator.py  # Official HA only
```

**Important**: Never suggest pushing configs until `make validate` passes cleanly.

## Project Structure

```
├── config/                    # HA config files (edit these)
│   ├── automations.yaml      # Automation definitions
│   ├── scripts.yaml          # Reusable scripts
│   ├── configuration.yaml    # Main config
│   └── .storage/             # Entity registry (read-only)
├── tools/                     # Validation scripts
└── Makefile                   # Management commands
```

## Entity Naming Convention

**Format**: `location_room_device_sensor`

**Examples**:
- `binary_sensor.home_basement_motion_battery`
- `media_player.home_kitchen_sonos`
- `climate.home_living_room_heatpump`
- `lock.home_front_door`

**Structure**:
- location: home, office, cabin
- room: basement, kitchen, living_room, main_bedroom
- device: motion, heatpump, sonos, lock, vacuum
- sensor: battery, tamper, status, temperature

## Automation Format

```yaml
- id: 'unique_id'
  alias: 'Human Readable Name'
  description: 'What this does'
  trigger:
    - platform: state|time|sun|numeric_state|event|webhook|zone|device
      entity_id: sensor.example  # if applicable
  condition:  # optional
    - condition: state|time|numeric_state|sun|template|zone
  action:
    - service: domain.service_name
      target:
        entity_id: light.example
      data:  # optional
        brightness_pct: 75
```

**Valid platforms**: state, time, sun, numeric_state, template, event, webhook, zone, device, tag
**Common services**: light.turn_on, light.turn_off, switch.turn_on, switch.turn_off, climate.set_temperature

## Workflow

### Creating Automations

1. **Discover entities**: `make entities ARGS='--search keyword'`
2. **Draft YAML**: Follow format above
3. **Edit file**: Add to `config/automations.yaml`
4. **Validate**: `make validate`
5. **Fix errors**: Edit and re-validate until clean
6. **Deploy**: User runs `make push`

### Before Editing

- Always read current file first
- Use entity explorer to find correct entity_ids
- Ask user for clarification if multiple options exist

### After Editing

- **ALWAYS run validation**: `make validate`
- Fix any errors found
- Re-validate until clean
- Don't suggest pushing until validation passes

## Critical Rules

- **NEVER push without validation** - system blocks invalid configs anyway
- **ALWAYS validate after edits** - run `make validate`
- **Use entity explorer before creating automations** - don't guess entity_ids
- **Follow naming convention strictly** - location_room_device_sensor
- **Python commands need venv** - prefix with `source venv/bin/activate &&`
- **Blueprint files use !input tags** - this is normal, don't flag as error
- **Secrets are skipped** - secrets.yaml not validated for security

## Available Domains

alarm_control_panel, binary_sensor, button, camera, climate, device_tracker, event, image, light, lock, media_player, number, person, scene, select, sensor, siren, switch, time, tts, update, vacuum, water_heater, weather, zone

## Common Tasks

**Show available lights**:
```bash
make entities ARGS='--domain light'
```

**Find motion sensors**:
```bash
make entities ARGS='--search motion'
```

**Validate configs**:
```bash
make validate
```

**Create backup**:
```bash
make backup
```

## Error Handling

**YAML syntax error**: Check indentation (2 spaces), quotes, colons
**Entity not found**: Use entity explorer to find correct entity_id
**Invalid service**: Check format is domain.service_name
**Invalid platform**: Must be one of the valid platforms listed above

## Response Style

- Be conversational but concise
- Show command output when relevant
- Explain what you're doing before executing
- Ask for clarification when needed
- Summarize results after operations
- Suggest next steps

## Notes

- Three validation layers: YAML syntax, entity references, official HA validation
- Hooks automatically validate after edits
- SSH access required for pull/push
- Python venv required for all Python tools
