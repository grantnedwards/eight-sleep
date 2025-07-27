"""Biometric trends sensors for Eight Sleep."""

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
    PERCENTAGE,
    UnitOfFrequency,
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

# Biometric trend constants
TREND_PERIODS = {
    "hour": "Last Hour",
    "day": "Last Day",
    "week": "Last Week",
    "month": "Last Month",
}

BIOMETRIC_METRICS = {
    "heart_rate": {
        "name": "Heart Rate",
        "unit": "bpm",
        "device_class": SensorDeviceClass.FREQUENCY,
        "icon": "mdi:heart-pulse",
    },
    "respiratory_rate": {
        "name": "Respiratory Rate",
        "unit": "breaths/min",
        "device_class": SensorDeviceClass.FREQUENCY,
        "icon": "mdi:lungs",
    },
    "heart_rate_variability": {
        "name": "Heart Rate Variability",
        "unit": "ms",
        "device_class": None,
        "icon": "mdi:heart-multiple",
    },
    "sleep_efficiency": {
        "name": "Sleep Efficiency",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:sleep",
    },
    "sleep_duration": {
        "name": "Sleep Duration",
        "unit": "hours",
        "device_class": None,
        "icon": "mdi:clock-outline",
    },
    "deep_sleep_duration": {
        "name": "Deep Sleep Duration",
        "unit": "hours",
        "device_class": None,
        "icon": "mdi:bed-deep",
    },
    "rem_sleep_duration": {
        "name": "REM Sleep Duration",
        "unit": "hours",
        "device_class": None,
        "icon": "mdi:brain",
    },
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep biometric trends sensors."""
    config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    eight = config_entry_data.api

    entities = []

    # Create biometric trend sensors for each user
    for user in eight.users.values():
        for metric in BIOMETRIC_METRICS:
            for period in TREND_PERIODS:
                entities.append(
                    EightSleepBiometricTrendSensor(
                        entry,
                        config_entry_data.user_coordinator,
                        eight,
                        user,
                        metric,
                        period,
                    )
                )

    async_add_entities(entities)

class EightSleepBiometricTrendSensor(EightSleepBaseEntity, SensorEntity):
    """Biometric trend tracking sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        metric: str,
        period: str,
    ) -> None:
        """Initialize the biometric trend sensor."""
        super().__init__(
            entry, coordinator, eight, user, f"biometric_trend_{metric}_{period}"
        )

        self._metric = metric
        self._period = period
        self._metric_config = BIOMETRIC_METRICS[metric]

        # Set sensor properties
        self._attr_name = f"{self._metric_config['name']} Trend ({TREND_PERIODS[period]})"
        self._attr_icon = self._metric_config["icon"]
        self._attr_native_unit_of_measurement = self._metric_config["unit"]

        if self._metric_config["device_class"]:
            self._attr_device_class = self._metric_config["device_class"]

        # Set state class for numeric values
        if metric not in ["sleep_efficiency"]:
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | str | None:
        """Return the current trend value."""
        if not self.coordinator.data:
            return None

        try:
            trend_data = self._calculate_trend()
            if trend_data is None:
                return None

            if self._metric == "sleep_efficiency":
                return self._format_sleep_efficiency(trend_data)
            else:
                return round(trend_data, 2)

        except Exception as err:
            _LOGGER.error("Error calculating trend for %s: %s", self._attr_unique_id, err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None

        try:
            trend_data = self._calculate_trend()
            if trend_data is None:
                return None

            attributes = {
                "trend_period": self._period,
                "metric": self._metric,
                "last_updated": datetime.now().isoformat(),
            }

            # Add trend direction
            if hasattr(self, '_previous_value') and self._previous_value is not None:
                if trend_data > self._previous_value:
                    attributes["trend_direction"] = "increasing"
                elif trend_data < self._previous_value:
                    attributes["trend_direction"] = "decreasing"
                else:
                    attributes["trend_direction"] = "stable"

            self._previous_value = trend_data

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating attributes for %s: %s", self._attr_unique_id, err)
            return None

    def _calculate_trend(self) -> float | None:
        """Calculate the trend value for the specified metric and period."""
        if not self._user_obj or not hasattr(self._user_obj, 'sleep_data'):
            return None

        try:
            # Get the time range for the trend period
            end_time = datetime.now()
            if self._period == "hour":
                start_time = end_time - timedelta(hours=1)
            elif self._period == "day":
                start_time = end_time - timedelta(days=1)
            elif self._period == "week":
                start_time = end_time - timedelta(weeks=1)
            elif self._period == "month":
                start_time = end_time - timedelta(days=30)
            else:
                return None

            # Extract data points within the time range
            data_points = self._extract_data_points(start_time, end_time)

            if not data_points:
                return None

            # Calculate trend based on metric type
            if self._metric == "heart_rate":
                return self._calculate_average_trend(data_points, "heartRate")
            elif self._metric == "respiratory_rate":
                return self._calculate_average_trend(data_points, "respiratoryRate")
            elif self._metric == "heart_rate_variability":
                return self._calculate_average_trend(data_points, "hrv")
            elif self._metric == "sleep_efficiency":
                return self._calculate_sleep_efficiency_trend(data_points)
            elif self._metric == "sleep_duration":
                return self._calculate_sleep_duration_trend(data_points)
            elif self._metric == "deep_sleep_duration":
                return self._calculate_sleep_stage_duration_trend(data_points, "deep")
            elif self._metric == "rem_sleep_duration":
                return self._calculate_sleep_stage_duration_trend(data_points, "rem")
            else:
                return None

        except Exception as err:
            _LOGGER.error("Error calculating trend: %s", err)
            return None

    def _extract_data_points(self, start_time: datetime, end_time: datetime) -> list:
        """Extract data points within the specified time range."""
        data_points = []

        try:
            sleep_data = getattr(self._user_obj, 'sleep_data', {})
            if not sleep_data:
                return data_points

            # Extract relevant data points
            for session in sleep_data.get("sessions", []):
                session_start = self._parse_datetime(session.get("startTime"))
                session_end = self._parse_datetime(session.get("endTime"))

                if session_start and session_end:
                    # Check if session overlaps with our time range
                    if session_start <= end_time and session_end >= start_time:
                        data_points.append(session)

        except Exception as err:
            _LOGGER.error("Error extracting data points: %s", err)

        return data_points

    def _parse_datetime(self, datetime_str: str) -> datetime | None:
        """Parse datetime string to datetime object."""
        if not datetime_str:
            return None

        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except Exception:
            return None

    def _calculate_average_trend(self, data_points: list, key: str) -> float | None:
        """Calculate average trend for numeric metrics."""
        values = []

        for point in data_points:
            value = point.get(key)
            if value is not None and isinstance(value, (int, float)):
                values.append(float(value))

        if not values:
            return None

        return sum(values) / len(values)

    def _calculate_sleep_efficiency_trend(self, data_points: list) -> float | None:
        """Calculate sleep efficiency trend."""
        total_efficiency = 0
        valid_sessions = 0

        for point in data_points:
            efficiency = point.get("sleepEfficiency")
            if efficiency is not None and isinstance(efficiency, (int, float)):
                total_efficiency += float(efficiency)
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return total_efficiency / valid_sessions

    def _calculate_sleep_duration_trend(self, data_points: list) -> float | None:
        """Calculate sleep duration trend in hours."""
        total_duration = 0
        valid_sessions = 0

        for point in data_points:
            duration = point.get("sleepDuration")
            if duration is not None and isinstance(duration, (int, float)):
                # Convert to hours
                total_duration += float(duration) / 3600
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return total_duration / valid_sessions

    def _calculate_sleep_stage_duration_trend(self, data_points: list, stage: str) -> float | None:
        """Calculate sleep stage duration trend in hours."""
        total_duration = 0
        valid_sessions = 0

        for point in data_points:
            stage_data = point.get("sleepStages", {})
            duration = stage_data.get(f"{stage}Duration")
            if duration is not None and isinstance(duration, (int, float)):
                # Convert to hours
                total_duration += float(duration) / 3600
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return total_duration / valid_sessions

    def _format_sleep_efficiency(self, efficiency: float) -> str:
        """Format sleep efficiency as a percentage string."""
        if efficiency is None:
            return "Unknown"

        if efficiency >= 90:
            return "Excellent"
        elif efficiency >= 80:
            return "Good"
        elif efficiency >= 70:
            return "Fair"
        elif efficiency >= 60:
            return "Poor"
        else:
            return "Very Poor"
