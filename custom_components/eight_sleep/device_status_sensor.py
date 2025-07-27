"""Device status sensors for Eight Sleep."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import EightSleepBaseEntity, EightSleepConfigEntryData
from .const import DOMAIN
from .pyEight.eight import EightSleep
from .pyEight.user import EightUser

_LOGGER = logging.getLogger(__name__)

# Device status sensor types
DEVICE_STATUS_SENSORS = {
    "device_id": {
        "name": "Device ID",
        "unit": None,
        "device_class": None,
        "icon": "mdi:identifier",
        "state_class": None,
    },
    "left_heating_level": {
        "name": "Left Side Heating Level",
        "unit": None,
        "device_class": None,
        "icon": "mdi:thermometer",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "right_heating_level": {
        "name": "Right Side Heating Level",
        "unit": None,
        "device_class": None,
        "icon": "mdi:thermometer",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "left_target_heating_level": {
        "name": "Left Side Target Heating Level",
        "unit": None,
        "device_class": None,
        "icon": "mdi:thermometer-target",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "right_target_heating_level": {
        "name": "Right Side Target Heating Level",
        "unit": None,
        "device_class": None,
        "icon": "mdi:thermometer-target",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "left_now_heating": {
        "name": "Left Side Heating Status",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:fire",
        "state_class": None,
    },
    "right_now_heating": {
        "name": "Right Side Heating Status",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:fire",
        "state_class": None,
    },
    "left_heating_duration": {
        "name": "Left Side Heating Duration",
        "unit": "seconds",
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:timer",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "right_heating_duration": {
        "name": "Right Side Heating Duration",
        "unit": "seconds",
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:timer",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "priming": {
        "name": "Priming Status",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:water-sync",
        "state_class": None,
    },
    "needs_priming": {
        "name": "Needs Priming",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:water-alert",
        "state_class": None,
    },
    "has_water": {
        "name": "Water Status",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:water",
        "state_class": None,
    },
    "led_brightness_level": {
        "name": "LED Brightness Level",
        "unit": None,
        "device_class": None,
        "icon": "mdi:lightbulb",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "firmware_version": {
        "name": "Firmware Version",
        "unit": None,
        "device_class": None,
        "icon": "mdi:chip",
        "state_class": None,
    },
    "firmware_updated": {
        "name": "Firmware Updated",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:update",
        "state_class": None,
    },
    "firmware_updating": {
        "name": "Firmware Updating",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:update",
        "state_class": None,
    },
    "last_heard": {
        "name": "Last Heard",
        "unit": None,
        "device_class": None,
        "icon": "mdi:clock",
        "state_class": None,
    },
    "online": {
        "name": "Online Status",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:wifi",
        "state_class": None,
    },
    "left_kelvin": {
        "name": "Left Side Temperature (Kelvin)",
        "unit": "K",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "icon": "mdi:thermometer",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "right_kelvin": {
        "name": "Right Side Temperature (Kelvin)",
        "unit": "K",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "icon": "mdi:thermometer",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "model_string": {
        "name": "Model String",
        "unit": None,
        "device_class": None,
        "icon": "mdi:information",
        "state_class": None,
    },
    "hub_serial": {
        "name": "Hub Serial",
        "unit": None,
        "device_class": None,
        "icon": "mdi:serial-port",
        "state_class": None,
    },
    "is_temperature_available": {
        "name": "Temperature Available",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:thermometer-check",
        "state_class": None,
    },
    "deactivated": {
        "name": "Device Deactivated",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:power-off",
        "state_class": None,
    },
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep device status sensors."""
    config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    eight = config_entry_data.api

    entities = []

    # Get device IDs from user data
    try:
        user_data = eight.user_data
        if user_data and "user" in user_data:
            devices = user_data["user"].get("devices", [])
            
            # Create device status sensors for each device
            for device_id in devices:
                # Create comprehensive device status sensor
                entities.append(
                    EightSleepDeviceStatusSensor(
                        entry,
                        config_entry_data.device_coordinator,
                        eight,
                        None,  # No specific user for device data
                        device_id,
                    )
                )

                # Create individual device status sensors
                for sensor_type in DEVICE_STATUS_SENSORS:
                    entities.append(
                        EightSleepDeviceStatusDetailSensor(
                            entry,
                            config_entry_data.device_coordinator,
                            eight,
                            None,  # No specific user for device data
                            device_id,
                            sensor_type,
                        )
                    )
        else:
            _LOGGER.warning("No user data available for device status sensors")
    except Exception as e:
        _LOGGER.error("Error setting up device status sensors: %s", e)

    async_add_entities(entities)

class EightSleepDeviceStatusSensor(EightSleepBaseEntity, SensorEntity):
    """Comprehensive device status sensor."""

    _attr_has_entity_name = True
    _attr_name = "Device Status"
    _attr_icon = "mdi:devices"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser | None,
        device_id: str,
    ) -> None:
        """Initialize the device status sensor."""
        super().__init__(entry, coordinator, eight, user, f"device_status_{device_id}")
        self._device_id = device_id

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        device_data = self._get_device_data()
        if not device_data:
            return None
        
        # Return a summary of the device status
        online = device_data.get("online", False)
        if online:
            return "Online"
        return "Offline"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        device_data = self._get_device_data()
        if not device_data:
            return None
        
        return {
            "device_id": device_data.get("deviceId"),
            "owner_id": device_data.get("ownerId"),
            "left_heating_level": device_data.get("leftHeatingLevel"),
            "right_heating_level": device_data.get("rightHeatingLevel"),
            "left_target_heating_level": device_data.get("leftTargetHeatingLevel"),
            "right_target_heating_level": device_data.get("rightTargetHeatingLevel"),
            "left_now_heating": device_data.get("leftNowHeating"),
            "right_now_heating": device_data.get("rightNowHeating"),
            "left_heating_duration": device_data.get("leftHeatingDuration"),
            "right_heating_duration": device_data.get("rightHeatingDuration"),
            "priming": device_data.get("priming"),
            "needs_priming": device_data.get("needsPriming"),
            "has_water": device_data.get("hasWater"),
            "led_brightness_level": device_data.get("ledBrightnessLevel"),
            "firmware_version": device_data.get("firmwareVersion"),
            "firmware_updated": device_data.get("firmwareUpdated"),
            "firmware_updating": device_data.get("firmwareUpdating"),
            "last_heard": device_data.get("lastHeard"),
            "online": device_data.get("online"),
            "left_kelvin": device_data.get("leftKelvin"),
            "right_kelvin": device_data.get("rightKelvin"),
            "model_string": device_data.get("modelString"),
            "hub_serial": device_data.get("hubSerial"),
            "is_temperature_available": device_data.get("isTemperatureAvailable"),
            "deactivated": device_data.get("deactivated"),
            "timezone": device_data.get("timezone"),
            "features": device_data.get("features"),
        }

    def _get_device_data(self) -> dict | None:
        """Get device data from the API."""
        try:
            # Get device data from the API
            device_data = self.eight.device_data
            if device_data and "result" in device_data:
                return device_data["result"]
            return None
        except Exception as e:
            _LOGGER.error("Error getting device data: %s", e)
            return None

class EightSleepDeviceStatusDetailSensor(EightSleepBaseEntity, SensorEntity):
    """Individual device status detail sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser | None,
        device_id: str,
        sensor_type: str,
    ) -> None:
        """Initialize the device status detail sensor."""
        super().__init__(entry, coordinator, eight, user, f"device_status_{device_id}_{sensor_type}")
        self._device_id = device_id
        self._sensor_type = sensor_type
        self._sensor_config = DEVICE_STATUS_SENSORS[sensor_type]
        
        # Set entity attributes
        self._attr_name = f"{self._sensor_config['name']} ({device_id[:8]}...)"
        self._attr_icon = self._sensor_config["icon"]
        self._attr_device_class = self._sensor_config["device_class"]
        self._attr_native_unit_of_measurement = self._sensor_config["unit"]
        self._attr_state_class = self._sensor_config["state_class"]

    @property
    def native_value(self) -> str | int | float | None:
        """Return the state of the sensor."""
        device_data = self._get_device_data()
        if not device_data:
            return None
        
        # Map sensor types to device data fields
        field_mapping = {
            "device_id": "deviceId",
            "left_heating_level": "leftHeatingLevel",
            "right_heating_level": "rightHeatingLevel",
            "left_target_heating_level": "leftTargetHeatingLevel",
            "right_target_heating_level": "rightTargetHeatingLevel",
            "left_now_heating": "leftNowHeating",
            "right_now_heating": "rightNowHeating",
            "left_heating_duration": "leftHeatingDuration",
            "right_heating_duration": "rightHeatingDuration",
            "priming": "priming",
            "needs_priming": "needsPriming",
            "has_water": "hasWater",
            "led_brightness_level": "ledBrightnessLevel",
            "firmware_version": "firmwareVersion",
            "firmware_updated": "firmwareUpdated",
            "firmware_updating": "firmwareUpdating",
            "last_heard": "lastHeard",
            "online": "online",
            "left_kelvin": "leftKelvin",
            "right_kelvin": "rightKelvin",
            "model_string": "modelString",
            "hub_serial": "hubSerial",
            "is_temperature_available": "isTemperatureAvailable",
            "deactivated": "deactivated",
        }
        
        field_name = field_mapping.get(self._sensor_type)
        if not field_name:
            return None
        
        value = device_data.get(field_name)
        
        # Format values based on sensor type
        if self._sensor_type in ["left_now_heating", "right_now_heating", "priming", "needs_priming", "has_water", "firmware_updated", "firmware_updating", "online", "is_temperature_available", "deactivated"]:
            if value is True:
                return "Yes"
            elif value is False:
                return "No"
            return "Unknown"
        
        elif self._sensor_type in ["left_heating_level", "right_heating_level", "left_target_heating_level", "right_target_heating_level"]:
            if value is not None:
                return f"{value}°C"
            return None
        
        elif self._sensor_type in ["left_kelvin", "right_kelvin"]:
            if value is not None:
                return f"{value}K"
            return None
        
        elif self._sensor_type == "last_heard":
            if value:
                try:
                    # Try to parse the timestamp
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    return value
            return None
        
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        device_data = self._get_device_data()
        if not device_data:
            return None
        
        # Return relevant attributes based on sensor type
        if self._sensor_type in ["left_heating_level", "left_target_heating_level", "left_now_heating", "left_heating_duration"]:
            return {
                "left_heating_level": device_data.get("leftHeatingLevel"),
                "left_target_heating_level": device_data.get("leftTargetHeatingLevel"),
                "left_now_heating": device_data.get("leftNowHeating"),
                "left_heating_duration": device_data.get("leftHeatingDuration"),
                "left_schedule": device_data.get("leftSchedule"),
                "left_kelvin": device_data.get("leftKelvin"),
            }
        
        elif self._sensor_type in ["right_heating_level", "right_target_heating_level", "right_now_heating", "right_heating_duration"]:
            return {
                "right_heating_level": device_data.get("rightHeatingLevel"),
                "right_target_heating_level": device_data.get("rightTargetHeatingLevel"),
                "right_now_heating": device_data.get("rightNowHeating"),
                "right_heating_duration": device_data.get("rightHeatingDuration"),
                "right_schedule": device_data.get("rightSchedule"),
                "right_kelvin": device_data.get("rightKelvin"),
            }
        
        elif self._sensor_type in ["priming", "needs_priming", "has_water"]:
            return {
                "priming": device_data.get("priming"),
                "needs_priming": device_data.get("needsPriming"),
                "has_water": device_data.get("hasWater"),
                "last_low_water": device_data.get("lastLowWater"),
                "last_prime": device_data.get("lastPrime"),
            }
        
        elif self._sensor_type in ["firmware_version", "firmware_updated", "firmware_updating"]:
            return {
                "firmware_version": device_data.get("firmwareVersion"),
                "firmware_commit": device_data.get("firmwareCommit"),
                "firmware_updated": device_data.get("firmwareUpdated"),
                "firmware_updating": device_data.get("firmwareUpdating"),
                "last_firmware_update_start": device_data.get("lastFirmwareUpdateStart"),
            }
        
        elif self._sensor_type in ["online", "last_heard"]:
            return {
                "online": device_data.get("online"),
                "last_heard": device_data.get("lastHeard"),
                "timezone": device_data.get("timezone"),
            }
        
        return {
            "device_id": device_data.get("deviceId"),
            "owner_id": device_data.get("ownerId"),
            "model_string": device_data.get("modelString"),
            "hub_serial": device_data.get("hubSerial"),
        }

    def _get_device_data(self) -> dict | None:
        """Get device data from the API."""
        try:
            # Get device data from the API
            device_data = self.eight.device_data
            if device_data and "result" in device_data:
                return device_data["result"]
            return None
        except Exception as e:
            _LOGGER.error("Error getting device data: %s", e)
            return None 