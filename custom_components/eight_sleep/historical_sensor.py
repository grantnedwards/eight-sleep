"""Historical data sensors for Eight Sleep."""

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

# Historical data periods
HISTORICAL_PERIODS = {
    "week": "Last Week",
    "month": "Last Month",
    "quarter": "Last Quarter",
    "year": "Last Year",
}

# Historical metrics
HISTORICAL_METRICS = {
    "average_sleep_duration": {
        "name": "Average Sleep Duration",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:clock-outline",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "average_sleep_efficiency": {
        "name": "Average Sleep Efficiency",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:percent",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "average_heart_rate": {
        "name": "Average Heart Rate",
        "unit": "bpm",
        "device_class": SensorDeviceClass.FREQUENCY,
        "icon": "mdi:heart-pulse",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "average_respiratory_rate": {
        "name": "Average Respiratory Rate",
        "unit": "breaths/min",
        "device_class": SensorDeviceClass.FREQUENCY,
        "icon": "mdi:lungs",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "total_sleep_sessions": {
        "name": "Total Sleep Sessions",
        "unit": "sessions",
        "device_class": None,
        "icon": "mdi:bed",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "best_sleep_score": {
        "name": "Best Sleep Score",
        "unit": None,
        "device_class": None,
        "icon": "mdi:star",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "worst_sleep_score": {
        "name": "Worst Sleep Score",
        "unit": None,
        "device_class": None,
        "icon": "mdi:star-outline",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "sleep_consistency": {
        "name": "Sleep Consistency",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:calendar-clock",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "deep_sleep_average": {
        "name": "Average Deep Sleep",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:bed-deep",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "rem_sleep_average": {
        "name": "Average REM Sleep",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:brain",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "light_sleep_average": {
        "name": "Average Light Sleep",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:bed",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "awake_time_average": {
        "name": "Average Awake Time",
        "unit": UnitOfTime.HOURS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:eye",
        "state_class": SensorStateClass.MEASUREMENT,
    },
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep historical sensors."""
    config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    eight = config_entry_data.api

    entities = []

    # Create historical sensors for each user
    for user in eight.users.values():
        for metric in HISTORICAL_METRICS:
            for period in HISTORICAL_PERIODS:
                entities.append(
                    EightSleepHistoricalSensor(
                        entry,
                        config_entry_data.user_coordinator,
                        eight,
                        user,
                        metric,
                        period,
                    )
                )

        # Create comprehensive historical sensor
        entities.append(
            EightSleepComprehensiveHistoricalSensor(
                entry,
                config_entry_data.user_coordinator,
                eight,
                user,
            )
        )

    async_add_entities(entities)

class EightSleepHistoricalSensor(EightSleepBaseEntity, SensorEntity):
    """Individual historical data sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        metric: str,
        period: str,
    ) -> None:
        """Initialize the historical sensor."""
        super().__init__(
            entry, coordinator, eight, user, f"historical_{metric}_{period}"
        )

        self._metric = metric
        self._period = period
        self._metric_config = HISTORICAL_METRICS[metric]

        # Set sensor properties
        self._attr_name = f"{self._metric_config['name']} ({HISTORICAL_PERIODS[period]})"
        self._attr_icon = self._metric_config["icon"]
        self._attr_native_unit_of_measurement = self._metric_config["unit"]

        if self._metric_config["device_class"]:
            self._attr_device_class = self._metric_config["device_class"]

        if self._metric_config["state_class"]:
            self._attr_state_class = self._metric_config["state_class"]

    @property
    def native_value(self) -> float | str | None:
        """Return the current historical value."""
        if not self.coordinator.data:
            return None

        try:
            historical_data = self._calculate_historical_data()
            if historical_data is None:
                return None

            value = historical_data.get(self._metric)
            if value is None:
                return None

            if self._metric == "average_sleep_efficiency":
                return self._format_sleep_efficiency(value)
            elif self._metric == "sleep_consistency":
                return self._format_consistency(value)
            else:
                return round(float(value), 2)

        except Exception as err:
            _LOGGER.error("Error calculating historical data for %s: %s", self._attr_unique_id, err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None

        try:
            historical_data = self._calculate_historical_data()
            if historical_data is None:
                return None

            attributes = {
                "metric": self._metric,
                "period": self._period,
                "last_updated": datetime.now().isoformat(),
            }

            # Add trend information
            if hasattr(self, '_previous_value') and self._previous_value is not None:
                current_value = historical_data.get(self._metric)
                if current_value is not None:
                    if current_value > self._previous_value:
                        attributes["trend"] = "improving"
                    elif current_value < self._previous_value:
                        attributes["trend"] = "declining"
                    else:
                        attributes["trend"] = "stable"

            self._previous_value = historical_data.get(self._metric)

            # Add period-specific attributes
            attributes["period_start"] = self._get_period_start().isoformat()
            attributes["period_end"] = self._get_period_end().isoformat()
            attributes["data_points"] = historical_data.get("data_points", 0)

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating attributes for %s: %s", self._attr_unique_id, err)
            return None

    def _calculate_historical_data(self) -> dict | None:
        """Calculate historical data for the specified metric and period."""
        if not self._user_obj or not hasattr(self._user_obj, 'sleep_data'):
            return None

        try:
            # Get the time range for the historical period
            end_time = datetime.now()
            start_time = self._get_period_start()

            # Extract data points within the time range
            data_points = self._extract_historical_data_points(start_time, end_time)

            if not data_points:
                return None

            # Calculate historical metrics based on metric type
            if self._metric == "average_sleep_duration":
                return self._calculate_average_sleep_duration(data_points)
            elif self._metric == "average_sleep_efficiency":
                return self._calculate_average_sleep_efficiency(data_points)
            elif self._metric == "average_heart_rate":
                return self._calculate_average_heart_rate(data_points)
            elif self._metric == "average_respiratory_rate":
                return self._calculate_average_respiratory_rate(data_points)
            elif self._metric == "total_sleep_sessions":
                return self._calculate_total_sleep_sessions(data_points)
            elif self._metric == "best_sleep_score":
                return self._calculate_best_sleep_score(data_points)
            elif self._metric == "worst_sleep_score":
                return self._calculate_worst_sleep_score(data_points)
            elif self._metric == "sleep_consistency":
                return self._calculate_sleep_consistency(data_points)
            elif self._metric == "deep_sleep_average":
                return self._calculate_deep_sleep_average(data_points)
            elif self._metric == "rem_sleep_average":
                return self._calculate_rem_sleep_average(data_points)
            elif self._metric == "light_sleep_average":
                return self._calculate_light_sleep_average(data_points)
            elif self._metric == "awake_time_average":
                return self._calculate_awake_time_average(data_points)
            else:
                return None

        except Exception as err:
            _LOGGER.error("Error calculating historical data: %s", err)
            return None

    def _get_period_start(self) -> datetime:
        """Get the start time for the historical period."""
        end_time = datetime.now()

        if self._period == "week":
            return end_time - timedelta(weeks=1)
        elif self._period == "month":
            return end_time - timedelta(days=30)
        elif self._period == "quarter":
            return end_time - timedelta(days=90)
        elif self._period == "year":
            return end_time - timedelta(days=365)
        else:
            return end_time - timedelta(days=7)

    def _get_period_end(self) -> datetime:
        """Get the end time for the historical period."""
        return datetime.now()

    def _extract_historical_data_points(self, start_time: datetime, end_time: datetime) -> list:
        """Extract historical data points within the specified time range."""
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
                    # Check if session is within our time range
                    if session_start >= start_time and session_end <= end_time:
                        data_points.append(session)

        except Exception as err:
            _LOGGER.error("Error extracting historical data points: %s", err)

        return data_points

    def _parse_datetime(self, datetime_str: str) -> datetime | None:
        """Parse datetime string to datetime object."""
        if not datetime_str:
            return None

        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except Exception:
            return None

    def _calculate_average_sleep_duration(self, data_points: list) -> dict:
        """Calculate average sleep duration."""
        total_duration = 0
        valid_sessions = 0

        for point in data_points:
            duration = point.get("sleepDuration")
            if duration is not None and isinstance(duration, (int, float)):
                total_duration += float(duration) / 3600  # Convert to hours
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return {
            "average_sleep_duration": total_duration / valid_sessions,
            "data_points": valid_sessions,
        }

    def _calculate_average_sleep_efficiency(self, data_points: list) -> dict:
        """Calculate average sleep efficiency."""
        total_efficiency = 0
        valid_sessions = 0

        for point in data_points:
            efficiency = point.get("sleepEfficiency")
            if efficiency is not None and isinstance(efficiency, (int, float)):
                total_efficiency += float(efficiency)
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return {
            "average_sleep_efficiency": total_efficiency / valid_sessions,
            "data_points": valid_sessions,
        }

    def _calculate_average_heart_rate(self, data_points: list) -> dict:
        """Calculate average heart rate."""
        total_heart_rate = 0
        valid_sessions = 0

        for point in data_points:
            heart_rate = point.get("heartRate")
            if heart_rate is not None and isinstance(heart_rate, (int, float)):
                total_heart_rate += float(heart_rate)
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return {
            "average_heart_rate": total_heart_rate / valid_sessions,
            "data_points": valid_sessions,
        }

    def _calculate_average_respiratory_rate(self, data_points: list) -> dict:
        """Calculate average respiratory rate."""
        total_respiratory_rate = 0
        valid_sessions = 0

        for point in data_points:
            respiratory_rate = point.get("respiratoryRate")
            if respiratory_rate is not None and isinstance(respiratory_rate, (int, float)):
                total_respiratory_rate += float(respiratory_rate)
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return {
            "average_respiratory_rate": total_respiratory_rate / valid_sessions,
            "data_points": valid_sessions,
        }

    def _calculate_total_sleep_sessions(self, data_points: list) -> dict:
        """Calculate total sleep sessions."""
        return {
            "total_sleep_sessions": len(data_points),
            "data_points": len(data_points),
        }

    def _calculate_best_sleep_score(self, data_points: list) -> dict:
        """Calculate best sleep score."""
        best_score = None

        for point in data_points:
            score = point.get("sleepScore")
            if score is not None and isinstance(score, (int, float)):
                if best_score is None or score > best_score:
                    best_score = float(score)

        return {
            "best_sleep_score": best_score,
            "data_points": len(data_points),
        }

    def _calculate_worst_sleep_score(self, data_points: list) -> dict:
        """Calculate worst sleep score."""
        worst_score = None

        for point in data_points:
            score = point.get("sleepScore")
            if score is not None and isinstance(score, (int, float)):
                if worst_score is None or score < worst_score:
                    worst_score = float(score)

        return {
            "worst_sleep_score": worst_score,
            "data_points": len(data_points),
        }

    def _calculate_sleep_consistency(self, data_points: list) -> dict:
        """Calculate sleep consistency."""
        if len(data_points) < 2:
            return None

        # Calculate consistency based on sleep duration variance
        durations = []
        for point in data_points:
            duration = point.get("sleepDuration")
            if duration is not None and isinstance(duration, (int, float)):
                durations.append(float(duration) / 3600)  # Convert to hours

        if len(durations) < 2:
            return None

        # Calculate coefficient of variation (lower is more consistent)
        mean_duration = sum(durations) / len(durations)
        variance = sum((d - mean_duration) ** 2 for d in durations) / len(durations)
        std_dev = variance ** 0.5
        cv = (std_dev / mean_duration) * 100 if mean_duration > 0 else 0

        # Convert to consistency percentage (lower CV = higher consistency)
        consistency = max(0, 100 - cv)

        return {
            "sleep_consistency": consistency,
            "data_points": len(data_points),
        }

    def _calculate_deep_sleep_average(self, data_points: list) -> dict:
        """Calculate average deep sleep duration."""
        total_deep_sleep = 0
        valid_sessions = 0

        for point in data_points:
            sleep_stages = point.get("sleepStages", {})
            deep_sleep = sleep_stages.get("deepDuration")
            if deep_sleep is not None and isinstance(deep_sleep, (int, float)):
                total_deep_sleep += float(deep_sleep) / 3600  # Convert to hours
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return {
            "deep_sleep_average": total_deep_sleep / valid_sessions,
            "data_points": valid_sessions,
        }

    def _calculate_rem_sleep_average(self, data_points: list) -> dict:
        """Calculate average REM sleep duration."""
        total_rem_sleep = 0
        valid_sessions = 0

        for point in data_points:
            sleep_stages = point.get("sleepStages", {})
            rem_sleep = sleep_stages.get("remDuration")
            if rem_sleep is not None and isinstance(rem_sleep, (int, float)):
                total_rem_sleep += float(rem_sleep) / 3600  # Convert to hours
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return {
            "rem_sleep_average": total_rem_sleep / valid_sessions,
            "data_points": valid_sessions,
        }

    def _calculate_light_sleep_average(self, data_points: list) -> dict:
        """Calculate average light sleep duration."""
        total_light_sleep = 0
        valid_sessions = 0

        for point in data_points:
            sleep_stages = point.get("sleepStages", {})
            light_sleep = sleep_stages.get("lightDuration")
            if light_sleep is not None and isinstance(light_sleep, (int, float)):
                total_light_sleep += float(light_sleep) / 3600  # Convert to hours
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return {
            "light_sleep_average": total_light_sleep / valid_sessions,
            "data_points": valid_sessions,
        }

    def _calculate_awake_time_average(self, data_points: list) -> dict:
        """Calculate average awake time during sleep."""
        total_awake_time = 0
        valid_sessions = 0

        for point in data_points:
            sleep_stages = point.get("sleepStages", {})
            awake_time = sleep_stages.get("awakeDuration")
            if awake_time is not None and isinstance(awake_time, (int, float)):
                total_awake_time += float(awake_time) / 3600  # Convert to hours
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return {
            "awake_time_average": total_awake_time / valid_sessions,
            "data_points": valid_sessions,
        }

    def _format_sleep_efficiency(self, efficiency: float) -> str:
        """Format sleep efficiency."""
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

    def _format_consistency(self, consistency: float) -> str:
        """Format sleep consistency."""
        if consistency >= 90:
            return "Excellent"
        elif consistency >= 80:
            return "Good"
        elif consistency >= 70:
            return "Fair"
        elif consistency >= 60:
            return "Poor"
        else:
            return "Very Poor"

class EightSleepComprehensiveHistoricalSensor(EightSleepBaseEntity, SensorEntity):
    """Comprehensive historical data sensor."""

    _attr_has_entity_name = True
    _attr_name = "Sleep History Analysis"
    _attr_icon = "mdi:chart-line"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
    ) -> None:
        """Initialize the comprehensive historical sensor."""
        super().__init__(
            entry, coordinator, eight, user, "historical_comprehensive"
        )

    @property
    def native_value(self) -> str | None:
        """Return the overall historical assessment."""
        if not self.coordinator.data:
            return None

        try:
            historical_data = self._get_comprehensive_historical_data()
            if historical_data is None:
                return "Unknown"

            return self._get_historical_assessment(historical_data)

        except Exception as err:
            _LOGGER.error("Error getting comprehensive historical data: %s", err)
            return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return detailed historical attributes."""
        if not self.coordinator.data:
            return None

        try:
            historical_data = self._get_comprehensive_historical_data()
            if historical_data is None:
                return None

            attributes = {
                "last_updated": datetime.now().isoformat(),
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            }

            # Add all historical metrics
            for metric, config in HISTORICAL_METRICS.items():
                value = historical_data.get(metric)
                if value is not None:
                    attributes[f"{metric}_value"] = value

            # Add recommendations
            recommendations = self._get_historical_recommendations(historical_data)
            if recommendations:
                attributes["recommendations"] = recommendations

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating comprehensive attributes: %s", err)
            return None

    def _get_comprehensive_historical_data(self) -> dict | None:
        """Get comprehensive historical data."""
        if not self._user_obj or not hasattr(self._user_obj, 'sleep_data'):
            return None

        try:
            # Get last 30 days of data for comprehensive analysis
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)

            data_points = self._extract_historical_data_points(start_time, end_time)

            if not data_points:
                return None

            # Calculate comprehensive metrics
            return {
                "average_sleep_duration": self._calculate_average_sleep_duration(data_points),
                "average_sleep_efficiency": self._calculate_average_sleep_efficiency(data_points),
                "total_sleep_sessions": len(data_points),
                "sleep_consistency": self._calculate_sleep_consistency(data_points),
                "deep_sleep_average": self._calculate_deep_sleep_average(data_points),
                "rem_sleep_average": self._calculate_rem_sleep_average(data_points),
                "light_sleep_average": self._calculate_light_sleep_average(data_points),
                "awake_time_average": self._calculate_awake_time_average(data_points),
            }

        except Exception as err:
            _LOGGER.error("Error getting comprehensive historical data: %s", err)
            return None

    def _extract_historical_data_points(self, start_time: datetime, end_time: datetime) -> list:
        """Extract historical data points within the specified time range."""
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
                    # Check if session is within our time range
                    if session_start >= start_time and session_end <= end_time:
                        data_points.append(session)

        except Exception as err:
            _LOGGER.error("Error extracting historical data points: %s", err)

        return data_points

    def _parse_datetime(self, datetime_str: str) -> datetime | None:
        """Parse datetime string to datetime object."""
        if not datetime_str:
            return None

        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except Exception:
            return None

    def _calculate_average_sleep_duration(self, data_points: list) -> float | None:
        """Calculate average sleep duration."""
        total_duration = 0
        valid_sessions = 0

        for point in data_points:
            duration = point.get("sleepDuration")
            if duration is not None and isinstance(duration, (int, float)):
                total_duration += float(duration) / 3600  # Convert to hours
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return total_duration / valid_sessions

    def _calculate_average_sleep_efficiency(self, data_points: list) -> float | None:
        """Calculate average sleep efficiency."""
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

    def _calculate_sleep_consistency(self, data_points: list) -> float | None:
        """Calculate sleep consistency."""
        if len(data_points) < 2:
            return None

        # Calculate consistency based on sleep duration variance
        durations = []
        for point in data_points:
            duration = point.get("sleepDuration")
            if duration is not None and isinstance(duration, (int, float)):
                durations.append(float(duration) / 3600)  # Convert to hours

        if len(durations) < 2:
            return None

        # Calculate coefficient of variation (lower is more consistent)
        mean_duration = sum(durations) / len(durations)
        variance = sum((d - mean_duration) ** 2 for d in durations) / len(durations)
        std_dev = variance ** 0.5
        cv = (std_dev / mean_duration) * 100 if mean_duration > 0 else 0

        # Convert to consistency percentage (lower CV = higher consistency)
        return max(0, 100 - cv)

    def _calculate_deep_sleep_average(self, data_points: list) -> float | None:
        """Calculate average deep sleep duration."""
        total_deep_sleep = 0
        valid_sessions = 0

        for point in data_points:
            sleep_stages = point.get("sleepStages", {})
            deep_sleep = sleep_stages.get("deepDuration")
            if deep_sleep is not None and isinstance(deep_sleep, (int, float)):
                total_deep_sleep += float(deep_sleep) / 3600  # Convert to hours
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return total_deep_sleep / valid_sessions

    def _calculate_rem_sleep_average(self, data_points: list) -> float | None:
        """Calculate average REM sleep duration."""
        total_rem_sleep = 0
        valid_sessions = 0

        for point in data_points:
            sleep_stages = point.get("sleepStages", {})
            rem_sleep = sleep_stages.get("remDuration")
            if rem_sleep is not None and isinstance(rem_sleep, (int, float)):
                total_rem_sleep += float(rem_sleep) / 3600  # Convert to hours
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return total_rem_sleep / valid_sessions

    def _calculate_light_sleep_average(self, data_points: list) -> float | None:
        """Calculate average light sleep duration."""
        total_light_sleep = 0
        valid_sessions = 0

        for point in data_points:
            sleep_stages = point.get("sleepStages", {})
            light_sleep = sleep_stages.get("lightDuration")
            if light_sleep is not None and isinstance(light_sleep, (int, float)):
                total_light_sleep += float(light_sleep) / 3600  # Convert to hours
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return total_light_sleep / valid_sessions

    def _calculate_awake_time_average(self, data_points: list) -> float | None:
        """Calculate average awake time during sleep."""
        total_awake_time = 0
        valid_sessions = 0

        for point in data_points:
            sleep_stages = point.get("sleepStages", {})
            awake_time = sleep_stages.get("awakeDuration")
            if awake_time is not None and isinstance(awake_time, (int, float)):
                total_awake_time += float(awake_time) / 3600  # Convert to hours
                valid_sessions += 1

        if valid_sessions == 0:
            return None

        return total_awake_time / valid_sessions

    def _get_historical_assessment(self, historical_data: dict) -> str:
        """Get overall historical assessment."""
        # Simple assessment based on available data
        issues = []

        sleep_duration = historical_data.get("average_sleep_duration")
        if sleep_duration is not None:
            if sleep_duration < 6:
                issues.append("short_sleep")
            elif sleep_duration > 9:
                issues.append("long_sleep")

        sleep_efficiency = historical_data.get("average_sleep_efficiency")
        if sleep_efficiency is not None and sleep_efficiency < 80:
            issues.append("low_efficiency")

        sleep_consistency = historical_data.get("sleep_consistency")
        if sleep_consistency is not None and sleep_consistency < 70:
            issues.append("inconsistent")

        if not issues:
            return "Excellent Sleep Patterns"
        elif len(issues) == 1:
            return f"Good Sleep Patterns ({issues[0].replace('_', ' ').title()} needs attention)"
        else:
            return f"Sleep Patterns Need Improvement ({len(issues)} areas)"

    def _get_historical_recommendations(self, historical_data: dict) -> list[str]:
        """Get historical sleep recommendations based on patterns."""
        recommendations = []

        try:
            sleep_duration = historical_data.get("average_sleep_duration")
            sleep_efficiency = historical_data.get("average_sleep_efficiency")
            sleep_consistency = historical_data.get("sleep_consistency")

            if sleep_duration is not None:
                if sleep_duration < 6:
                    recommendations.append("Consider increasing sleep duration")
                elif sleep_duration > 9:
                    recommendations.append("Consider reducing sleep duration")

            if sleep_efficiency is not None and sleep_efficiency < 80:
                recommendations.append("Focus on improving sleep efficiency")

            if sleep_consistency is not None and sleep_consistency < 70:
                recommendations.append("Work on maintaining consistent sleep schedule")

            if not recommendations:
                recommendations.append("Maintain current sleep habits")

        except Exception as err:
            _LOGGER.error("Error generating historical recommendations: %s", err)

        return recommendations
