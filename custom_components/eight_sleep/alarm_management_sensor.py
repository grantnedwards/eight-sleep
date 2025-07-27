"""Support for Eight Sleep Alarm Management sensors."""

from __future__ import annotations

import logging
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
    CONF_BINARY_SENSORS,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import EightSleepBaseEntity, EightSleepConfigEntryData
from .const import DOMAIN
from .pyEight.user import EightUser
from .pyEight.eight import EightSleep

_LOGGER = logging.getLogger(__name__)

# Alarm Management Sensor Types
ALARM_MANAGEMENT_SENSORS = [
    "alarm_enabled",
    "alarm_time",
    "alarm_days",
    "alarm_snooze_time",
    "alarm_snooze_count",
    "alarm_dismissed",
    "alarm_ringing",
    "alarm_stopped",
    "alarm_wakeup_push",
    "alarm_insight",
    "alarm_notification",
    "alarm_alert",
    "alarm_status",
    "alarm_state",
    "alarm_quality",
    "alarm_consistency",
    "alarm_reliability",
    "alarm_accuracy",
    "alarm_analytics",
    "alarm_insights",
    "alarm_trends",
    "alarm_history",
    "alarm_settings",
    "alarm_configuration",
    "alarm_schedule",
    "alarm_routine",
    "alarm_preferences",
    "alarm_options",
    "alarm_features",
    "alarm_capabilities",
]

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep Alarm Management sensors."""
    config_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    coordinator = config_data.coordinator
    eight = config_data.eight

    entities = []

    # Add alarm management sensors for each user
    for user in eight.users.values():
        for sensor_type in ALARM_MANAGEMENT_SENSORS:
            entities.append(
                EightAlarmManagementSensor(
                    entry,
                    coordinator,
                    eight,
                    user,
                    sensor_type,
                )
            )

    async_add_entities(entities)


class EightAlarmManagementSensor(EightSleepBaseEntity, SensorEntity):
    """Representation of an Eight Sleep Alarm Management sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        sensor_type: str,
    ) -> None:
        """Initialize the alarm management sensor."""
        super().__init__(entry, coordinator, eight, user)
        self._sensor_type = sensor_type
        self._attr_name = f"{self._user.side} {self._get_sensor_name(sensor_type)}"
        self._attr_unique_id = f"{self._user.user_id}_{sensor_type}"
        
        # Set device class and unit based on sensor type
        self._set_sensor_properties(sensor_type)

    def _get_sensor_name(self, sensor_type: str) -> str:
        """Get the display name for the sensor type."""
        name_map = {
            "alarm_enabled": "Alarm Enabled",
            "alarm_time": "Alarm Time",
            "alarm_days": "Alarm Days",
            "alarm_snooze_time": "Alarm Snooze Time",
            "alarm_snooze_count": "Alarm Snooze Count",
            "alarm_dismissed": "Alarm Dismissed",
            "alarm_ringing": "Alarm Ringing",
            "alarm_stopped": "Alarm Stopped",
            "alarm_wakeup_push": "Alarm Wakeup Push",
            "alarm_insight": "Alarm Insight",
            "alarm_notification": "Alarm Notification",
            "alarm_alert": "Alarm Alert",
            "alarm_status": "Alarm Status",
            "alarm_state": "Alarm State",
            "alarm_quality": "Alarm Quality",
            "alarm_consistency": "Alarm Consistency",
            "alarm_reliability": "Alarm Reliability",
            "alarm_accuracy": "Alarm Accuracy",
            "alarm_analytics": "Alarm Analytics",
            "alarm_insights": "Alarm Insights",
            "alarm_trends": "Alarm Trends",
            "alarm_history": "Alarm History",
            "alarm_settings": "Alarm Settings",
            "alarm_configuration": "Alarm Configuration",
            "alarm_schedule": "Alarm Schedule",
            "alarm_routine": "Alarm Routine",
            "alarm_preferences": "Alarm Preferences",
            "alarm_options": "Alarm Options",
            "alarm_features": "Alarm Features",
            "alarm_capabilities": "Alarm Capabilities",
        }
        return name_map.get(sensor_type, sensor_type.replace("_", " ").title())

    def _set_sensor_properties(self, sensor_type: str) -> None:
        """Set device class, unit, and state class based on sensor type."""
        if "time" in sensor_type.lower():
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = None
        elif "count" in sensor_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = "count"
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "quality" in sensor_type.lower() or "accuracy" in sensor_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "status" in sensor_type.lower() or "state" in sensor_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = None
        else:
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> str | int | float | None:
        """Return the state of the sensor."""
        if not self._user:
            return None

        try:
            if self._sensor_type == "alarm_enabled":
                return self._get_alarm_enabled()
            elif self._sensor_type == "alarm_time":
                return self._get_alarm_time()
            elif self._sensor_type == "alarm_days":
                return self._get_alarm_days()
            elif self._sensor_type == "alarm_snooze_time":
                return self._get_alarm_snooze_time()
            elif self._sensor_type == "alarm_snooze_count":
                return self._get_alarm_snooze_count()
            elif self._sensor_type == "alarm_dismissed":
                return self._get_alarm_dismissed()
            elif self._sensor_type == "alarm_ringing":
                return self._get_alarm_ringing()
            elif self._sensor_type == "alarm_stopped":
                return self._get_alarm_stopped()
            elif self._sensor_type == "alarm_wakeup_push":
                return self._get_alarm_wakeup_push()
            elif self._sensor_type == "alarm_insight":
                return self._get_alarm_insight()
            elif self._sensor_type == "alarm_notification":
                return self._get_alarm_notification()
            elif self._sensor_type == "alarm_alert":
                return self._get_alarm_alert()
            elif self._sensor_type == "alarm_status":
                return self._get_alarm_status()
            elif self._sensor_type == "alarm_state":
                return self._get_alarm_state()
            elif self._sensor_type == "alarm_quality":
                return self._get_alarm_quality()
            elif self._sensor_type == "alarm_consistency":
                return self._get_alarm_consistency()
            elif self._sensor_type == "alarm_reliability":
                return self._get_alarm_reliability()
            elif self._sensor_type == "alarm_accuracy":
                return self._get_alarm_accuracy()
            elif self._sensor_type == "alarm_analytics":
                return self._get_alarm_analytics()
            elif self._sensor_type == "alarm_insights":
                return self._get_alarm_insights()
            elif self._sensor_type == "alarm_trends":
                return self._get_alarm_trends()
            elif self._sensor_type == "alarm_history":
                return self._get_alarm_history()
            elif self._sensor_type == "alarm_settings":
                return self._get_alarm_settings()
            elif self._sensor_type == "alarm_configuration":
                return self._get_alarm_configuration()
            elif self._sensor_type == "alarm_schedule":
                return self._get_alarm_schedule()
            elif self._sensor_type == "alarm_routine":
                return self._get_alarm_routine()
            elif self._sensor_type == "alarm_preferences":
                return self._get_alarm_preferences()
            elif self._sensor_type == "alarm_options":
                return self._get_alarm_options()
            elif self._sensor_type == "alarm_features":
                return self._get_alarm_features()
            elif self._sensor_type == "alarm_capabilities":
                return self._get_alarm_capabilities()
            else:
                return None
        except Exception as e:
            _LOGGER.error(f"Error getting {self._sensor_type} value: {e}")
            return None

    def _get_alarm_enabled(self) -> bool | None:
        """Get alarm enabled status."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("enabled", False)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm enabled: {e}")
        return None

    def _get_alarm_time(self) -> str | None:
        """Get alarm time."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("time")
        except Exception as e:
            _LOGGER.error(f"Error getting alarm time: {e}")
        return None

    def _get_alarm_days(self) -> str | None:
        """Get alarm days."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    days = side_alarms[0].get("days", [])
                    if days:
                        return ", ".join(days)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm days: {e}")
        return None

    def _get_alarm_snooze_time(self) -> str | None:
        """Get alarm snooze time."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("snoozeTime")
        except Exception as e:
            _LOGGER.error(f"Error getting alarm snooze time: {e}")
        return None

    def _get_alarm_snooze_count(self) -> int | None:
        """Get alarm snooze count."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("snoozeCount", 0)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm snooze count: {e}")
        return None

    def _get_alarm_dismissed(self) -> bool | None:
        """Get alarm dismissed status."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("dismissed", False)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm dismissed: {e}")
        return None

    def _get_alarm_ringing(self) -> bool | None:
        """Get alarm ringing status."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("ringing", False)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm ringing: {e}")
        return None

    def _get_alarm_stopped(self) -> bool | None:
        """Get alarm stopped status."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("stopped", False)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm stopped: {e}")
        return None

    def _get_alarm_wakeup_push(self) -> str | None:
        """Get alarm wakeup push notification."""
        try:
            if self._user.user_profile:
                notifications = self._user.user_profile.get("notifications", {})
                return notifications.get("alarmWakeupPush")
        except Exception as e:
            _LOGGER.error(f"Error getting alarm wakeup push: {e}")
        return None

    def _get_alarm_insight(self) -> str | None:
        """Get alarm insight."""
        try:
            if self._user.user_profile:
                notifications = self._user.user_profile.get("notifications", {})
                return notifications.get("alarmInsight")
        except Exception as e:
            _LOGGER.error(f"Error getting alarm insight: {e}")
        return None

    def _get_alarm_notification(self) -> str | None:
        """Get alarm notification."""
        try:
            if self._user.user_profile:
                notifications = self._user.user_profile.get("notifications", {})
                return notifications.get("alarmNotification")
        except Exception as e:
            _LOGGER.error(f"Error getting alarm notification: {e}")
        return None

    def _get_alarm_alert(self) -> str | None:
        """Get alarm alert."""
        try:
            if self._user.user_profile:
                alerts = self._user.user_profile.get("alerts", {})
                return alerts.get("alarmAlert")
        except Exception as e:
            _LOGGER.error(f"Error getting alarm alert: {e}")
        return None

    def _get_alarm_status(self) -> str | None:
        """Get alarm status."""
        try:
            if self._get_alarm_ringing():
                return "Ringing"
            elif self._get_alarm_dismissed():
                return "Dismissed"
            elif self._get_alarm_stopped():
                return "Stopped"
            elif self._get_alarm_enabled():
                return "Enabled"
            else:
                return "Disabled"
        except Exception as e:
            _LOGGER.error(f"Error getting alarm status: {e}")
        return None

    def _get_alarm_state(self) -> str | None:
        """Get alarm state."""
        try:
            if self._get_alarm_ringing():
                return "Active"
            elif self._get_alarm_snooze_count() and self._get_alarm_snooze_count() > 0:
                return "Snoozed"
            elif self._get_alarm_enabled():
                return "Set"
            else:
                return "Off"
        except Exception as e:
            _LOGGER.error(f"Error getting alarm state: {e}")
        return None

    def _get_alarm_quality(self) -> float | None:
        """Get alarm quality score."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("alarmQuality")
        except Exception as e:
            _LOGGER.error(f"Error getting alarm quality: {e}")
        return None

    def _get_alarm_consistency(self) -> float | None:
        """Get alarm consistency score."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("alarmConsistency")
        except Exception as e:
            _LOGGER.error(f"Error getting alarm consistency: {e}")
        return None

    def _get_alarm_reliability(self) -> float | None:
        """Get alarm reliability score."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("alarmReliability")
        except Exception as e:
            _LOGGER.error(f"Error getting alarm reliability: {e}")
        return None

    def _get_alarm_accuracy(self) -> float | None:
        """Get alarm accuracy score."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("alarmAccuracy")
        except Exception as e:
            _LOGGER.error(f"Error getting alarm accuracy: {e}")
        return None

    def _get_alarm_analytics(self) -> str | None:
        """Get alarm analytics."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return str(current_trend.get("alarmAnalytics", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting alarm analytics: {e}")
        return None

    def _get_alarm_insights(self) -> str | None:
        """Get alarm insights."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return str(current_trend.get("alarmInsights", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting alarm insights: {e}")
        return None

    def _get_alarm_trends(self) -> str | None:
        """Get alarm trends."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return str(current_trend.get("alarmTrends", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting alarm trends: {e}")
        return None

    def _get_alarm_history(self) -> str | None:
        """Get alarm history."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return str(current_trend.get("alarmHistory", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting alarm history: {e}")
        return None

    def _get_alarm_settings(self) -> str | None:
        """Get alarm settings."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return str(side_alarms[0].get("settings", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting alarm settings: {e}")
        return None

    def _get_alarm_configuration(self) -> str | None:
        """Get alarm configuration."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return str(side_alarms[0].get("configuration", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting alarm configuration: {e}")
        return None

    def _get_alarm_schedule(self) -> str | None:
        """Get alarm schedule."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return str(side_alarms[0].get("schedule", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting alarm schedule: {e}")
        return None

    def _get_alarm_routine(self) -> str | None:
        """Get alarm routine."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return str(side_alarms[0].get("routine", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting alarm routine: {e}")
        return None

    def _get_alarm_preferences(self) -> str | None:
        """Get alarm preferences."""
        try:
            if self._user.user_profile:
                return str(self._user.user_profile.get("alarmPreferences", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting alarm preferences: {e}")
        return None

    def _get_alarm_options(self) -> str | None:
        """Get alarm options."""
        try:
            if self._user.user_profile:
                return str(self._user.user_profile.get("alarmOptions", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting alarm options: {e}")
        return None

    def _get_alarm_features(self) -> str | None:
        """Get alarm features."""
        try:
            features = []
            if self._get_alarm_enabled():
                features.append("Enabled")
            if self._get_alarm_snooze_time():
                features.append("Snooze")
            if self._get_alarm_days():
                features.append("Schedule")
            if features:
                return ", ".join(features)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm features: {e}")
        return None

    def _get_alarm_capabilities(self) -> str | None:
        """Get alarm capabilities."""
        try:
            capabilities = ["Time", "Days", "Snooze", "Dismiss", "Stop"]
            return ", ".join(capabilities)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm capabilities: {e}")
        return None

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

        # Add alarm-specific attributes
        if "alarm" in self._sensor_type.lower():
            attrs["alarm_enabled"] = self._get_alarm_enabled()
            attrs["alarm_time"] = self._get_alarm_time()
            attrs["alarm_days"] = self._get_alarm_days()
            attrs["alarm_snooze_time"] = self._get_alarm_snooze_time()
            attrs["alarm_snooze_count"] = self._get_alarm_snooze_count()
            attrs["alarm_dismissed"] = self._get_alarm_dismissed()
            attrs["alarm_ringing"] = self._get_alarm_ringing()
            attrs["alarm_stopped"] = self._get_alarm_stopped()
            attrs["alarm_status"] = self._get_alarm_status()
            attrs["alarm_state"] = self._get_alarm_state()

        return attrs 