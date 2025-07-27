"""User profile sensors for Eight Sleep."""

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
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import EightSleepBaseEntity, EightSleepConfigEntryData
from .const import DOMAIN
from .pyEight.eight import EightSleep
from .pyEight.user import EightUser

_LOGGER = logging.getLogger(__name__)

# User profile sensor types
USER_PROFILE_SENSORS = {
    "user_name": {
        "name": "User Name",
        "unit": None,
        "device_class": None,
        "icon": "mdi:account",
        "state_class": None,
    },
    "user_email": {
        "name": "User Email",
        "unit": None,
        "device_class": None,
        "icon": "mdi:email",
        "state_class": None,
    },
    "device_count": {
        "name": "Device Count",
        "unit": "devices",
        "device_class": None,
        "icon": "mdi:devices",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "temp_preference": {
        "name": "Temperature Preference",
        "unit": None,
        "device_class": None,
        "icon": "mdi:thermometer",
        "state_class": None,
    },
    "sleep_tracking": {
        "name": "Sleep Tracking Status",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:sleep",
        "state_class": None,
    },
    "autopilot_enabled": {
        "name": "Autopilot Status",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:robot",
        "state_class": None,
    },
    "experimental_features": {
        "name": "Experimental Features",
        "unit": None,
        "device_class": None,
        "icon": "mdi:flask",
        "state_class": None,
    },
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep user profile sensors."""
    config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    eight = config_entry_data.api

    entities = []

    # Create user profile sensors
    entities.append(
        EightSleepUserProfileSensor(
            entry,
            config_entry_data.user_coordinator,
            eight,
            None,  # No specific user for profile data
        )
    )

    # Create individual profile sensors
    for sensor_type in USER_PROFILE_SENSORS:
        entities.append(
            EightSleepUserProfileDetailSensor(
                entry,
                config_entry_data.user_coordinator,
                eight,
                None,  # No specific user for profile data
                sensor_type,
            )
        )

    async_add_entities(entities)

class EightSleepUserProfileSensor(EightSleepBaseEntity, SensorEntity):
    """Comprehensive user profile sensor."""

    _attr_has_entity_name = True
    _attr_name = "User Profile"
    _attr_icon = "mdi:account-details"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser | None,
    ) -> None:
        """Initialize the user profile sensor."""
        super().__init__(entry, coordinator, eight, user, "user_profile")

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        user_data = self._get_user_data()
        if not user_data:
            return None
        
        # Return a summary of the user profile
        name = f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}".strip()
        if name:
            return f"Active - {name}"
        return "Active"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        user_data = self._get_user_data()
        if not user_data:
            return None
        
        return {
            "user_id": user_data.get("userId"),
            "first_name": user_data.get("firstName"),
            "last_name": user_data.get("lastName"),
            "email": user_data.get("email"),
            "gender": user_data.get("gender"),
            "temp_preference": user_data.get("tempPreference"),
            "temp_preference_updated": user_data.get("tempPreferenceUpdatedAt"),
            "date_of_birth": user_data.get("dob"),
            "zip_code": user_data.get("zip"),
            "email_verified": user_data.get("emailVerified"),
            "sleep_tracking": user_data.get("sleepTracking"),
            "autopilot_enabled": user_data.get("autopilotEnabled"),
            "experimental_features": user_data.get("experimentalFeatures"),
            "created_at": user_data.get("createdAt"),
            "last_reset": user_data.get("lastReset"),
            "next_reset": user_data.get("nextReset"),
            "device_count": len(user_data.get("devices", [])),
            "current_device": user_data.get("currentDevice"),
            "features": user_data.get("features"),
        }

    def _get_user_data(self) -> dict | None:
        """Get user data from the API."""
        try:
            # Get user data from the API
            user_data = self.eight.user_data
            if user_data and "user" in user_data:
                return user_data["user"]
            return None
        except Exception as e:
            _LOGGER.error("Error getting user data: %s", e)
            return None

class EightSleepUserProfileDetailSensor(EightSleepBaseEntity, SensorEntity):
    """Individual user profile detail sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser | None,
        sensor_type: str,
    ) -> None:
        """Initialize the user profile detail sensor."""
        super().__init__(entry, coordinator, eight, user, f"user_profile_{sensor_type}")
        self._sensor_type = sensor_type
        self._sensor_config = USER_PROFILE_SENSORS[sensor_type]
        
        # Set entity attributes
        self._attr_name = self._sensor_config["name"]
        self._attr_icon = self._sensor_config["icon"]
        self._attr_device_class = self._sensor_config["device_class"]
        self._attr_native_unit_of_measurement = self._sensor_config["unit"]
        self._attr_state_class = self._sensor_config["state_class"]

    @property
    def native_value(self) -> str | int | float | None:
        """Return the state of the sensor."""
        user_data = self._get_user_data()
        if not user_data:
            return None
        
        if self._sensor_type == "user_name":
            first_name = user_data.get("firstName", "")
            last_name = user_data.get("lastName", "")
            return f"{first_name} {last_name}".strip()
        
        elif self._sensor_type == "user_email":
            return user_data.get("email")
        
        elif self._sensor_type == "device_count":
            return len(user_data.get("devices", []))
        
        elif self._sensor_type == "temp_preference":
            temp_pref = user_data.get("tempPreference")
            if temp_pref is not None:
                return f"{temp_pref}°C"
            return None
        
        elif self._sensor_type == "sleep_tracking":
            tracking = user_data.get("sleepTracking")
            if tracking is True:
                return "Enabled"
            elif tracking is False:
                return "Disabled"
            return "Unknown"
        
        elif self._sensor_type == "autopilot_enabled":
            autopilot = user_data.get("autopilotEnabled")
            if autopilot is True:
                return "Enabled"
            elif autopilot is False:
                return "Disabled"
            return "Unknown"
        
        elif self._sensor_type == "experimental_features":
            features = user_data.get("experimentalFeatures")
            if features:
                return "Enabled"
            return "Disabled"
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        user_data = self._get_user_data()
        if not user_data:
            return None
        
        # Return relevant attributes based on sensor type
        if self._sensor_type == "user_name":
            return {
                "first_name": user_data.get("firstName"),
                "last_name": user_data.get("lastName"),
                "full_name": f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}".strip(),
            }
        
        elif self._sensor_type == "user_email":
            return {
                "email": user_data.get("email"),
                "email_verified": user_data.get("emailVerified"),
            }
        
        elif self._sensor_type == "device_count":
            devices = user_data.get("devices", [])
            return {
                "device_count": len(devices),
                "devices": devices,
                "current_device": user_data.get("currentDevice"),
            }
        
        elif self._sensor_type == "temp_preference":
            return {
                "temp_preference": user_data.get("tempPreference"),
                "temp_preference_updated": user_data.get("tempPreferenceUpdatedAt"),
                "temp_preference_celsius": user_data.get("tempPreference"),
            }
        
        elif self._sensor_type == "sleep_tracking":
            return {
                "sleep_tracking": user_data.get("sleepTracking"),
                "features": user_data.get("features"),
            }
        
        elif self._sensor_type == "autopilot_enabled":
            return {
                "autopilot_enabled": user_data.get("autopilotEnabled"),
                "last_reset": user_data.get("lastReset"),
                "next_reset": user_data.get("nextReset"),
            }
        
        elif self._sensor_type == "experimental_features":
            return {
                "experimental_features": user_data.get("experimentalFeatures"),
                "features": user_data.get("features"),
            }
        
        return None

    def _get_user_data(self) -> dict | None:
        """Get user data from the API."""
        try:
            # Get user data from the API
            user_data = self.eight.user_data
            if user_data and "user" in user_data:
                return user_data["user"]
            return None
        except Exception as e:
            _LOGGER.error("Error getting user data: %s", e)
            return None 