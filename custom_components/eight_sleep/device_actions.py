"""Device actions for Eight Sleep integration."""

from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_TYPE,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from .const import DOMAIN

# Device action types
ACTION_SET_TEMPERATURE = "set_temperature"
ACTION_INCREMENT_TEMPERATURE = "increment_temperature"
ACTION_TURN_ON_SIDE = "turn_on_side"
ACTION_TURN_OFF_SIDE = "turn_off_side"
ACTION_SET_PRESET = "set_preset"
ACTION_START_AWAY_MODE = "start_away_mode"
ACTION_STOP_AWAY_MODE = "stop_away_mode"
ACTION_PRIME_POD = "prime_pod"
ACTION_SET_BED_SIDE = "set_bed_side"

# Action schemas
SET_TEMPERATURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required("temperature"): vol.Coerce(float),
        vol.Optional("duration", default=7200): vol.Coerce(int),
        vol.Optional("sleep_stage", default="current"): vol.In([
            "current", "bedTimeLevel", "initialSleepLevel", "finalSleepLevel"
        ]),
    }
)

INCREMENT_TEMPERATURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required("increment"): vol.Coerce(float),
    }
)

TURN_SIDE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): str,
        vol.Optional("side", default="both"): vol.In(["left", "right", "both"]),
    }
)

SET_PRESET_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required("preset"): vol.In(["cool", "warm", "neutral"]),
        vol.Optional("side", default="both"): vol.In(["left", "right", "both"]),
    }
)

AWAY_MODE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): str,
    }
)

SET_BED_SIDE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required("bed_side_state"): vol.In(["solo", "left", "right"]),
    }
)

PRIME_POD_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): str,
    }
)

async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """Get device actions for Eight Sleep devices."""
    actions = []

    # Get the device registry entry
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)

    if not device or device.domain != DOMAIN:
        return actions

    # Get all entities for this device
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_device(entity_registry, device_id)

    # Check if device has climate entities
    has_climate = any(entity.domain == "climate" for entity in entities)
    has_sensor = any(entity.domain == "sensor" for entity in entities)

    if has_climate:
        # Temperature control actions
        actions.extend([
            {
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: ACTION_SET_TEMPERATURE,
                CONF_DEVICE_ID: device_id,
                "name": "Set Temperature",
                "description": "Set the bed temperature",
            },
            {
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: ACTION_INCREMENT_TEMPERATURE,
                CONF_DEVICE_ID: device_id,
                "name": "Increment Temperature",
                "description": "Adjust temperature by increment",
            },
            {
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: ACTION_TURN_ON_SIDE,
                CONF_DEVICE_ID: device_id,
                "name": "Turn On Side",
                "description": "Turn on heating/cooling for a side",
            },
            {
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: ACTION_TURN_OFF_SIDE,
                CONF_DEVICE_ID: device_id,
                "name": "Turn Off Side",
                "description": "Turn off heating/cooling for a side",
            },
            {
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: ACTION_SET_PRESET,
                CONF_DEVICE_ID: device_id,
                "name": "Set Temperature Preset",
                "description": "Set temperature preset (Cool/Warm/Neutral)",
            },
        ])

    if has_sensor:
        # Device control actions
        actions.extend([
            {
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: ACTION_START_AWAY_MODE,
                CONF_DEVICE_ID: device_id,
                "name": "Start Away Mode",
                "description": "Start away mode",
            },
            {
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: ACTION_STOP_AWAY_MODE,
                CONF_DEVICE_ID: device_id,
                "name": "Stop Away Mode",
                "description": "Stop away mode",
            },
            {
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: ACTION_PRIME_POD,
                CONF_DEVICE_ID: device_id,
                "name": "Prime Pod",
                "description": "Prime the pod",
            },
            {
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: ACTION_SET_BED_SIDE,
                CONF_DEVICE_ID: device_id,
                "name": "Set Bed Side",
                "description": "Configure bed side settings",
            },
        ])

    return actions

async def async_call_action_from_config(
    hass: HomeAssistant,
    config: ConfigType,
    variables: TemplateVarsType,
    context: Context | None,
) -> None:
    """Execute a device action."""
    action_type = config[CONF_TYPE]
    device_id = config[CONF_DEVICE_ID]

    # Get the device registry entry
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)

    if not device or device.domain != DOMAIN:
        return

    # Get all entities for this device
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_device(entity_registry, device_id)

    # Get climate entities
    climate_entities = [
        entity.entity_id for entity in entities if entity.domain == "climate"
    ]

    # Get sensor entities (for device actions)
    sensor_entities = [
        entity.entity_id for entity in entities if entity.domain == "sensor"
    ]

    if action_type == ACTION_SET_TEMPERATURE:
        temperature = config["temperature"]

        for entity_id in climate_entities:
            await hass.services.async_call(
                "climate",
                "set_temperature",
                {
                    ATTR_ENTITY_ID: entity_id,
                    "temperature": temperature,
                },
                blocking=True,
                context=context,
            )

    elif action_type == ACTION_INCREMENT_TEMPERATURE:
        increment = config["increment"]

        for entity_id in climate_entities:
            # Get current temperature and add increment
            state = hass.states.get(entity_id)
            if state and state.attributes.get("target_temperature"):
                current_temp = state.attributes["target_temperature"]
                new_temp = current_temp + increment

                await hass.services.async_call(
                    "climate",
                    "set_temperature",
                    {
                        ATTR_ENTITY_ID: entity_id,
                        "temperature": new_temp,
                    },
                    blocking=True,
                    context=context,
                )

    elif action_type == ACTION_TURN_ON_SIDE:
        side = config.get("side", "both")

        for entity_id in climate_entities:
            if side == "both" or side in entity_id.lower():
                await hass.services.async_call(
                    "climate",
                    "turn_on",
                    {ATTR_ENTITY_ID: entity_id},
                    blocking=True,
                    context=context,
                )

    elif action_type == ACTION_TURN_OFF_SIDE:
        side = config.get("side", "both")

        for entity_id in climate_entities:
            if side == "both" or side in entity_id.lower():
                await hass.services.async_call(
                    "climate",
                    "turn_off",
                    {ATTR_ENTITY_ID: entity_id},
                    blocking=True,
                    context=context,
                )

    elif action_type == ACTION_SET_PRESET:
        preset = config["preset"]
        side = config.get("side", "both")

        for entity_id in climate_entities:
            if side == "both" or side in entity_id.lower():
                await hass.services.async_call(
                    "climate",
                    "set_preset_mode",
                    {
                        ATTR_ENTITY_ID: entity_id,
                        "preset_mode": preset,
                    },
                    blocking=True,
                    context=context,
                )

    elif action_type == ACTION_START_AWAY_MODE:
        for entity_id in sensor_entities:
            await hass.services.async_call(
                DOMAIN,
                "away_mode_start",
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
                context=context,
            )

    elif action_type == ACTION_STOP_AWAY_MODE:
        for entity_id in sensor_entities:
            await hass.services.async_call(
                DOMAIN,
                "away_mode_stop",
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
                context=context,
            )

    elif action_type == ACTION_PRIME_POD:
        for entity_id in sensor_entities:
            await hass.services.async_call(
                DOMAIN,
                "prime_pod",
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
                context=context,
            )

    elif action_type == ACTION_SET_BED_SIDE:
        bed_side_state = config["bed_side_state"]

        for entity_id in sensor_entities:
            await hass.services.async_call(
                DOMAIN,
                "set_bed_side",
                {
                    ATTR_ENTITY_ID: entity_id,
                    "bed_side_state": bed_side_state,
                },
                blocking=True,
                context=context,
            )

async def async_validate_action_config(
    hass: HomeAssistant, config: ConfigType
) -> ConfigType:
    """Validate config."""
    action_type = config[CONF_TYPE]

    if action_type == ACTION_SET_TEMPERATURE:
        config = SET_TEMPERATURE_SCHEMA(config)
    elif action_type == ACTION_INCREMENT_TEMPERATURE:
        config = INCREMENT_TEMPERATURE_SCHEMA(config)
    elif action_type == ACTION_TURN_ON_SIDE:
        config = TURN_SIDE_SCHEMA(config)
    elif action_type == ACTION_TURN_OFF_SIDE:
        config = TURN_SIDE_SCHEMA(config)
    elif action_type == ACTION_SET_PRESET:
        config = SET_PRESET_SCHEMA(config)
    elif action_type == ACTION_START_AWAY_MODE:
        config = AWAY_MODE_SCHEMA(config)
    elif action_type == ACTION_STOP_AWAY_MODE:
        config = AWAY_MODE_SCHEMA(config)
    elif action_type == ACTION_PRIME_POD:
        config = PRIME_POD_SCHEMA(config)
    elif action_type == ACTION_SET_BED_SIDE:
        config = SET_BED_SIDE_SCHEMA(config)

    return config
