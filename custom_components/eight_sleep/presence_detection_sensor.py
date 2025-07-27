"""Support for Eight Sleep Presence Detection sensors."""

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

# Presence Detection Sensor Types
PRESENCE_DETECTION_SENSORS = [
    "bed_presence",
    "away_mode_status",
    "presence_duration",
    "presence_start_time",
    "presence_end_time",
    "away_sides",
    "presence_confidence",
    "presence_detection_enabled",
    "presence_algorithm_version",
    "presence_trend",
    "presence_analytics",
    "presence_insights",
    "presence_notifications",
    "presence_alerts",
    "presence_status",
    "presence_state",
    "presence_quality",
    "presence_consistency",
    "presence_reliability",
    "presence_accuracy",
]

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep Presence Detection sensors."""
    config_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    coordinator = config_data.coordinator
    eight = config_data.eight

    entities = []

    # Add presence detection sensors for each user
    for user in eight.users.values():
        for sensor_type in PRESENCE_DETECTION_SENSORS:
            entities.append(
                EightPresenceDetectionSensor(
                    entry,
                    coordinator,
                    eight,
                    user,
                    sensor_type,
                )
            )

    async_add_entities(entities)


class EightPresenceDetectionSensor(EightSleepBaseEntity, SensorEntity):
    """Representation of an Eight Sleep Presence Detection sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        sensor_type: str,
    ) -> None:
        """Initialize the presence detection sensor."""
        super().__init__(entry, coordinator, eight, user)
        self._sensor_type = sensor_type
        self._attr_name = f"{self._user.side} {self._get_sensor_name(sensor_type)}"
        self._attr_unique_id = f"{self._user.user_id}_{sensor_type}"
        
        # Set device class and unit based on sensor type
        self._set_sensor_properties(sensor_type)

    def _get_sensor_name(self, sensor_type: str) -> str:
        """Get the display name for the sensor type."""
        name_map = {
            "bed_presence": "Bed Presence",
            "away_mode_status": "Away Mode Status",
            "presence_duration": "Presence Duration",
            "presence_start_time": "Presence Start Time",
            "presence_end_time": "Presence End Time",
            "away_sides": "Away Sides",
            "presence_confidence": "Presence Confidence",
            "presence_detection_enabled": "Presence Detection Enabled",
            "presence_algorithm_version": "Presence Algorithm Version",
            "presence_trend": "Presence Trend",
            "presence_analytics": "Presence Analytics",
            "presence_insights": "Presence Insights",
            "presence_notifications": "Presence Notifications",
            "presence_alerts": "Presence Alerts",
            "presence_status": "Presence Status",
            "presence_state": "Presence State",
            "presence_quality": "Presence Quality",
            "presence_consistency": "Presence Consistency",
            "presence_reliability": "Presence Reliability",
            "presence_accuracy": "Presence Accuracy",
        }
        return name_map.get(sensor_type, sensor_type.replace("_", " ").title())

    def _set_sensor_properties(self, sensor_type: str) -> None:
        """Set device class, unit, and state class based on sensor type."""
        if "duration" in sensor_type.lower():
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "confidence" in sensor_type.lower() or "quality" in sensor_type.lower() or "accuracy" in sensor_type.lower():
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
            if self._sensor_type == "bed_presence":
                return self._user.bed_presence
            elif self._sensor_type == "away_mode_status":
                return self._get_away_mode_status()
            elif self._sensor_type == "presence_duration":
                return self._get_presence_duration()
            elif self._sensor_type == "presence_start_time":
                return self._get_presence_start_time()
            elif self._sensor_type == "presence_end_time":
                return self._get_presence_end_time()
            elif self._sensor_type == "away_sides":
                return self._get_away_sides()
            elif self._sensor_type == "presence_confidence":
                return self._get_presence_confidence()
            elif self._sensor_type == "presence_detection_enabled":
                return self._get_presence_detection_enabled()
            elif self._sensor_type == "presence_algorithm_version":
                return self._get_presence_algorithm_version()
            elif self._sensor_type == "presence_trend":
                return self._get_presence_trend()
            elif self._sensor_type == "presence_analytics":
                return self._get_presence_analytics()
            elif self._sensor_type == "presence_insights":
                return self._get_presence_insights()
            elif self._sensor_type == "presence_notifications":
                return self._get_presence_notifications()
            elif self._sensor_type == "presence_alerts":
                return self._get_presence_alerts()
            elif self._sensor_type == "presence_status":
                return self._get_presence_status()
            elif self._sensor_type == "presence_state":
                return self._get_presence_state()
            elif self._sensor_type == "presence_quality":
                return self._get_presence_quality()
            elif self._sensor_type == "presence_consistency":
                return self._get_presence_consistency()
            elif self._sensor_type == "presence_reliability":
                return self._get_presence_reliability()
            elif self._sensor_type == "presence_accuracy":
                return self._get_presence_accuracy()
            else:
                return None
        except Exception as e:
            _LOGGER.error(f"Error getting {self._sensor_type} value: {e}")
            return None

    def _get_away_mode_status(self) -> str | None:
        """Get away mode status."""
        try:
            if self._eight.device_data:
                away_sides = self._eight.device_data.get("awaySides", {})
                if self._user.side in away_sides:
                    return "Away"
                else:
                    return "Present"
        except Exception as e:
            _LOGGER.error(f"Error getting away mode status: {e}")
        return None

    def _get_presence_duration(self) -> int | None:
        """Get presence duration."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceDuration")
        except Exception as e:
            _LOGGER.error(f"Error getting presence duration: {e}")
        return None

    def _get_presence_start_time(self) -> str | None:
        """Get presence start time."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceStart")
        except Exception as e:
            _LOGGER.error(f"Error getting presence start time: {e}")
        return None

    def _get_presence_end_time(self) -> str | None:
        """Get presence end time."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceEnd")
        except Exception as e:
            _LOGGER.error(f"Error getting presence end time: {e}")
        return None

    def _get_away_sides(self) -> str | None:
        """Get away sides information."""
        try:
            if self._eight.device_data:
                away_sides = self._eight.device_data.get("awaySides", {})
                if away_sides:
                    return ", ".join(away_sides.keys())
                else:
                    return "None"
        except Exception as e:
            _LOGGER.error(f"Error getting away sides: {e}")
        return None

    def _get_presence_confidence(self) -> float | None:
        """Get presence confidence level."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceConfidence")
        except Exception as e:
            _LOGGER.error(f"Error getting presence confidence: {e}")
        return None

    def _get_presence_detection_enabled(self) -> bool | None:
        """Get presence detection enabled status."""
        try:
            if self._user.user_profile:
                return self._user.user_profile.get("presenceDetection", {}).get("enabled", True)
        except Exception as e:
            _LOGGER.error(f"Error getting presence detection enabled: {e}")
        return None

    def _get_presence_algorithm_version(self) -> str | None:
        """Get presence algorithm version."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceAlgorithmVersion")
        except Exception as e:
            _LOGGER.error(f"Error getting presence algorithm version: {e}")
        return None

    def _get_presence_trend(self) -> str | None:
        """Get presence trend."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceTrend")
        except Exception as e:
            _LOGGER.error(f"Error getting presence trend: {e}")
        return None

    def _get_presence_analytics(self) -> str | None:
        """Get presence analytics."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return str(current_trend.get("presenceAnalytics", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting presence analytics: {e}")
        return None

    def _get_presence_insights(self) -> str | None:
        """Get presence insights."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return str(current_trend.get("presenceInsights", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting presence insights: {e}")
        return None

    def _get_presence_notifications(self) -> str | None:
        """Get presence notifications."""
        try:
            if self._user.user_profile:
                notifications = self._user.user_profile.get("notifications", {})
                return notifications.get("presenceNotification")
        except Exception as e:
            _LOGGER.error(f"Error getting presence notifications: {e}")
        return None

    def _get_presence_alerts(self) -> str | None:
        """Get presence alerts."""
        try:
            if self._user.user_profile:
                alerts = self._user.user_profile.get("alerts", {})
                return alerts.get("presenceAlert")
        except Exception as e:
            _LOGGER.error(f"Error getting presence alerts: {e}")
        return None

    def _get_presence_status(self) -> str | None:
        """Get presence status."""
        try:
            if self._user.bed_presence:
                return "Present"
            else:
                return "Absent"
        except Exception as e:
            _LOGGER.error(f"Error getting presence status: {e}")
        return None

    def _get_presence_state(self) -> str | None:
        """Get presence state."""
        try:
            if self._user.bed_presence:
                return "In Bed"
            else:
                return "Out of Bed"
        except Exception as e:
            _LOGGER.error(f"Error getting presence state: {e}")
        return None

    def _get_presence_quality(self) -> float | None:
        """Get presence quality score."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceQuality")
        except Exception as e:
            _LOGGER.error(f"Error getting presence quality: {e}")
        return None

    def _get_presence_consistency(self) -> float | None:
        """Get presence consistency score."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceConsistency")
        except Exception as e:
            _LOGGER.error(f"Error getting presence consistency: {e}")
        return None

    def _get_presence_reliability(self) -> float | None:
        """Get presence reliability score."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceReliability")
        except Exception as e:
            _LOGGER.error(f"Error getting presence reliability: {e}")
        return None

    def _get_presence_accuracy(self) -> float | None:
        """Get presence accuracy score."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceAccuracy")
        except Exception as e:
            _LOGGER.error(f"Error getting presence accuracy: {e}")
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

        # Add presence-specific attributes
        if "presence" in self._sensor_type.lower():
            attrs["bed_presence"] = self._user.bed_presence
            attrs["presence_duration"] = self._get_presence_duration()
            attrs["presence_start_time"] = self._get_presence_start_time()
            attrs["presence_end_time"] = self._get_presence_end_time()
            attrs["presence_confidence"] = self._get_presence_confidence()
        elif "away" in self._sensor_type.lower():
            attrs["away_mode_status"] = self._get_away_mode_status()
            attrs["away_sides"] = self._get_away_sides()
            attrs["bed_presence"] = self._user.bed_presence

        return attrs 