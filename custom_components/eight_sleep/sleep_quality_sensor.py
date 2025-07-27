"""Sleep quality breakdown sensors for Eight Sleep."""

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

# Sleep quality metrics
SLEEP_QUALITY_METRICS = {
    "overall_score": {
        "name": "Overall Sleep Score",
        "unit": None,
        "device_class": None,
        "icon": "mdi:sleep",
        "min_value": 0,
        "max_value": 100,
    },
    "sleep_efficiency": {
        "name": "Sleep Efficiency",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:percent",
        "min_value": 0,
        "max_value": 100,
    },
    "sleep_latency": {
        "name": "Sleep Latency",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:timer-sand",
        "min_value": 0,
        "max_value": 60,
    },
    "wake_ups": {
        "name": "Wake Ups",
        "unit": "count",
        "device_class": None,
        "icon": "mdi:eye",
        "min_value": 0,
        "max_value": 20,
    },
    "restlessness": {
        "name": "Restlessness",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:bed",
        "min_value": 0,
        "max_value": 100,
    },
    "sleep_consistency": {
        "name": "Sleep Consistency",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:calendar-clock",
        "min_value": 0,
        "max_value": 100,
    },
    "sleep_regularity": {
        "name": "Sleep Regularity",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:clock-outline",
        "min_value": 0,
        "max_value": 100,
    },
    "sleep_balance": {
        "name": "Sleep Balance",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:scale-balance",
        "min_value": 0,
        "max_value": 100,
    },
}

# Sleep quality categories
SLEEP_QUALITY_CATEGORIES = {
    "excellent": {"min": 90, "color": "#4CAF50", "icon": "mdi:star"},
    "good": {"min": 80, "color": "#8BC34A", "icon": "mdi:star-half"},
    "fair": {"min": 70, "color": "#FFC107", "icon": "mdi:star-outline"},
    "poor": {"min": 60, "color": "#FF9800", "icon": "mdi:star-outline"},
    "very_poor": {"min": 0, "color": "#F44336", "icon": "mdi:star-outline"},
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep sleep quality sensors."""
    config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    eight = config_entry_data.api

    entities = []

    # Create sleep quality sensors for each user
    for user in eight.users.values():
        for metric in SLEEP_QUALITY_METRICS:
            entities.append(
                EightSleepQualitySensor(
                    entry,
                    config_entry_data.user_coordinator,
                    eight,
                    user,
                    metric,
                )
            )

        # Create comprehensive sleep quality sensor
        entities.append(
            EightSleepComprehensiveQualitySensor(
                entry,
                config_entry_data.user_coordinator,
                eight,
                user,
            )
        )

    async_add_entities(entities)

class EightSleepQualitySensor(EightSleepBaseEntity, SensorEntity):
    """Individual sleep quality metric sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        metric: str,
    ) -> None:
        """Initialize the sleep quality sensor."""
        super().__init__(
            entry, coordinator, eight, user, f"sleep_quality_{metric}"
        )

        self._metric = metric
        self._metric_config = SLEEP_QUALITY_METRICS[metric]

        # Set sensor properties
        self._attr_name = self._metric_config["name"]
        self._attr_icon = self._metric_config["icon"]
        self._attr_native_unit_of_measurement = self._metric_config["unit"]

        if self._metric_config["device_class"]:
            self._attr_device_class = self._metric_config["device_class"]

        # Set state class for numeric values
        if metric not in ["overall_score"]:
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | str | None:
        """Return the current sleep quality value."""
        if not self.coordinator.data:
            return None

        try:
            quality_data = self._get_sleep_quality_data()
            if quality_data is None:
                return None

            value = quality_data.get(self._metric)
            if value is None:
                return None

            if self._metric == "overall_score":
                return self._format_overall_score(value)
            elif self._metric == "sleep_efficiency":
                return self._format_sleep_efficiency(value)
            elif self._metric == "restlessness":
                return self._format_restlessness(value)
            elif self._metric == "sleep_consistency":
                return self._format_consistency(value)
            elif self._metric == "sleep_regularity":
                return self._format_regularity(value)
            elif self._metric == "sleep_balance":
                return self._format_balance(value)
            else:
                return round(float(value), 2)

        except Exception as err:
            _LOGGER.error("Error getting sleep quality for %s: %s", self._attr_unique_id, err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None

        try:
            quality_data = self._get_sleep_quality_data()
            if quality_data is None:
                return None

            attributes = {
                "metric": self._metric,
                "last_updated": datetime.now().isoformat(),
                "min_value": self._metric_config["min_value"],
                "max_value": self._metric_config["max_value"],
            }

            # Add quality category
            value = quality_data.get(self._metric)
            if value is not None:
                attributes["quality_category"] = self._get_quality_category(value)
                attributes["raw_value"] = value

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating attributes for %s: %s", self._attr_unique_id, err)
            return None

    def _get_sleep_quality_data(self) -> dict | None:
        """Get sleep quality data from the user."""
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
            return latest_session.get("qualityMetrics", {})

        except Exception as err:
            _LOGGER.error("Error getting sleep quality data: %s", err)
            return None

    def _get_quality_category(self, value: float) -> str:
        """Get the quality category for a given value."""
        for category, config in SLEEP_QUALITY_CATEGORIES.items():
            if value >= config["min"]:
                return category
        return "very_poor"

    def _format_overall_score(self, score: float) -> str:
        """Format overall sleep score."""
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

    def _format_restlessness(self, restlessness: float) -> str:
        """Format restlessness (lower is better)."""
        if restlessness <= 10:
            return "Very Low"
        elif restlessness <= 20:
            return "Low"
        elif restlessness <= 30:
            return "Moderate"
        elif restlessness <= 40:
            return "High"
        else:
            return "Very High"

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

    def _format_regularity(self, regularity: float) -> str:
        """Format sleep regularity."""
        if regularity >= 90:
            return "Excellent"
        elif regularity >= 80:
            return "Good"
        elif regularity >= 70:
            return "Fair"
        elif regularity >= 60:
            return "Poor"
        else:
            return "Very Poor"

    def _format_balance(self, balance: float) -> str:
        """Format sleep balance."""
        if balance >= 90:
            return "Excellent"
        elif balance >= 80:
            return "Good"
        elif balance >= 70:
            return "Fair"
        elif balance >= 60:
            return "Poor"
        else:
            return "Very Poor"

class EightSleepComprehensiveQualitySensor(EightSleepBaseEntity, SensorEntity):
    """Comprehensive sleep quality sensor with detailed breakdown."""

    _attr_has_entity_name = True
    _attr_name = "Sleep Quality Analysis"
    _attr_icon = "mdi:sleep"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
    ) -> None:
        """Initialize the comprehensive sleep quality sensor."""
        super().__init__(
            entry, coordinator, eight, user, "sleep_quality_comprehensive"
        )

    @property
    def native_value(self) -> str | None:
        """Return the overall sleep quality assessment."""
        if not self.coordinator.data:
            return None

        try:
            quality_data = self._get_comprehensive_quality_data()
            if quality_data is None:
                return "Unknown"

            overall_score = quality_data.get("overall_score", 0)
            return self._get_overall_assessment(overall_score)

        except Exception as err:
            _LOGGER.error("Error getting comprehensive quality: %s", err)
            return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return detailed sleep quality attributes."""
        if not self.coordinator.data:
            return None

        try:
            quality_data = self._get_comprehensive_quality_data()
            if quality_data is None:
                return None

            attributes = {
                "last_updated": datetime.now().isoformat(),
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            }

            # Add all quality metrics
            for metric, config in SLEEP_QUALITY_METRICS.items():
                value = quality_data.get(metric)
                if value is not None:
                    attributes[f"{metric}_value"] = value
                    attributes[f"{metric}_category"] = self._get_quality_category(value)

            # Add recommendations
            recommendations = self._get_sleep_recommendations(quality_data)
            if recommendations:
                attributes["recommendations"] = recommendations

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating comprehensive attributes: %s", err)
            return None

    def _get_comprehensive_quality_data(self) -> dict | None:
        """Get comprehensive sleep quality data."""
        if not self._user_obj or not hasattr(self._user_obj, 'sleep_data'):
            return None

        try:
            sleep_data = getattr(self._user_obj, 'sleep_data', {})
            sessions = sleep_data.get("sessions", [])

            if not sessions:
                return None

            # Get the most recent session
            latest_session = sessions[0]
            return latest_session.get("qualityMetrics", {})

        except Exception as err:
            _LOGGER.error("Error getting comprehensive quality data: %s", err)
            return None

    def _get_overall_assessment(self, score: float) -> str:
        """Get overall sleep assessment."""
        if score >= 90:
            return "Excellent Sleep"
        elif score >= 80:
            return "Good Sleep"
        elif score >= 70:
            return "Fair Sleep"
        elif score >= 60:
            return "Poor Sleep"
        else:
            return "Very Poor Sleep"

    def _get_quality_category(self, value: float) -> str:
        """Get the quality category for a given value."""
        for category, config in SLEEP_QUALITY_CATEGORIES.items():
            if value >= config["min"]:
                return category
        return "very_poor"

    def _get_sleep_recommendations(self, quality_data: dict) -> list[str]:
        """Get personalized sleep recommendations based on quality data."""
        recommendations = []

        try:
            efficiency = quality_data.get("sleep_efficiency", 0)
            latency = quality_data.get("sleep_latency", 0)
            wake_ups = quality_data.get("wake_ups", 0)
            restlessness = quality_data.get("restlessness", 0)

            if efficiency < 80:
                recommendations.append("Consider improving sleep environment")

            if latency > 20:
                recommendations.append("Try relaxation techniques before bed")

            if wake_ups > 3:
                recommendations.append("Reduce caffeine and screen time")

            if restlessness > 30:
                recommendations.append("Check mattress comfort and room temperature")

            if not recommendations:
                recommendations.append("Maintain current sleep habits")

        except Exception as err:
            _LOGGER.error("Error generating recommendations: %s", err)

        return recommendations
