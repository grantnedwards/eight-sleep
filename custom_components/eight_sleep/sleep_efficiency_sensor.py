"""Sleep efficiency calculation sensors for Eight Sleep."""

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

# Sleep efficiency calculation types
SLEEP_EFFICIENCY_CALCULATIONS = {
    "overall_efficiency": {
        "name": "Overall Sleep Efficiency",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:percent",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "time_in_bed_efficiency": {
        "name": "Time in Bed Efficiency",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:bed",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "sleep_latency_efficiency": {
        "name": "Sleep Latency Efficiency",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:timer-sand",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "wake_efficiency": {
        "name": "Wake Efficiency",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:eye",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "restlessness_efficiency": {
        "name": "Restlessness Efficiency",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:bed",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "sleep_continuity": {
        "name": "Sleep Continuity",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:chart-line",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "sleep_consolidation": {
        "name": "Sleep Consolidation",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:chart-areaspline",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "sleep_quality_score": {
        "name": "Sleep Quality Score",
        "unit": None,
        "device_class": None,
        "icon": "mdi:star",
        "state_class": SensorStateClass.MEASUREMENT,
    },
}

# Sleep efficiency categories
SLEEP_EFFICIENCY_CATEGORIES = {
    "excellent": {"min": 90, "max": 100, "color": "#4CAF50", "icon": "mdi:star"},
    "good": {"min": 80, "max": 89, "color": "#8BC34A", "icon": "mdi:star-half"},
    "fair": {"min": 70, "max": 79, "color": "#FFC107", "icon": "mdi:star-outline"},
    "poor": {"min": 60, "max": 69, "color": "#FF9800", "icon": "mdi:star-outline"},
    "very_poor": {"min": 0, "max": 59, "color": "#F44336", "icon": "mdi:star-outline"},
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep sleep efficiency sensors."""
    config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    eight = config_entry_data.api

    entities = []

    # Create sleep efficiency sensors for each user
    for user in eight.users.values():
        for calculation in SLEEP_EFFICIENCY_CALCULATIONS:
            entities.append(
                EightSleepEfficiencySensor(
                    entry,
                    config_entry_data.user_coordinator,
                    eight,
                    user,
                    calculation,
                )
            )

        # Create comprehensive sleep efficiency sensor
        entities.append(
            EightSleepComprehensiveEfficiencySensor(
                entry,
                config_entry_data.user_coordinator,
                eight,
                user,
            )
        )

    async_add_entities(entities)

class EightSleepEfficiencySensor(EightSleepBaseEntity, SensorEntity):
    """Individual sleep efficiency calculation sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        calculation: str,
    ) -> None:
        """Initialize the sleep efficiency sensor."""
        super().__init__(
            entry, coordinator, eight, user, f"sleep_efficiency_{calculation}"
        )

        self._calculation = calculation
        self._calculation_config = SLEEP_EFFICIENCY_CALCULATIONS[calculation]

        # Set sensor properties
        self._attr_name = self._calculation_config["name"]
        self._attr_icon = self._calculation_config["icon"]
        self._attr_native_unit_of_measurement = self._calculation_config["unit"]

        if self._calculation_config["device_class"]:
            self._attr_device_class = self._calculation_config["device_class"]

        if self._calculation_config["state_class"]:
            self._attr_state_class = self._calculation_config["state_class"]

    @property
    def native_value(self) -> float | str | None:
        """Return the current sleep efficiency value."""
        if not self.coordinator.data:
            return None

        try:
            efficiency_data = self._calculate_sleep_efficiency()
            if efficiency_data is None:
                return None

            value = efficiency_data.get(self._calculation)
            if value is None:
                return None

            if self._calculation == "sleep_quality_score":
                return self._format_sleep_quality_score(value)
            else:
                return round(float(value), 2)

        except Exception as err:
            _LOGGER.error("Error calculating sleep efficiency for %s: %s", self._attr_unique_id, err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None

        try:
            efficiency_data = self._calculate_sleep_efficiency()
            if efficiency_data is None:
                return None

            attributes = {
                "calculation": self._calculation,
                "last_updated": datetime.now().isoformat(),
            }

            # Add efficiency category
            value = efficiency_data.get(self._calculation)
            if value is not None:
                attributes["efficiency_category"] = self._get_efficiency_category(value)
                attributes["raw_value"] = value

            # Add calculation-specific attributes
            if self._calculation == "overall_efficiency":
                attributes["components"] = efficiency_data.get("components", {})
            elif self._calculation == "sleep_latency_efficiency":
                attributes["sleep_latency_minutes"] = efficiency_data.get("sleep_latency_minutes", 0)
            elif self._calculation == "wake_efficiency":
                attributes["wake_ups_count"] = efficiency_data.get("wake_ups_count", 0)
                attributes["total_wake_time"] = efficiency_data.get("total_wake_time", 0)
            elif self._calculation == "restlessness_efficiency":
                attributes["restlessness_score"] = efficiency_data.get("restlessness_score", 0)

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating attributes for %s: %s", self._attr_unique_id, err)
            return None

    def _calculate_sleep_efficiency(self) -> dict | None:
        """Calculate sleep efficiency metrics."""
        if not self._user_obj or not hasattr(self._user_obj, 'sleep_data'):
            return None

        try:
            # Get the most recent sleep session
            sleep_data = getattr(self._user_obj, 'sleep_data', {})
            sessions = sleep_data.get("sessions", [])

            if not sessions:
                return None

            # Get the most recent session
            latest_session = sessions[0]  # Assuming sessions are ordered by date
            return self._calculate_session_efficiency(latest_session)

        except Exception as err:
            _LOGGER.error("Error calculating sleep efficiency: %s", err)
            return None

    def _calculate_session_efficiency(self, session: dict) -> dict:
        """Calculate efficiency metrics for a sleep session."""
        try:
            # Extract basic sleep data
            total_sleep_time = session.get("sleepDuration", 0) / 3600  # Convert to hours
            time_in_bed = session.get("timeInBed", 0) / 3600  # Convert to hours
            sleep_latency = session.get("sleepLatency", 0) / 60  # Convert to minutes
            wake_ups = session.get("wakeUps", 0)
            restlessness = session.get("restlessness", 0)

            # Calculate efficiency metrics
            overall_efficiency = self._calculate_overall_efficiency(session)
            time_in_bed_efficiency = self._calculate_time_in_bed_efficiency(total_sleep_time, time_in_bed)
            sleep_latency_efficiency = self._calculate_sleep_latency_efficiency(sleep_latency)
            wake_efficiency = self._calculate_wake_efficiency(wake_ups, total_sleep_time)
            restlessness_efficiency = self._calculate_restlessness_efficiency(restlessness)
            sleep_continuity = self._calculate_sleep_continuity(session)
            sleep_consolidation = self._calculate_sleep_consolidation(session)
            sleep_quality_score = self._calculate_sleep_quality_score(session)

            return {
                "overall_efficiency": overall_efficiency,
                "time_in_bed_efficiency": time_in_bed_efficiency,
                "sleep_latency_efficiency": sleep_latency_efficiency,
                "wake_efficiency": wake_efficiency,
                "restlessness_efficiency": restlessness_efficiency,
                "sleep_continuity": sleep_continuity,
                "sleep_consolidation": sleep_consolidation,
                "sleep_quality_score": sleep_quality_score,
                "components": {
                    "total_sleep_time": total_sleep_time,
                    "time_in_bed": time_in_bed,
                    "sleep_latency_minutes": sleep_latency,
                    "wake_ups_count": wake_ups,
                    "restlessness_score": restlessness,
                }
            }

        except Exception as err:
            _LOGGER.error("Error calculating session efficiency: %s", err)
            return None

    def _calculate_overall_efficiency(self, session: dict) -> float:
        """Calculate overall sleep efficiency."""
        try:
            # Use the provided sleep efficiency if available
            efficiency = session.get("sleepEfficiency")
            if efficiency is not None:
                return float(efficiency)

            # Calculate based on time in bed vs actual sleep
            total_sleep_time = session.get("sleepDuration", 0)
            time_in_bed = session.get("timeInBed", 0)

            if time_in_bed > 0:
                return (total_sleep_time / time_in_bed) * 100
            else:
                return 0.0

        except Exception:
            return 0.0

    def _calculate_time_in_bed_efficiency(self, total_sleep_time: float, time_in_bed: float) -> float:
        """Calculate time in bed efficiency."""
        try:
            if time_in_bed > 0:
                efficiency = (total_sleep_time / time_in_bed) * 100
                return min(100.0, max(0.0, efficiency))
            else:
                return 0.0
        except Exception:
            return 0.0

    def _calculate_sleep_latency_efficiency(self, sleep_latency: float) -> float:
        """Calculate sleep latency efficiency (lower latency = higher efficiency)."""
        try:
            # Optimal sleep latency is 10-20 minutes
            # Efficiency decreases as latency increases
            if sleep_latency <= 10:
                return 100.0
            elif sleep_latency <= 20:
                return 90.0
            elif sleep_latency <= 30:
                return 75.0
            elif sleep_latency <= 45:
                return 50.0
            elif sleep_latency <= 60:
                return 25.0
            else:
                return 0.0
        except Exception:
            return 0.0

    def _calculate_wake_efficiency(self, wake_ups: int, total_sleep_time: float) -> float:
        """Calculate wake efficiency (fewer wake-ups = higher efficiency)."""
        try:
            if total_sleep_time <= 0:
                return 0.0

            # Calculate wake-ups per hour
            wake_ups_per_hour = wake_ups / total_sleep_time

            # Efficiency decreases with more wake-ups
            if wake_ups_per_hour <= 0.5:
                return 100.0
            elif wake_ups_per_hour <= 1.0:
                return 85.0
            elif wake_ups_per_hour <= 2.0:
                return 70.0
            elif wake_ups_per_hour <= 3.0:
                return 50.0
            elif wake_ups_per_hour <= 4.0:
                return 30.0
            else:
                return 10.0
        except Exception:
            return 0.0

    def _calculate_restlessness_efficiency(self, restlessness: float) -> float:
        """Calculate restlessness efficiency (lower restlessness = higher efficiency)."""
        try:
            # Restlessness is typically 0-100, where 0 is no restlessness
            # Efficiency decreases as restlessness increases
            if restlessness <= 10:
                return 100.0
            elif restlessness <= 25:
                return 85.0
            elif restlessness <= 40:
                return 70.0
            elif restlessness <= 60:
                return 50.0
            elif restlessness <= 80:
                return 30.0
            else:
                return 10.0
        except Exception:
            return 0.0

    def _calculate_sleep_continuity(self, session: dict) -> float:
        """Calculate sleep continuity (uninterrupted sleep periods)."""
        try:
            # This would typically analyze sleep stage transitions
            # For now, use a simplified calculation based on wake-ups
            wake_ups = session.get("wakeUps", 0)
            total_sleep_time = session.get("sleepDuration", 0) / 3600  # Hours

            if total_sleep_time <= 0:
                return 0.0

            # Fewer wake-ups per hour = better continuity
            wake_ups_per_hour = wake_ups / total_sleep_time

            if wake_ups_per_hour <= 0.2:
                return 100.0
            elif wake_ups_per_hour <= 0.5:
                return 90.0
            elif wake_ups_per_hour <= 1.0:
                return 75.0
            elif wake_ups_per_hour <= 2.0:
                return 50.0
            else:
                return 25.0
        except Exception:
            return 0.0

    def _calculate_sleep_consolidation(self, session: dict) -> float:
        """Calculate sleep consolidation (how well sleep is consolidated)."""
        try:
            # This would analyze sleep stage patterns
            # For now, use a simplified calculation
            deep_sleep = session.get("sleepStages", {}).get("deepDuration", 0) / 3600
            rem_sleep = session.get("sleepStages", {}).get("remDuration", 0) / 3600
            total_sleep_time = session.get("sleepDuration", 0) / 3600

            if total_sleep_time <= 0:
                return 0.0

            # Good consolidation has adequate deep and REM sleep
            deep_rem_ratio = (deep_sleep + rem_sleep) / total_sleep_time

            if deep_rem_ratio >= 0.4:
                return 100.0
            elif deep_rem_ratio >= 0.3:
                return 85.0
            elif deep_rem_ratio >= 0.2:
                return 70.0
            elif deep_rem_ratio >= 0.1:
                return 50.0
            else:
                return 25.0
        except Exception:
            return 0.0

    def _calculate_sleep_quality_score(self, session: dict) -> float:
        """Calculate overall sleep quality score."""
        try:
            # Weighted average of different efficiency metrics
            overall_efficiency = self._calculate_overall_efficiency(session)
            sleep_latency = session.get("sleepLatency", 0) / 60
            wake_ups = session.get("wakeUps", 0)
            restlessness = session.get("restlessness", 0)

            # Calculate individual scores
            latency_score = self._calculate_sleep_latency_efficiency(sleep_latency)
            wake_score = self._calculate_wake_efficiency(wake_ups, session.get("sleepDuration", 0) / 3600)
            restlessness_score = self._calculate_restlessness_efficiency(restlessness)

            # Weighted average (can be adjusted based on importance)
            quality_score = (
                overall_efficiency * 0.4 +
                latency_score * 0.2 +
                wake_score * 0.2 +
                restlessness_score * 0.2
            )

            return round(quality_score, 1)
        except Exception:
            return 0.0

    def _get_efficiency_category(self, efficiency: float) -> str:
        """Get efficiency category for a given value."""
        for category, config in SLEEP_EFFICIENCY_CATEGORIES.items():
            if config["min"] <= efficiency <= config["max"]:
                return category
        return "very_poor"

    def _format_sleep_quality_score(self, score: float) -> str:
        """Format sleep quality score."""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Fair"
        elif score >= 60:
            return "Poor"
        else:
            return "Very Poor"

class EightSleepComprehensiveEfficiencySensor(EightSleepBaseEntity, SensorEntity):
    """Comprehensive sleep efficiency sensor."""

    _attr_has_entity_name = True
    _attr_name = "Sleep Efficiency Analysis"
    _attr_icon = "mdi:chart-pie"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
    ) -> None:
        """Initialize the comprehensive sleep efficiency sensor."""
        super().__init__(
            entry, coordinator, eight, user, "sleep_efficiency_comprehensive"
        )

    @property
    def native_value(self) -> str | None:
        """Return the overall sleep efficiency assessment."""
        if not self.coordinator.data:
            return None

        try:
            efficiency_data = self._get_comprehensive_efficiency_data()
            if efficiency_data is None:
                return "Unknown"

            overall_efficiency = efficiency_data.get("overall_efficiency", 0)
            return self._get_efficiency_assessment(overall_efficiency)

        except Exception as err:
            _LOGGER.error("Error getting comprehensive efficiency data: %s", err)
            return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return detailed efficiency attributes."""
        if not self.coordinator.data:
            return None

        try:
            efficiency_data = self._get_comprehensive_efficiency_data()
            if efficiency_data is None:
                return None

            attributes = {
                "last_updated": datetime.now().isoformat(),
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            }

            # Add all efficiency metrics
            for calculation, config in SLEEP_EFFICIENCY_CALCULATIONS.items():
                value = efficiency_data.get(calculation)
                if value is not None:
                    attributes[f"{calculation}_value"] = value
                    attributes[f"{calculation}_category"] = self._get_efficiency_category(value)

            # Add recommendations
            recommendations = self._get_efficiency_recommendations(efficiency_data)
            if recommendations:
                attributes["recommendations"] = recommendations

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating comprehensive attributes: %s", err)
            return None

    def _get_comprehensive_efficiency_data(self) -> dict | None:
        """Get comprehensive efficiency data."""
        if not self._user_obj or not hasattr(self._user_obj, 'sleep_data'):
            return None

        try:
            sleep_data = getattr(self._user_obj, 'sleep_data', {})
            sessions = sleep_data.get("sessions", [])

            if not sessions:
                return None

            # Get the most recent session
            latest_session = sessions[0]
            return self._calculate_session_efficiency(latest_session)

        except Exception as err:
            _LOGGER.error("Error getting comprehensive efficiency data: %s", err)
            return None

    def _calculate_session_efficiency(self, session: dict) -> dict:
        """Calculate efficiency metrics for a sleep session."""
        try:
            # Extract basic sleep data
            total_sleep_time = session.get("sleepDuration", 0) / 3600  # Convert to hours
            time_in_bed = session.get("timeInBed", 0) / 3600  # Convert to hours
            sleep_latency = session.get("sleepLatency", 0) / 60  # Convert to minutes
            wake_ups = session.get("wakeUps", 0)
            restlessness = session.get("restlessness", 0)

            # Calculate efficiency metrics
            overall_efficiency = self._calculate_overall_efficiency(session)
            time_in_bed_efficiency = self._calculate_time_in_bed_efficiency(total_sleep_time, time_in_bed)
            sleep_latency_efficiency = self._calculate_sleep_latency_efficiency(sleep_latency)
            wake_efficiency = self._calculate_wake_efficiency(wake_ups, total_sleep_time)
            restlessness_efficiency = self._calculate_restlessness_efficiency(restlessness)
            sleep_continuity = self._calculate_sleep_continuity(session)
            sleep_consolidation = self._calculate_sleep_consolidation(session)
            sleep_quality_score = self._calculate_sleep_quality_score(session)

            return {
                "overall_efficiency": overall_efficiency,
                "time_in_bed_efficiency": time_in_bed_efficiency,
                "sleep_latency_efficiency": sleep_latency_efficiency,
                "wake_efficiency": wake_efficiency,
                "restlessness_efficiency": restlessness_efficiency,
                "sleep_continuity": sleep_continuity,
                "sleep_consolidation": sleep_consolidation,
                "sleep_quality_score": sleep_quality_score,
            }

        except Exception as err:
            _LOGGER.error("Error calculating session efficiency: %s", err)
            return None

    def _calculate_overall_efficiency(self, session: dict) -> float:
        """Calculate overall sleep efficiency."""
        try:
            efficiency = session.get("sleepEfficiency")
            if efficiency is not None:
                return float(efficiency)

            total_sleep_time = session.get("sleepDuration", 0)
            time_in_bed = session.get("timeInBed", 0)

            if time_in_bed > 0:
                return (total_sleep_time / time_in_bed) * 100
            else:
                return 0.0
        except Exception:
            return 0.0

    def _calculate_time_in_bed_efficiency(self, total_sleep_time: float, time_in_bed: float) -> float:
        """Calculate time in bed efficiency."""
        try:
            if time_in_bed > 0:
                efficiency = (total_sleep_time / time_in_bed) * 100
                return min(100.0, max(0.0, efficiency))
            else:
                return 0.0
        except Exception:
            return 0.0

    def _calculate_sleep_latency_efficiency(self, sleep_latency: float) -> float:
        """Calculate sleep latency efficiency."""
        try:
            if sleep_latency <= 10:
                return 100.0
            elif sleep_latency <= 20:
                return 90.0
            elif sleep_latency <= 30:
                return 75.0
            elif sleep_latency <= 45:
                return 50.0
            elif sleep_latency <= 60:
                return 25.0
            else:
                return 0.0
        except Exception:
            return 0.0

    def _calculate_wake_efficiency(self, wake_ups: int, total_sleep_time: float) -> float:
        """Calculate wake efficiency."""
        try:
            if total_sleep_time <= 0:
                return 0.0

            wake_ups_per_hour = wake_ups / total_sleep_time

            if wake_ups_per_hour <= 0.5:
                return 100.0
            elif wake_ups_per_hour <= 1.0:
                return 85.0
            elif wake_ups_per_hour <= 2.0:
                return 70.0
            elif wake_ups_per_hour <= 3.0:
                return 50.0
            elif wake_ups_per_hour <= 4.0:
                return 30.0
            else:
                return 10.0
        except Exception:
            return 0.0

    def _calculate_restlessness_efficiency(self, restlessness: float) -> float:
        """Calculate restlessness efficiency."""
        try:
            if restlessness <= 10:
                return 100.0
            elif restlessness <= 25:
                return 85.0
            elif restlessness <= 40:
                return 70.0
            elif restlessness <= 60:
                return 50.0
            elif restlessness <= 80:
                return 30.0
            else:
                return 10.0
        except Exception:
            return 0.0

    def _calculate_sleep_continuity(self, session: dict) -> float:
        """Calculate sleep continuity."""
        try:
            wake_ups = session.get("wakeUps", 0)
            total_sleep_time = session.get("sleepDuration", 0) / 3600

            if total_sleep_time <= 0:
                return 0.0

            wake_ups_per_hour = wake_ups / total_sleep_time

            if wake_ups_per_hour <= 0.2:
                return 100.0
            elif wake_ups_per_hour <= 0.5:
                return 90.0
            elif wake_ups_per_hour <= 1.0:
                return 75.0
            elif wake_ups_per_hour <= 2.0:
                return 50.0
            else:
                return 25.0
        except Exception:
            return 0.0

    def _calculate_sleep_consolidation(self, session: dict) -> float:
        """Calculate sleep consolidation."""
        try:
            deep_sleep = session.get("sleepStages", {}).get("deepDuration", 0) / 3600
            rem_sleep = session.get("sleepStages", {}).get("remDuration", 0) / 3600
            total_sleep_time = session.get("sleepDuration", 0) / 3600

            if total_sleep_time <= 0:
                return 0.0

            deep_rem_ratio = (deep_sleep + rem_sleep) / total_sleep_time

            if deep_rem_ratio >= 0.4:
                return 100.0
            elif deep_rem_ratio >= 0.3:
                return 85.0
            elif deep_rem_ratio >= 0.2:
                return 70.0
            elif deep_rem_ratio >= 0.1:
                return 50.0
            else:
                return 25.0
        except Exception:
            return 0.0

    def _calculate_sleep_quality_score(self, session: dict) -> float:
        """Calculate overall sleep quality score."""
        try:
            overall_efficiency = self._calculate_overall_efficiency(session)
            sleep_latency = session.get("sleepLatency", 0) / 60
            wake_ups = session.get("wakeUps", 0)
            restlessness = session.get("restlessness", 0)

            latency_score = self._calculate_sleep_latency_efficiency(sleep_latency)
            wake_score = self._calculate_wake_efficiency(wake_ups, session.get("sleepDuration", 0) / 3600)
            restlessness_score = self._calculate_restlessness_efficiency(restlessness)

            quality_score = (
                overall_efficiency * 0.4 +
                latency_score * 0.2 +
                wake_score * 0.2 +
                restlessness_score * 0.2
            )

            return round(quality_score, 1)
        except Exception:
            return 0.0

    def _get_efficiency_assessment(self, efficiency: float) -> str:
        """Get overall efficiency assessment."""
        if efficiency >= 90:
            return "Excellent Sleep Efficiency"
        elif efficiency >= 80:
            return "Good Sleep Efficiency"
        elif efficiency >= 70:
            return "Fair Sleep Efficiency"
        elif efficiency >= 60:
            return "Poor Sleep Efficiency"
        else:
            return "Very Poor Sleep Efficiency"

    def _get_efficiency_category(self, efficiency: float) -> str:
        """Get efficiency category for a given value."""
        for category, config in SLEEP_EFFICIENCY_CATEGORIES.items():
            if config["min"] <= efficiency <= config["max"]:
                return category
        return "very_poor"

    def _get_efficiency_recommendations(self, efficiency_data: dict) -> list[str]:
        """Get sleep efficiency recommendations based on current metrics."""
        recommendations = []

        try:
            overall_efficiency = efficiency_data.get("overall_efficiency", 0)
            sleep_latency_efficiency = efficiency_data.get("sleep_latency_efficiency", 0)
            wake_efficiency = efficiency_data.get("wake_efficiency", 0)
            restlessness_efficiency = efficiency_data.get("restlessness_efficiency", 0)

            if overall_efficiency < 80:
                recommendations.append("Focus on improving overall sleep efficiency")

            if sleep_latency_efficiency < 70:
                recommendations.append("Work on reducing sleep latency")

            if wake_efficiency < 70:
                recommendations.append("Minimize wake-ups during sleep")

            if restlessness_efficiency < 70:
                recommendations.append("Reduce restlessness during sleep")

            if not recommendations:
                recommendations.append("Maintain current sleep efficiency")

        except Exception as err:
            _LOGGER.error("Error generating efficiency recommendations: %s", err)

        return recommendations
