"""Support for Eight Sleep Sleep Analytics sensors."""

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

# Sleep Analytics Sensor Types
SLEEP_ANALYTICS_SENSORS = [
    "sleep_quality_score",
    "sleep_efficiency_score",
    "sleep_fitness_score",
    "sleep_routine_score",
    "sleep_duration_score",
    "sleep_latency_score",
    "sleep_consistency_score",
    "sleep_breakdown_light",
    "sleep_breakdown_deep",
    "sleep_breakdown_rem",
    "sleep_breakdown_awake",
    "sleep_stage_current",
    "sleep_stage_last",
    "sleep_duration_current",
    "sleep_duration_last",
    "sleep_latency_asleep",
    "sleep_latency_out",
    "sleep_tnt_current",
    "sleep_tnt_last",
    "sleep_presence_duration",
    "sleep_processing_status",
    "sleep_session_start",
    "sleep_session_end",
    "sleep_insight",
    "sleep_tracking_enabled",
    "sleep_analytics_version",
    "sleep_quality_trend",
    "sleep_efficiency_trend",
    "sleep_consistency_trend",
    "sleep_recovery_score",
]

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep Sleep Analytics sensors."""
    config_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    coordinator = config_data.coordinator
    eight = config_data.eight

    entities = []

    # Add sleep analytics sensors for each user
    for user in eight.users.values():
        for sensor_type in SLEEP_ANALYTICS_SENSORS:
            entities.append(
                EightSleepAnalyticsSensor(
                    entry,
                    coordinator,
                    eight,
                    user,
                    sensor_type,
                )
            )

    async_add_entities(entities)


class EightSleepAnalyticsSensor(EightSleepBaseEntity, SensorEntity):
    """Representation of an Eight Sleep Sleep Analytics sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        sensor_type: str,
    ) -> None:
        """Initialize the sleep analytics sensor."""
        super().__init__(entry, coordinator, eight, user)
        self._sensor_type = sensor_type
        self._attr_name = f"{self._user.side} {self._get_sensor_name(sensor_type)}"
        self._attr_unique_id = f"{self._user.user_id}_{sensor_type}"
        
        # Set device class and unit based on sensor type
        self._set_sensor_properties(sensor_type)

    def _get_sensor_name(self, sensor_type: str) -> str:
        """Get the display name for the sensor type."""
        name_map = {
            "sleep_quality_score": "Sleep Quality Score",
            "sleep_efficiency_score": "Sleep Efficiency Score",
            "sleep_fitness_score": "Sleep Fitness Score",
            "sleep_routine_score": "Sleep Routine Score",
            "sleep_duration_score": "Sleep Duration Score",
            "sleep_latency_score": "Sleep Latency Score",
            "sleep_consistency_score": "Sleep Consistency Score",
            "sleep_breakdown_light": "Light Sleep Duration",
            "sleep_breakdown_deep": "Deep Sleep Duration",
            "sleep_breakdown_rem": "REM Sleep Duration",
            "sleep_breakdown_awake": "Awake Duration",
            "sleep_stage_current": "Current Sleep Stage",
            "sleep_stage_last": "Last Sleep Stage",
            "sleep_duration_current": "Current Sleep Duration",
            "sleep_duration_last": "Last Sleep Duration",
            "sleep_latency_asleep": "Time to Fall Asleep",
            "sleep_latency_out": "Time Out of Bed",
            "sleep_tnt_current": "Toss & Turns (Current)",
            "sleep_tnt_last": "Toss & Turns (Last)",
            "sleep_presence_duration": "Bed Presence Duration",
            "sleep_processing_status": "Sleep Processing Status",
            "sleep_session_start": "Sleep Session Start",
            "sleep_session_end": "Sleep Session End",
            "sleep_insight": "Sleep Insight",
            "sleep_tracking_enabled": "Sleep Tracking Enabled",
            "sleep_analytics_version": "Sleep Analytics Version",
            "sleep_quality_trend": "Sleep Quality Trend",
            "sleep_efficiency_trend": "Sleep Efficiency Trend",
            "sleep_consistency_trend": "Sleep Consistency Trend",
            "sleep_recovery_score": "Sleep Recovery Score",
        }
        return name_map.get(sensor_type, sensor_type.replace("_", " ").title())

    def _set_sensor_properties(self, sensor_type: str) -> None:
        """Set device class, unit, and state class based on sensor type."""
        if "duration" in sensor_type.lower() or "latency" in sensor_type.lower():
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "score" in sensor_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "stage" in sensor_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = None
        elif "tnt" in sensor_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = "count"
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
            if self._sensor_type == "sleep_quality_score":
                return self._user.current_sleep_quality_score
            elif self._sensor_type == "sleep_efficiency_score":
                return self._get_sleep_efficiency_score()
            elif self._sensor_type == "sleep_fitness_score":
                return self._user.current_sleep_fitness_score
            elif self._sensor_type == "sleep_routine_score":
                return self._user.current_sleep_routine_score
            elif self._sensor_type == "sleep_duration_score":
                return self._user.current_sleep_duration_score
            elif self._sensor_type == "sleep_latency_score":
                return self._user.current_latency_asleep_score
            elif self._sensor_type == "sleep_consistency_score":
                return self._user.current_wakeup_consistency_score
            elif self._sensor_type == "sleep_breakdown_light":
                return self._get_sleep_breakdown_duration("light")
            elif self._sensor_type == "sleep_breakdown_deep":
                return self._get_sleep_breakdown_duration("deep")
            elif self._sensor_type == "sleep_breakdown_rem":
                return self._get_sleep_breakdown_duration("rem")
            elif self._sensor_type == "sleep_breakdown_awake":
                return self._get_sleep_breakdown_duration("awake")
            elif self._sensor_type == "sleep_stage_current":
                return self._user.current_sleep_stage
            elif self._sensor_type == "sleep_stage_last":
                return self._get_last_sleep_stage()
            elif self._sensor_type == "sleep_duration_current":
                return self._user.time_slept
            elif self._sensor_type == "sleep_duration_last":
                return self._get_last_sleep_duration()
            elif self._sensor_type == "sleep_latency_asleep":
                return self._get_sleep_latency_asleep()
            elif self._sensor_type == "sleep_latency_out":
                return self._get_sleep_latency_out()
            elif self._sensor_type == "sleep_tnt_current":
                return self._user.current_tnt
            elif self._sensor_type == "sleep_tnt_last":
                return self._user.last_tnt
            elif self._sensor_type == "sleep_presence_duration":
                return self._get_presence_duration()
            elif self._sensor_type == "sleep_processing_status":
                return self._user.current_session_processing
            elif self._sensor_type == "sleep_session_start":
                return self._get_session_start()
            elif self._sensor_type == "sleep_session_end":
                return self._get_session_end()
            elif self._sensor_type == "sleep_insight":
                return self._get_sleep_insight()
            elif self._sensor_type == "sleep_tracking_enabled":
                return self._get_sleep_tracking_enabled()
            elif self._sensor_type == "sleep_analytics_version":
                return self._get_sleep_analytics_version()
            elif self._sensor_type == "sleep_quality_trend":
                return self._get_sleep_quality_trend()
            elif self._sensor_type == "sleep_efficiency_trend":
                return self._get_sleep_efficiency_trend()
            elif self._sensor_type == "sleep_consistency_trend":
                return self._get_sleep_consistency_trend()
            elif self._sensor_type == "sleep_recovery_score":
                return self._get_sleep_recovery_score()
            else:
                return None
        except Exception as e:
            _LOGGER.error(f"Error getting {self._sensor_type} value: {e}")
            return None

    def _get_sleep_efficiency_score(self) -> int | None:
        """Get sleep efficiency score."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepQualityScore", {}).get("sleepEfficiency", {}).get("score")
        except Exception as e:
            _LOGGER.error(f"Error getting sleep efficiency score: {e}")
        return None

    def _get_sleep_breakdown_duration(self, stage: str) -> int | None:
        """Get sleep stage breakdown duration."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                if stage == "light":
                    return current_trend.get("lightDuration")
                elif stage == "deep":
                    return current_trend.get("deepDuration")
                elif stage == "rem":
                    return current_trend.get("remDuration")
                elif stage == "awake":
                    presence_duration = current_trend.get("presenceDuration", 0)
                    sleep_duration = current_trend.get("sleepDuration", 0)
                    return presence_duration - sleep_duration
        except Exception as e:
            _LOGGER.error(f"Error getting sleep breakdown duration for {stage}: {e}")
        return None

    def _get_last_sleep_stage(self) -> str | None:
        """Get last sleep stage."""
        try:
            if self._user.trends and len(self._user.trends) > 1:
                last_trend = self._user.trends[-2]
                sessions = last_trend.get("sessions", [])
                if sessions:
                    stages = sessions[-1].get("stages", [])
                    if stages:
                        return stages[-1].get("stage")
        except Exception as e:
            _LOGGER.error(f"Error getting last sleep stage: {e}")
        return None

    def _get_last_sleep_duration(self) -> int | None:
        """Get last sleep duration."""
        try:
            if self._user.trends and len(self._user.trends) > 1:
                last_trend = self._user.trends[-2]
                return last_trend.get("sleepDuration")
        except Exception as e:
            _LOGGER.error(f"Error getting last sleep duration: {e}")
        return None

    def _get_sleep_latency_asleep(self) -> int | None:
        """Get sleep latency (time to fall asleep)."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepRoutineScore", {}).get("latencyAsleepSeconds", {}).get("score")
        except Exception as e:
            _LOGGER.error(f"Error getting sleep latency asleep: {e}")
        return None

    def _get_sleep_latency_out(self) -> int | None:
        """Get sleep latency out of bed."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepRoutineScore", {}).get("latencyOutSeconds", {}).get("score")
        except Exception as e:
            _LOGGER.error(f"Error getting sleep latency out: {e}")
        return None

    def _get_presence_duration(self) -> int | None:
        """Get bed presence duration."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceDuration")
        except Exception as e:
            _LOGGER.error(f"Error getting presence duration: {e}")
        return None

    def _get_session_start(self) -> str | None:
        """Get sleep session start time."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceStart")
        except Exception as e:
            _LOGGER.error(f"Error getting session start: {e}")
        return None

    def _get_session_end(self) -> str | None:
        """Get sleep session end time."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceEnd")
        except Exception as e:
            _LOGGER.error(f"Error getting session end: {e}")
        return None

    def _get_sleep_insight(self) -> str | None:
        """Get sleep insight from user profile."""
        try:
            if self._user.user_profile:
                notifications = self._user.user_profile.get("notifications", {})
                return notifications.get("sleepInsight")
        except Exception as e:
            _LOGGER.error(f"Error getting sleep insight: {e}")
        return None

    def _get_sleep_tracking_enabled(self) -> bool | None:
        """Get sleep tracking enabled status."""
        try:
            if self._user.user_profile:
                return self._user.user_profile.get("sleepTracking", {}).get("enabled", False)
        except Exception as e:
            _LOGGER.error(f"Error getting sleep tracking enabled: {e}")
        return None

    def _get_sleep_analytics_version(self) -> str | None:
        """Get sleep analytics version."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("analyticsVersion")
        except Exception as e:
            _LOGGER.error(f"Error getting sleep analytics version: {e}")
        return None

    def _get_sleep_quality_trend(self) -> float | None:
        """Get sleep quality trend."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepQualityScore", {}).get("total")
        except Exception as e:
            _LOGGER.error(f"Error getting sleep quality trend: {e}")
        return None

    def _get_sleep_efficiency_trend(self) -> float | None:
        """Get sleep efficiency trend."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepQualityScore", {}).get("sleepEfficiency", {}).get("current")
        except Exception as e:
            _LOGGER.error(f"Error getting sleep efficiency trend: {e}")
        return None

    def _get_sleep_consistency_trend(self) -> float | None:
        """Get sleep consistency trend."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepRoutineScore", {}).get("wakeupConsistency")
        except Exception as e:
            _LOGGER.error(f"Error getting sleep consistency trend: {e}")
        return None

    def _get_sleep_recovery_score(self) -> int | None:
        """Get sleep recovery score based on multiple metrics."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                quality_score = current_trend.get("sleepQualityScore", {}).get("total", 0)
                fitness_score = current_trend.get("sleepFitnessScore", {}).get("total", 0)
                routine_score = current_trend.get("sleepRoutineScore", {}).get("total", 0)
                # Calculate recovery score as average of all scores
                return (quality_score + fitness_score + routine_score) // 3
        except Exception as e:
            _LOGGER.error(f"Error getting sleep recovery score: {e}")
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

        # Add sleep-specific attributes
        if "breakdown" in self._sensor_type.lower():
            attrs["light_duration"] = self._get_sleep_breakdown_duration("light")
            attrs["deep_duration"] = self._get_sleep_breakdown_duration("deep")
            attrs["rem_duration"] = self._get_sleep_breakdown_duration("rem")
            attrs["awake_duration"] = self._get_sleep_breakdown_duration("awake")
        elif "score" in self._sensor_type.lower():
            attrs["sleep_quality_score"] = self._user.current_sleep_quality_score
            attrs["sleep_fitness_score"] = self._user.current_sleep_fitness_score
            attrs["sleep_routine_score"] = self._user.current_sleep_routine_score
            attrs["sleep_efficiency_score"] = self._get_sleep_efficiency_score()
        elif "stage" in self._sensor_type.lower():
            attrs["current_stage"] = self._user.current_sleep_stage
            attrs["last_stage"] = self._get_last_sleep_stage()
            attrs["processing_status"] = self._user.current_session_processing

        return attrs 