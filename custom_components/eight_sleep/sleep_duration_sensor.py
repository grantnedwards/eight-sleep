"""Sleep duration tracking sensors for Eight Sleep."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import EightSleepBaseEntity, EightSleepConfigEntryData
from .const import DOMAIN
from .pyEight.eight import EightSleep
from .pyEight.user import EightUser

_LOGGER = logging.getLogger(__name__)

# Sleep duration tracking types
SLEEP_DURATION_TRACKING = {
    "total_sleep_duration": {
        "name": "Total Sleep Duration",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:clock-outline",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "deep_sleep_duration": {
        "name": "Deep Sleep Duration",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:bed-deep",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "rem_sleep_duration": {
        "name": "REM Sleep Duration",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:brain",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "light_sleep_duration": {
        "name": "Light Sleep Duration",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:bed",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "awake_duration": {
        "name": "Awake Duration",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:eye",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "time_in_bed": {
        "name": "Time in Bed",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:bed",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "sleep_latency": {
        "name": "Sleep Latency",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:timer-sand",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "sleep_onset_time": {
        "name": "Sleep Onset Time",
        "unit": None,
        "device_class": None,
        "icon": "mdi:clock-start",
        "state_class": None,
    },
    "sleep_end_time": {
        "name": "Sleep End Time",
        "unit": None,
        "device_class": None,
        "icon": "mdi:clock-end",
        "state_class": None,
    },
    "sleep_duration_category": {
        "name": "Sleep Duration Category",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:chart-bar",
        "state_class": None,
    },
}

# Sleep duration categories
SLEEP_DURATION_CATEGORIES = {
    "very_short": {"min": 0, "max": 4, "description": "Very Short (< 4 hours)"},
    "short": {"min": 4, "max": 6, "description": "Short (4-6 hours)"},
    "adequate": {"min": 6, "max": 8, "description": "Adequate (6-8 hours)"},
    "optimal": {"min": 8, "max": 9, "description": "Optimal (8-9 hours)"},
    "long": {"min": 9, "max": 10, "description": "Long (9-10 hours)"},
    "very_long": {"min": 10, "max": 24, "description": "Very Long (> 10 hours)"},
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep sleep duration sensors."""
    config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    eight = config_entry_data.api

    entities = []

    # Create sleep duration sensors for each user
    for user in eight.users.values():
        for tracking in SLEEP_DURATION_TRACKING:
            entities.append(
                EightSleepDurationSensor(
                    entry,
                    config_entry_data.user_coordinator,
                    eight,
                    user,
                    tracking,
                )
            )

        # Create comprehensive sleep duration sensor
        entities.append(
            EightSleepComprehensiveDurationSensor(
                entry,
                config_entry_data.user_coordinator,
                eight,
                user,
            )
        )

    async_add_entities(entities)

class EightSleepDurationSensor(EightSleepBaseEntity, SensorEntity):
    """Individual sleep duration tracking sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        tracking: str,
    ) -> None:
        """Initialize the sleep duration sensor."""
        super().__init__(
            entry, coordinator, eight, user, f"sleep_duration_{tracking}"
        )

        self._tracking = tracking
        self._tracking_config = SLEEP_DURATION_TRACKING[tracking]

        # Set sensor properties
        self._attr_name = self._tracking_config["name"]
        self._attr_icon = self._tracking_config["icon"]
        self._attr_native_unit_of_measurement = self._tracking_config["unit"]

        if self._tracking_config["device_class"]:
            self._attr_device_class = self._tracking_config["device_class"]

        if self._tracking_config["state_class"]:
            self._attr_state_class = self._tracking_config["state_class"]

    @property
    def native_value(self) -> float | str | None:
        """Return the current sleep duration value."""
        if not self.coordinator.data:
            return None

        try:
            duration_data = self._get_sleep_duration_data()
            if duration_data is None:
                return None

            value = duration_data.get(self._tracking)
            if value is None:
                return None

            if self._tracking in ["sleep_onset_time", "sleep_end_time"]:
                return self._format_time(value)
            elif self._tracking == "sleep_duration_category":
                return self._get_duration_category(value)
            else:
                return round(float(value), 2)

        except Exception as err:
            _LOGGER.error("Error getting sleep duration data for %s: %s", self._attr_unique_id, err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None

        try:
            duration_data = self._get_sleep_duration_data()
            if duration_data is None:
                return None

            attributes = {
                "tracking": self._tracking,
                "last_updated": datetime.now().isoformat(),
            }

            # Add duration-specific attributes
            if self._tracking == "total_sleep_duration":
                value = duration_data.get(self._tracking)
                if value is not None:
                    attributes["duration_category"] = self._get_duration_category(value)
                    attributes["is_optimal_duration"] = 7 <= value <= 9
                    attributes["sleep_debt"] = self._calculate_sleep_debt(value)

            elif self._tracking == "deep_sleep_duration":
                value = duration_data.get(self._tracking)
                if value is not None:
                    attributes["deep_sleep_percentage"] = self._calculate_percentage(value, duration_data.get("total_sleep_duration"))
                    attributes["deep_sleep_quality"] = self._assess_deep_sleep_quality(value)

            elif self._tracking == "rem_sleep_duration":
                value = duration_data.get(self._tracking)
                if value is not None:
                    attributes["rem_sleep_percentage"] = self._calculate_percentage(value, duration_data.get("total_sleep_duration"))
                    attributes["rem_sleep_quality"] = self._assess_rem_sleep_quality(value)

            elif self._tracking == "sleep_latency":
                value = duration_data.get(self._tracking)
                if value is not None:
                    attributes["latency_category"] = self._get_latency_category(value)
                    attributes["is_optimal_latency"] = value <= 20

            elif self._tracking in ["sleep_onset_time", "sleep_end_time"]:
                value = duration_data.get(self._tracking)
                if value is not None:
                    attributes["time_formatted"] = self._format_time(value)
                    attributes["hour_of_day"] = self._extract_hour(value)

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating attributes for %s: %s", self._attr_unique_id, err)
            return None

    def _get_sleep_duration_data(self) -> dict | None:
        """Get sleep duration data from the user."""
        if not self._user_obj or not hasattr(self._user_obj, 'sleep_data'):
            return None

        try:
            sleep_data = getattr(self._user_obj, 'sleep_data', {})
            sessions = sleep_data.get("sessions", [])

            if not sessions:
                return None

            # Get the most recent session
            latest_session = sessions[0]
            return self._extract_duration_data(latest_session)

        except Exception as err:
            _LOGGER.error("Error getting sleep duration data: %s", err)
            return None

    def _extract_duration_data(self, session: dict) -> dict:
        """Extract duration data from a sleep session."""
        try:
            # Extract basic duration data
            total_sleep_duration = session.get("sleepDuration", 0) / 3600  # Convert to hours
            time_in_bed = session.get("timeInBed", 0) / 3600  # Convert to hours
            sleep_latency = session.get("sleepLatency", 0) / 60  # Convert to minutes

            # Extract sleep stage durations
            sleep_stages = session.get("sleepStages", {})
            deep_sleep_duration = sleep_stages.get("deepDuration", 0) / 3600  # Convert to hours
            rem_sleep_duration = sleep_stages.get("remDuration", 0) / 3600  # Convert to hours
            light_sleep_duration = sleep_stages.get("lightDuration", 0) / 3600  # Convert to hours
            awake_duration = sleep_stages.get("awakeDuration", 0) / 3600  # Convert to hours

            # Extract timing data
            sleep_onset_time = session.get("startTime")
            sleep_end_time = session.get("endTime")

            return {
                "total_sleep_duration": total_sleep_duration,
                "deep_sleep_duration": deep_sleep_duration,
                "rem_sleep_duration": rem_sleep_duration,
                "light_sleep_duration": light_sleep_duration,
                "awake_duration": awake_duration,
                "time_in_bed": time_in_bed,
                "sleep_latency": sleep_latency,
                "sleep_onset_time": sleep_onset_time,
                "sleep_end_time": sleep_end_time,
                "sleep_duration_category": total_sleep_duration,
            }

        except Exception as err:
            _LOGGER.error("Error extracting duration data: %s", err)
            return None

    def _format_time(self, time_str: str) -> str:
        """Format time string for display."""
        if not time_str:
            return "Unknown"

        try:
            # Parse ISO format time
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.strftime("%H:%M")
        except Exception:
            return "Unknown"

    def _get_duration_category(self, duration: float) -> str:
        """Get sleep duration category."""
        for category, config in SLEEP_DURATION_CATEGORIES.items():
            if config["min"] <= duration < config["max"]:
                return config["description"]
        return "Unknown"

    def _calculate_sleep_debt(self, duration: float) -> float:
        """Calculate sleep debt (optimal is 8 hours)."""
        optimal_duration = 8.0
        return max(0, optimal_duration - duration)

    def _calculate_percentage(self, part: float, total: float) -> float:
        """Calculate percentage of part relative to total."""
        if total <= 0:
            return 0.0
        return (part / total) * 100

    def _assess_deep_sleep_quality(self, duration: float) -> str:
        """Assess deep sleep quality."""
        if duration >= 1.5:
            return "Excellent"
        elif duration >= 1.0:
            return "Good"
        elif duration >= 0.5:
            return "Fair"
        else:
            return "Poor"

    def _assess_rem_sleep_quality(self, duration: float) -> str:
        """Assess REM sleep quality."""
        if duration >= 2.0:
            return "Excellent"
        elif duration >= 1.5:
            return "Good"
        elif duration >= 1.0:
            return "Fair"
        else:
            return "Poor"

    def _get_latency_category(self, latency: float) -> str:
        """Get sleep latency category."""
        if latency <= 10:
            return "Excellent"
        elif latency <= 20:
            return "Good"
        elif latency <= 30:
            return "Fair"
        elif latency <= 45:
            return "Poor"
        else:
            return "Very Poor"

    def _extract_hour(self, time_str: str) -> int:
        """Extract hour from time string."""
        if not time_str:
            return 0

        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.hour
        except Exception:
            return 0

class EightSleepComprehensiveDurationSensor(EightSleepBaseEntity, SensorEntity):
    """Comprehensive sleep duration tracking sensor."""

    _attr_has_entity_name = True
    _attr_name = "Sleep Duration Analysis"
    _attr_icon = "mdi:chart-timeline-variant"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
    ) -> None:
        """Initialize the comprehensive sleep duration sensor."""
        super().__init__(
            entry, coordinator, eight, user, "sleep_duration_comprehensive"
        )

    @property
    def native_value(self) -> str | None:
        """Return the overall sleep duration assessment."""
        if not self.coordinator.data:
            return None

        try:
            duration_data = self._get_comprehensive_duration_data()
            if duration_data is None:
                return "Unknown"

            total_duration = duration_data.get("total_sleep_duration", 0)
            return self._get_duration_assessment(total_duration)

        except Exception as err:
            _LOGGER.error("Error getting comprehensive duration data: %s", err)
            return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return detailed duration attributes."""
        if not self.coordinator.data:
            return None

        try:
            duration_data = self._get_comprehensive_duration_data()
            if duration_data is None:
                return None

            attributes = {
                "last_updated": datetime.now().isoformat(),
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            }

            # Add all duration metrics
            for tracking, config in SLEEP_DURATION_TRACKING.items():
                value = duration_data.get(tracking)
                if value is not None:
                    attributes[f"{tracking}_value"] = value
                    if tracking == "total_sleep_duration":
                        attributes[f"{tracking}_category"] = self._get_duration_category(value)

            # Add recommendations
            recommendations = self._get_duration_recommendations(duration_data)
            if recommendations:
                attributes["recommendations"] = recommendations

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating comprehensive attributes: %s", err)
            return None

    def _get_comprehensive_duration_data(self) -> dict | None:
        """Get comprehensive duration data."""
        if not self._user_obj or not hasattr(self._user_obj, 'sleep_data'):
            return None

        try:
            sleep_data = getattr(self._user_obj, 'sleep_data', {})
            sessions = sleep_data.get("sessions", [])

            if not sessions:
                return None

            # Get the most recent session
            latest_session = sessions[0]
            return self._extract_duration_data(latest_session)

        except Exception as err:
            _LOGGER.error("Error getting comprehensive duration data: %s", err)
            return None

    def _extract_duration_data(self, session: dict) -> dict:
        """Extract duration data from a sleep session."""
        try:
            # Extract basic duration data
            total_sleep_duration = session.get("sleepDuration", 0) / 3600  # Convert to hours
            time_in_bed = session.get("timeInBed", 0) / 3600  # Convert to hours
            sleep_latency = session.get("sleepLatency", 0) / 60  # Convert to minutes

            # Extract sleep stage durations
            sleep_stages = session.get("sleepStages", {})
            deep_sleep_duration = sleep_stages.get("deepDuration", 0) / 3600  # Convert to hours
            rem_sleep_duration = sleep_stages.get("remDuration", 0) / 3600  # Convert to hours
            light_sleep_duration = sleep_stages.get("lightDuration", 0) / 3600  # Convert to hours
            awake_duration = sleep_stages.get("awakeDuration", 0) / 3600  # Convert to hours

            # Extract timing data
            sleep_onset_time = session.get("startTime")
            sleep_end_time = session.get("endTime")

            return {
                "total_sleep_duration": total_sleep_duration,
                "deep_sleep_duration": deep_sleep_duration,
                "rem_sleep_duration": rem_sleep_duration,
                "light_sleep_duration": light_sleep_duration,
                "awake_duration": awake_duration,
                "time_in_bed": time_in_bed,
                "sleep_latency": sleep_latency,
                "sleep_onset_time": sleep_onset_time,
                "sleep_end_time": sleep_end_time,
                "sleep_duration_category": total_sleep_duration,
            }

        except Exception as err:
            _LOGGER.error("Error extracting duration data: %s", err)
            return None

    def _get_duration_assessment(self, duration: float) -> str:
        """Get overall duration assessment."""
        if duration >= 8 and duration <= 9:
            return "Optimal Sleep Duration"
        elif duration >= 7 and duration <= 10:
            return "Good Sleep Duration"
        elif duration >= 6 and duration <= 11:
            return "Adequate Sleep Duration"
        elif duration < 6:
            return "Insufficient Sleep Duration"
        else:
            return "Excessive Sleep Duration"

    def _get_duration_category(self, duration: float) -> str:
        """Get sleep duration category."""
        for category, config in SLEEP_DURATION_CATEGORIES.items():
            if config["min"] <= duration < config["max"]:
                return config["description"]
        return "Unknown"

    def _get_duration_recommendations(self, duration_data: dict) -> list[str]:
        """Get sleep duration recommendations based on current metrics."""
        recommendations = []

        try:
            total_duration = duration_data.get("total_sleep_duration", 0)
            deep_sleep_duration = duration_data.get("deep_sleep_duration", 0)
            rem_sleep_duration = duration_data.get("rem_sleep_duration", 0)
            sleep_latency = duration_data.get("sleep_latency", 0)

            if total_duration < 6:
                recommendations.append("Increase sleep duration to at least 6-8 hours")
            elif total_duration > 10:
                recommendations.append("Consider reducing sleep duration to 7-9 hours")

            if deep_sleep_duration < 1.0:
                recommendations.append("Focus on improving deep sleep quality")

            if rem_sleep_duration < 1.5:
                recommendations.append("Work on increasing REM sleep duration")

            if sleep_latency > 30:
                recommendations.append("Reduce sleep latency through better sleep hygiene")

            if not recommendations:
                recommendations.append("Maintain current sleep duration patterns")

        except Exception as err:
            _LOGGER.error("Error generating duration recommendations: %s", err)

        return recommendations
