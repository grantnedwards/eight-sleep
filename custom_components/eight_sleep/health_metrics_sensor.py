"""Support for Eight Sleep Health Metrics sensors."""

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

# Health Metrics Sensor Types
HEALTH_METRICS_SENSORS = [
    "current_hrv",
    "current_heart_rate", 
    "current_respiratory_rate",
    "current_breath_rate",
    "last_hrv",
    "last_heart_rate",
    "last_respiratory_rate",
    "last_breath_rate",
    "hrv_score",
    "heart_rate_score",
    "respiratory_rate_score",
    "health_insight",
    "hrv_algorithm_version",
    "mean_respiratory_rate",
    "current_hrv_trend",
    "heart_rate_variability",
    "respiratory_rate_trend",
    "breathing_quality_score",
    "cardiovascular_fitness_score",
    "recovery_score",
]

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep Health Metrics sensors."""
    config_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    coordinator = config_data.coordinator
    eight = config_data.eight

    entities = []

    # Add health metrics sensors for each user
    for user in eight.users.values():
        for sensor_type in HEALTH_METRICS_SENSORS:
            entities.append(
                EightHealthMetricsSensor(
                    entry,
                    coordinator,
                    eight,
                    user,
                    sensor_type,
                )
            )

    async_add_entities(entities)


class EightHealthMetricsSensor(EightSleepBaseEntity, SensorEntity):
    """Representation of an Eight Sleep Health Metrics sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        sensor_type: str,
    ) -> None:
        """Initialize the health metrics sensor."""
        super().__init__(entry, coordinator, eight, user)
        self._sensor_type = sensor_type
        self._attr_name = f"{self._user.side} {self._get_sensor_name(sensor_type)}"
        self._attr_unique_id = f"{self._user.user_id}_{sensor_type}"
        
        # Set device class and unit based on sensor type
        self._set_sensor_properties(sensor_type)

    def _get_sensor_name(self, sensor_type: str) -> str:
        """Get the display name for the sensor type."""
        name_map = {
            "current_hrv": "HRV (Current)",
            "current_heart_rate": "Heart Rate (Current)",
            "current_respiratory_rate": "Respiratory Rate (Current)",
            "current_breath_rate": "Breathing Rate (Current)",
            "last_hrv": "HRV (Last Session)",
            "last_heart_rate": "Heart Rate (Last Session)",
            "last_respiratory_rate": "Respiratory Rate (Last Session)",
            "last_breath_rate": "Breathing Rate (Last Session)",
            "hrv_score": "HRV Score",
            "heart_rate_score": "Heart Rate Score",
            "respiratory_rate_score": "Respiratory Rate Score",
            "health_insight": "Health Insight",
            "hrv_algorithm_version": "HRV Algorithm Version",
            "mean_respiratory_rate": "Mean Respiratory Rate",
            "current_hrv_trend": "HRV Trend",
            "heart_rate_variability": "Heart Rate Variability",
            "respiratory_rate_trend": "Respiratory Rate Trend",
            "breathing_quality_score": "Breathing Quality Score",
            "cardiovascular_fitness_score": "Cardiovascular Fitness Score",
            "recovery_score": "Recovery Score",
        }
        return name_map.get(sensor_type, sensor_type.replace("_", " ").title())

    def _set_sensor_properties(self, sensor_type: str) -> None:
        """Set device class, unit, and state class based on sensor type."""
        if "hrv" in sensor_type.lower():
            self._attr_device_class = SensorDeviceClass.VOLTAGE  # Closest match for HRV
            self._attr_native_unit_of_measurement = "ms"  # Milliseconds for HRV
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "heart_rate" in sensor_type.lower():
            self._attr_device_class = SensorDeviceClass.FREQUENCY
            self._attr_native_unit_of_measurement = "bpm"  # Beats per minute
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "respiratory" in sensor_type.lower() or "breath" in sensor_type.lower():
            self._attr_device_class = SensorDeviceClass.FREQUENCY
            self._attr_native_unit_of_measurement = "breaths/min"
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "score" in sensor_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
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
            if self._sensor_type == "current_hrv":
                return self._user.current_hrv
            elif self._sensor_type == "current_heart_rate":
                return self._user.current_heart_rate
            elif self._sensor_type == "current_respiratory_rate":
                return self._user.current_resp_rate
            elif self._sensor_type == "current_breath_rate":
                return self._user.current_breath_rate
            elif self._sensor_type == "last_hrv":
                return self._user.last_hrv
            elif self._sensor_type == "last_heart_rate":
                return self._user.last_heart_rate
            elif self._sensor_type == "last_respiratory_rate":
                return self._user.last_resp_rate
            elif self._sensor_type == "last_breath_rate":
                return self._user.last_breath_rate
            elif self._sensor_type == "hrv_score":
                return self._get_hrv_score()
            elif self._sensor_type == "heart_rate_score":
                return self._get_heart_rate_score()
            elif self._sensor_type == "respiratory_rate_score":
                return self._get_respiratory_rate_score()
            elif self._sensor_type == "health_insight":
                return self._get_health_insight()
            elif self._sensor_type == "hrv_algorithm_version":
                return self._get_hrv_algorithm_version()
            elif self._sensor_type == "mean_respiratory_rate":
                return self._get_mean_respiratory_rate()
            elif self._sensor_type == "current_hrv_trend":
                return self._get_current_hrv_trend()
            elif self._sensor_type == "heart_rate_variability":
                return self._get_heart_rate_variability()
            elif self._sensor_type == "respiratory_rate_trend":
                return self._get_respiratory_rate_trend()
            elif self._sensor_type == "breathing_quality_score":
                return self._get_breathing_quality_score()
            elif self._sensor_type == "cardiovascular_fitness_score":
                return self._get_cardiovascular_fitness_score()
            elif self._sensor_type == "recovery_score":
                return self._get_recovery_score()
            else:
                return None
        except Exception as e:
            _LOGGER.error(f"Error getting {self._sensor_type} value: {e}")
            return None

    def _get_hrv_score(self) -> int | None:
        """Get HRV score from sleep quality data."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepQualityScore", {}).get("hrv", {}).get("score")
        except Exception as e:
            _LOGGER.error(f"Error getting HRV score: {e}")
        return None

    def _get_heart_rate_score(self) -> int | None:
        """Get heart rate score from sleep quality data."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepQualityScore", {}).get("heartRate", {}).get("score")
        except Exception as e:
            _LOGGER.error(f"Error getting heart rate score: {e}")
        return None

    def _get_respiratory_rate_score(self) -> int | None:
        """Get respiratory rate score from sleep quality data."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepQualityScore", {}).get("respiratoryRate", {}).get("score")
        except Exception as e:
            _LOGGER.error(f"Error getting respiratory rate score: {e}")
        return None

    def _get_health_insight(self) -> str | None:
        """Get health insight from user profile."""
        try:
            if self._user.user_profile:
                notifications = self._user.user_profile.get("notifications", {})
                return notifications.get("healthInsight")
        except Exception as e:
            _LOGGER.error(f"Error getting health insight: {e}")
        return None

    def _get_hrv_algorithm_version(self) -> str | None:
        """Get HRV algorithm version from trends data."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                sessions = current_trend.get("sessions", [])
                if sessions:
                    return sessions[-1].get("hrvAlgorithmVersion")
        except Exception as e:
            _LOGGER.error(f"Error getting HRV algorithm version: {e}")
        return None

    def _get_mean_respiratory_rate(self) -> float | None:
        """Get mean respiratory rate from trends data."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepQualityScore", {}).get("respiratoryRate", {}).get("average")
        except Exception as e:
            _LOGGER.error(f"Error getting mean respiratory rate: {e}")
        return None

    def _get_current_hrv_trend(self) -> float | None:
        """Get current HRV trend value."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepQualityScore", {}).get("hrv", {}).get("current")
        except Exception as e:
            _LOGGER.error(f"Error getting current HRV trend: {e}")
        return None

    def _get_heart_rate_variability(self) -> float | None:
        """Get heart rate variability value."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepQualityScore", {}).get("hrv", {}).get("current")
        except Exception as e:
            _LOGGER.error(f"Error getting heart rate variability: {e}")
        return None

    def _get_respiratory_rate_trend(self) -> float | None:
        """Get respiratory rate trend value."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepQualityScore", {}).get("respiratoryRate", {}).get("current")
        except Exception as e:
            _LOGGER.error(f"Error getting respiratory rate trend: {e}")
        return None

    def _get_breathing_quality_score(self) -> int | None:
        """Get breathing quality score."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepQualityScore", {}).get("respiratoryRate", {}).get("score")
        except Exception as e:
            _LOGGER.error(f"Error getting breathing quality score: {e}")
        return None

    def _get_cardiovascular_fitness_score(self) -> int | None:
        """Get cardiovascular fitness score."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepQualityScore", {}).get("heartRate", {}).get("score")
        except Exception as e:
            _LOGGER.error(f"Error getting cardiovascular fitness score: {e}")
        return None

    def _get_recovery_score(self) -> int | None:
        """Get recovery score based on HRV and other metrics."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                hrv_score = current_trend.get("sleepQualityScore", {}).get("hrv", {}).get("score", 0)
                heart_rate_score = current_trend.get("sleepQualityScore", {}).get("heartRate", {}).get("score", 0)
                # Calculate recovery score as average of HRV and heart rate scores
                return (hrv_score + heart_rate_score) // 2
        except Exception as e:
            _LOGGER.error(f"Error getting recovery score: {e}")
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

        # Add health-specific attributes
        if "hrv" in self._sensor_type.lower():
            attrs["hrv_algorithm_version"] = self._get_hrv_algorithm_version()
            attrs["hrv_trend"] = self._get_current_hrv_trend()
        elif "heart_rate" in self._sensor_type.lower():
            attrs["heart_rate_variability"] = self._get_heart_rate_variability()
            attrs["cardiovascular_fitness_score"] = self._get_cardiovascular_fitness_score()
        elif "respiratory" in self._sensor_type.lower() or "breath" in self._sensor_type.lower():
            attrs["mean_respiratory_rate"] = self._get_mean_respiratory_rate()
            attrs["breathing_quality_score"] = self._get_breathing_quality_score()
            attrs["respiratory_rate_trend"] = self._get_respiratory_rate_trend()

        return attrs 