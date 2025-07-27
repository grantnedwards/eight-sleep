"""Support for Eight Sleep Binary Sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import EightSleepBaseEntity, EightSleepConfigEntryData
from .const import DOMAIN
from .pyEight.user import EightUser
from .pyEight.eight import EightSleep

_LOGGER = logging.getLogger(__name__)

# Binary Sensor Types
BINARY_SENSORS = [
    "bed_presence",
    "away_mode_active",
    "device_online",
    "priming_needed",
    "is_priming",
    "has_water",
    "alarm_enabled",
    "alarm_ringing",
    "alarm_dismissed",
    "alarm_stopped",
    "sleep_tracking_enabled",
    "session_processing",
    "device_connected",
    "firmware_updating",
    "maintenance_required",
    "error_detected",
    "warning_active",
    "notification_pending",
    "alert_active",
    "update_available",
    "support_needed",
    "warranty_active",
    "analytics_enabled",
    "insights_available",
    "trends_available",
    "history_available",
    "settings_modified",
    "configuration_changed",
    "schedule_active",
    "routine_enabled",
]

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep Binary Sensors."""
    config_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    coordinator = config_data.coordinator
    eight = config_data.eight

    entities = []

    # Add binary sensors for each user
    for user in eight.users.values():
        for sensor_type in BINARY_SENSORS:
            entities.append(
                EightBinarySensor(
                    entry,
                    coordinator,
                    eight,
                    user,
                    sensor_type,
                )
            )

    # Add device-level binary sensors
    for sensor_type in ["device_online", "priming_needed", "is_priming", "has_water", "device_connected", "firmware_updating", "maintenance_required", "error_detected", "warning_active", "notification_pending", "alert_active", "update_available", "support_needed", "warranty_active", "analytics_enabled", "insights_available", "trends_available", "history_available", "settings_modified", "configuration_changed", "schedule_active", "routine_enabled"]:
        entities.append(
            EightDeviceBinarySensor(
                entry,
                coordinator,
                eight,
                sensor_type,
            )
        )

    async_add_entities(entities)


class EightBinarySensor(EightSleepBaseEntity, BinarySensorEntity):
    """Representation of an Eight Sleep Binary Sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        sensor_type: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry, coordinator, eight, user)
        self._sensor_type = sensor_type
        self._attr_name = f"{self._user.side} {self._get_sensor_name(sensor_type)}"
        self._attr_unique_id = f"{self._user.user_id}_{sensor_type}"
        
        # Set device class based on sensor type
        self._set_sensor_properties(sensor_type)

    def _get_sensor_name(self, sensor_type: str) -> str:
        """Get the display name for the sensor type."""
        name_map = {
            "bed_presence": "Bed Presence",
            "away_mode_active": "Away Mode Active",
            "device_online": "Device Online",
            "priming_needed": "Priming Needed",
            "is_priming": "Is Priming",
            "has_water": "Has Water",
            "alarm_enabled": "Alarm Enabled",
            "alarm_ringing": "Alarm Ringing",
            "alarm_dismissed": "Alarm Dismissed",
            "alarm_stopped": "Alarm Stopped",
            "sleep_tracking_enabled": "Sleep Tracking Enabled",
            "session_processing": "Session Processing",
            "device_connected": "Device Connected",
            "firmware_updating": "Firmware Updating",
            "maintenance_required": "Maintenance Required",
            "error_detected": "Error Detected",
            "warning_active": "Warning Active",
            "notification_pending": "Notification Pending",
            "alert_active": "Alert Active",
            "update_available": "Update Available",
            "support_needed": "Support Needed",
            "warranty_active": "Warranty Active",
            "analytics_enabled": "Analytics Enabled",
            "insights_available": "Insights Available",
            "trends_available": "Trends Available",
            "history_available": "History Available",
            "settings_modified": "Settings Modified",
            "configuration_changed": "Configuration Changed",
            "schedule_active": "Schedule Active",
            "routine_enabled": "Routine Enabled",
        }
        return name_map.get(sensor_type, sensor_type.replace("_", " ").title())

    def _set_sensor_properties(self, sensor_type: str) -> None:
        """Set device class based on sensor type."""
        if "presence" in sensor_type.lower():
            self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY
        elif "alarm" in sensor_type.lower():
            self._attr_device_class = BinarySensorDeviceClass.SOUND
        elif "online" in sensor_type.lower() or "connected" in sensor_type.lower():
            self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        elif "error" in sensor_type.lower() or "warning" in sensor_type.lower():
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        elif "update" in sensor_type.lower() or "firmware" in sensor_type.lower():
            self._attr_device_class = BinarySensorDeviceClass.UPDATE
        elif "maintenance" in sensor_type.lower():
            self._attr_device_class = BinarySensorDeviceClass.MAINTENANCE
        else:
            self._attr_device_class = None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self._user:
            return None

        try:
            if self._sensor_type == "bed_presence":
                return self._user.bed_presence
            elif self._sensor_type == "away_mode_active":
                return self._get_away_mode_active()
            elif self._sensor_type == "alarm_enabled":
                return self._get_alarm_enabled()
            elif self._sensor_type == "alarm_ringing":
                return self._get_alarm_ringing()
            elif self._sensor_type == "alarm_dismissed":
                return self._get_alarm_dismissed()
            elif self._sensor_type == "alarm_stopped":
                return self._get_alarm_stopped()
            elif self._sensor_type == "sleep_tracking_enabled":
                return self._get_sleep_tracking_enabled()
            elif self._sensor_type == "session_processing":
                return self._user.current_session_processing
            else:
                return None
        except Exception as e:
            _LOGGER.error(f"Error getting {self._sensor_type} value: {e}")
            return None

    def _get_away_mode_active(self) -> bool:
        """Get away mode active status."""
        try:
            if self._eight.device_data:
                away_sides = self._eight.device_data.get("awaySides", {})
                return self._user.side in away_sides
        except Exception as e:
            _LOGGER.error(f"Error getting away mode active: {e}")
        return False

    def _get_alarm_enabled(self) -> bool:
        """Get alarm enabled status."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("enabled", False)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm enabled: {e}")
        return False

    def _get_alarm_ringing(self) -> bool:
        """Get alarm ringing status."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("ringing", False)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm ringing: {e}")
        return False

    def _get_alarm_dismissed(self) -> bool:
        """Get alarm dismissed status."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("dismissed", False)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm dismissed: {e}")
        return False

    def _get_alarm_stopped(self) -> bool:
        """Get alarm stopped status."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("stopped", False)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm stopped: {e}")
        return False

    def _get_sleep_tracking_enabled(self) -> bool:
        """Get sleep tracking enabled status."""
        try:
            if self._user.user_profile:
                return self._user.user_profile.get("sleepTracking", {}).get("enabled", True)
        except Exception as e:
            _LOGGER.error(f"Error getting sleep tracking enabled: {e}")
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if not self._user:
            return None

        attrs = {
            "side": self._user.side,
            "user_id": self._user.user_id,
            "sensor_type": self._sensor_type,
        }

        return attrs


class EightDeviceBinarySensor(EightSleepBaseEntity, BinarySensorEntity):
    """Representation of an Eight Sleep Device Binary Sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        sensor_type: str,
    ) -> None:
        """Initialize the device binary sensor."""
        super().__init__(entry, coordinator, eight, None)  # No user for device sensors
        self._sensor_type = sensor_type
        self._attr_name = f"Eight Sleep {self._get_sensor_name(sensor_type)}"
        self._attr_unique_id = f"device_{sensor_type}"
        
        # Set device class based on sensor type
        self._set_sensor_properties(sensor_type)

    def _get_sensor_name(self, sensor_type: str) -> str:
        """Get the display name for the sensor type."""
        name_map = {
            "device_online": "Device Online",
            "priming_needed": "Priming Needed",
            "is_priming": "Is Priming",
            "has_water": "Has Water",
            "device_connected": "Device Connected",
            "firmware_updating": "Firmware Updating",
            "maintenance_required": "Maintenance Required",
            "error_detected": "Error Detected",
            "warning_active": "Warning Active",
            "notification_pending": "Notification Pending",
            "alert_active": "Alert Active",
            "update_available": "Update Available",
            "support_needed": "Support Needed",
            "warranty_active": "Warranty Active",
            "analytics_enabled": "Analytics Enabled",
            "insights_available": "Insights Available",
            "trends_available": "Trends Available",
            "history_available": "History Available",
            "settings_modified": "Settings Modified",
            "configuration_changed": "Configuration Changed",
            "schedule_active": "Schedule Active",
            "routine_enabled": "Routine Enabled",
        }
        return name_map.get(sensor_type, sensor_type.replace("_", " ").title())

    def _set_sensor_properties(self, sensor_type: str) -> None:
        """Set device class based on sensor type."""
        if "online" in sensor_type.lower() or "connected" in sensor_type.lower():
            self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        elif "error" in sensor_type.lower() or "warning" in sensor_type.lower():
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        elif "update" in sensor_type.lower() or "firmware" in sensor_type.lower():
            self._attr_device_class = BinarySensorDeviceClass.UPDATE
        elif "maintenance" in sensor_type.lower():
            self._attr_device_class = BinarySensorDeviceClass.MAINTENANCE
        else:
            self._attr_device_class = None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self._eight:
            return None

        try:
            if self._sensor_type == "device_online":
                return self._eight.device_data is not None
            elif self._sensor_type == "priming_needed":
                return self._eight.need_priming
            elif self._sensor_type == "is_priming":
                return self._eight.is_priming
            elif self._sensor_type == "has_water":
                return self._eight.has_water
            elif self._sensor_type == "device_connected":
                return self._eight.device_data is not None
            elif self._sensor_type == "firmware_updating":
                return self._get_firmware_updating()
            elif self._sensor_type == "maintenance_required":
                return self._get_maintenance_required()
            elif self._sensor_type == "error_detected":
                return self._get_error_detected()
            elif self._sensor_type == "warning_active":
                return self._get_warning_active()
            elif self._sensor_type == "notification_pending":
                return self._get_notification_pending()
            elif self._sensor_type == "alert_active":
                return self._get_alert_active()
            elif self._sensor_type == "update_available":
                return self._get_update_available()
            elif self._sensor_type == "support_needed":
                return self._get_support_needed()
            elif self._sensor_type == "warranty_active":
                return self._get_warranty_active()
            elif self._sensor_type == "analytics_enabled":
                return self._get_analytics_enabled()
            elif self._sensor_type == "insights_available":
                return self._get_insights_available()
            elif self._sensor_type == "trends_available":
                return self._get_trends_available()
            elif self._sensor_type == "history_available":
                return self._get_history_available()
            elif self._sensor_type == "settings_modified":
                return self._get_settings_modified()
            elif self._sensor_type == "configuration_changed":
                return self._get_configuration_changed()
            elif self._sensor_type == "schedule_active":
                return self._get_schedule_active()
            elif self._sensor_type == "routine_enabled":
                return self._get_routine_enabled()
            else:
                return None
        except Exception as e:
            _LOGGER.error(f"Error getting {self._sensor_type} value: {e}")
            return None

    def _get_firmware_updating(self) -> bool:
        """Get firmware updating status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("firmwareUpdating", False)
        except Exception as e:
            _LOGGER.error(f"Error getting firmware updating: {e}")
        return False

    def _get_maintenance_required(self) -> bool:
        """Get maintenance required status."""
        try:
            return self._eight.need_priming or not self._eight.has_water
        except Exception as e:
            _LOGGER.error(f"Error getting maintenance required: {e}")
        return False

    def _get_error_detected(self) -> bool:
        """Get error detected status."""
        try:
            if self._eight.device_data:
                errors = self._eight.device_data.get("errors", [])
                return len(errors) > 0
        except Exception as e:
            _LOGGER.error(f"Error getting error detected: {e}")
        return False

    def _get_warning_active(self) -> bool:
        """Get warning active status."""
        try:
            if self._eight.device_data:
                warnings = self._eight.device_data.get("warnings", [])
                return len(warnings) > 0
        except Exception as e:
            _LOGGER.error(f"Error getting warning active: {e}")
        return False

    def _get_notification_pending(self) -> bool:
        """Get notification pending status."""
        try:
            if self._eight.device_data:
                notifications = self._eight.device_data.get("notifications", [])
                return len(notifications) > 0
        except Exception as e:
            _LOGGER.error(f"Error getting notification pending: {e}")
        return False

    def _get_alert_active(self) -> bool:
        """Get alert active status."""
        try:
            if self._eight.device_data:
                alerts = self._eight.device_data.get("alerts", [])
                return len(alerts) > 0
        except Exception as e:
            _LOGGER.error(f"Error getting alert active: {e}")
        return False

    def _get_update_available(self) -> bool:
        """Get update available status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("updateAvailable", False)
        except Exception as e:
            _LOGGER.error(f"Error getting update available: {e}")
        return False

    def _get_support_needed(self) -> bool:
        """Get support needed status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("supportNeeded", False)
        except Exception as e:
            _LOGGER.error(f"Error getting support needed: {e}")
        return False

    def _get_warranty_active(self) -> bool:
        """Get warranty active status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("warrantyActive", True)
        except Exception as e:
            _LOGGER.error(f"Error getting warranty active: {e}")
        return False

    def _get_analytics_enabled(self) -> bool:
        """Get analytics enabled status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("analyticsEnabled", True)
        except Exception as e:
            _LOGGER.error(f"Error getting analytics enabled: {e}")
        return False

    def _get_insights_available(self) -> bool:
        """Get insights available status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("insightsAvailable", True)
        except Exception as e:
            _LOGGER.error(f"Error getting insights available: {e}")
        return False

    def _get_trends_available(self) -> bool:
        """Get trends available status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("trendsAvailable", True)
        except Exception as e:
            _LOGGER.error(f"Error getting trends available: {e}")
        return False

    def _get_history_available(self) -> bool:
        """Get history available status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("historyAvailable", True)
        except Exception as e:
            _LOGGER.error(f"Error getting history available: {e}")
        return False

    def _get_settings_modified(self) -> bool:
        """Get settings modified status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("settingsModified", False)
        except Exception as e:
            _LOGGER.error(f"Error getting settings modified: {e}")
        return False

    def _get_configuration_changed(self) -> bool:
        """Get configuration changed status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("configurationChanged", False)
        except Exception as e:
            _LOGGER.error(f"Error getting configuration changed: {e}")
        return False

    def _get_schedule_active(self) -> bool:
        """Get schedule active status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("scheduleActive", False)
        except Exception as e:
            _LOGGER.error(f"Error getting schedule active: {e}")
        return False

    def _get_routine_enabled(self) -> bool:
        """Get routine enabled status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("routineEnabled", False)
        except Exception as e:
            _LOGGER.error(f"Error getting routine enabled: {e}")
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if not self._eight:
            return None

        attrs = {
            "sensor_type": self._sensor_type,
            "device_id": self._eight.device_id,
            "is_pod": self._eight.is_pod,
            "has_base": self._eight.has_base,
        }

        return attrs
