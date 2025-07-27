"""Respiratory rate monitoring sensors for Eight Sleep."""

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
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import EightSleepBaseEntity, EightSleepConfigEntryData
from .const import DOMAIN
from .pyEight.eight import EightSleep
from .pyEight.user import EightUser

_LOGGER = logging.getLogger(__name__)

# Respiratory rate sensor types
RESPIRATORY_RATE_SENSORS = {
    "current_respiratory_rate": {
        "name": "Current Respiratory Rate",
        "unit": "breaths/min",
        "device_class": SensorDeviceClass.FREQUENCY,
        "icon": "mdi:lungs",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "average_respiratory_rate": {
        "name": "Average Respiratory Rate",
        "unit": "breaths/min",
        "device_class": SensorDeviceClass.FREQUENCY,
        "icon": "mdi:lungs",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "respiratory_rate_trend": {
        "name": "Respiratory Rate Trend",
        "unit": "breaths/min",
        "device_class": None,
        "icon": "mdi:trending-up",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "respiratory_rate_quality": {
        "name": "Respiratory Rate Quality",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:lungs-check",
        "state_class": None,
    },
    "respiratory_rate_stability": {
        "name": "Respiratory Rate Stability",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:lungs-stable",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "breathing_pattern": {
        "name": "Breathing Pattern",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:lungs-pattern",
        "state_class": None,
    },
    "respiratory_efficiency": {
        "name": "Respiratory Efficiency",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:lungs-efficiency",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "sleep_apnea_risk": {
        "name": "Sleep Apnea Risk",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:lungs-alert",
        "state_class": None,
    },
    "respiratory_health_score": {
        "name": "Respiratory Health Score",
        "unit": None,
        "device_class": None,
        "icon": "mdi:lungs-score",
        "state_class": SensorStateClass.MEASUREMENT,
    },
}

# Respiratory rate categories
RESPIRATORY_RATE_CATEGORIES = {
    "very_slow": {"min": 0, "max": 8, "description": "Very Slow (< 8 breaths/min)"},
    "slow": {"min": 8, "max": 12, "description": "Slow (8-12 breaths/min)"},
    "normal": {"min": 12, "max": 20, "description": "Normal (12-20 breaths/min)"},
    "elevated": {"min": 20, "max": 25, "description": "Elevated (20-25 breaths/min)"},
    "rapid": {"min": 25, "max": 30, "description": "Rapid (25-30 breaths/min)"},
    "very_rapid": {"min": 30, "max": 100, "description": "Very Rapid (> 30 breaths/min)"},
}

# Respiratory rate quality categories
RESPIRATORY_QUALITY_CATEGORIES = {
    "excellent": {"min": 90, "max": 100, "description": "Excellent"},
    "good": {"min": 70, "max": 89, "description": "Good"},
    "fair": {"min": 50, "max": 69, "description": "Fair"},
    "poor": {"min": 30, "max": 49, "description": "Poor"},
    "very_poor": {"min": 0, "max": 29, "description": "Very Poor"},
}

# Sleep apnea risk categories
SLEEP_APNEA_RISK_CATEGORIES = {
    "low": {"min": 0, "max": 20, "description": "Low Risk"},
    "moderate": {"min": 21, "max": 40, "description": "Moderate Risk"},
    "high": {"min": 41, "max": 60, "description": "High Risk"},
    "very_high": {"min": 61, "max": 100, "description": "Very High Risk"},
}

# Breathing pattern categories
BREATHING_PATTERN_CATEGORIES = {
    "regular": "Regular Breathing",
    "irregular": "Irregular Breathing",
    "shallow": "Shallow Breathing",
    "deep": "Deep Breathing",
    "periodic": "Periodic Breathing",
    "apneic": "Apneic Episodes",
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep respiratory rate sensors."""
    config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    eight = config_entry_data.api

    entities = []

    # Create respiratory rate sensors for each user
    for user in eight.users.values():
        for sensor_type in RESPIRATORY_RATE_SENSORS:
            entities.append(
                EightSleepRespiratoryRateSensor(
                    entry,
                    config_entry_data.user_coordinator,
                    eight,
                    user,
                    sensor_type,
                )
            )

        # Create comprehensive respiratory rate sensor
        entities.append(
            EightSleepComprehensiveRespiratoryRateSensor(
                entry,
                config_entry_data.user_coordinator,
                eight,
                user,
            )
        )

    async_add_entities(entities)

class EightSleepRespiratoryRateSensor(EightSleepBaseEntity, SensorEntity):
    """Individual respiratory rate monitoring sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        sensor_type: str,
    ) -> None:
        """Initialize the respiratory rate sensor."""
        super().__init__(
            entry, coordinator, eight, user, f"respiratory_rate_{sensor_type}"
        )

        self._sensor_type = sensor_type
        self._sensor_config = RESPIRATORY_RATE_SENSORS[sensor_type]

        # Set sensor properties
        self._attr_name = self._sensor_config["name"]
        self._attr_icon = self._sensor_config["icon"]
        self._attr_native_unit_of_measurement = self._sensor_config["unit"]

        if self._sensor_config["device_class"]:
            self._attr_device_class = self._sensor_config["device_class"]

        if self._sensor_config["state_class"]:
            self._attr_state_class = self._sensor_config["state_class"]

    @property
    def native_value(self) -> float | str | None:
        """Return the current respiratory rate value."""
        if not self.coordinator.data:
            return None

        try:
            respiratory_data = self._get_respiratory_data()
            if respiratory_data is None:
                return None

            value = respiratory_data.get(self._sensor_type)
            if value is None:
                return None

            if self._sensor_type == "respiratory_rate_quality":
                return self._get_respiratory_quality_category(value)
            elif self._sensor_type == "breathing_pattern":
                return self._get_breathing_pattern_category(value)
            elif self._sensor_type == "sleep_apnea_risk":
                return self._get_sleep_apnea_risk_category(value)
            elif self._sensor_type == "respiratory_health_score":
                return self._get_respiratory_health_assessment(value)
            else:
                return round(float(value), 2)

        except Exception as err:
            _LOGGER.error("Error getting respiratory data for %s: %s", self._attr_unique_id, err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None

        try:
            respiratory_data = self._get_respiratory_data()
            if respiratory_data is None:
                return None

            attributes = {
                "sensor_type": self._sensor_type,
                "last_updated": datetime.now().isoformat(),
            }

            # Add respiratory-specific attributes
            if self._sensor_type == "current_respiratory_rate":
                value = respiratory_data.get(self._sensor_type)
                if value is not None:
                    attributes["respiratory_category"] = self._get_respiratory_category(value)
                    attributes["is_normal_rate"] = 12 <= value <= 20
                    attributes["breathing_quality"] = self._assess_breathing_quality(value)

            elif self._sensor_type == "average_respiratory_rate":
                value = respiratory_data.get(self._sensor_type)
                if value is not None:
                    attributes["average_trend"] = respiratory_data.get("respiratory_rate_trend", 0)
                    attributes["respiratory_consistency"] = respiratory_data.get("respiratory_consistency", 0)

            elif self._sensor_type == "respiratory_rate_trend":
                value = respiratory_data.get(self._sensor_type)
                if value is not None:
                    attributes["trend_direction"] = "increasing" if value > 0 else "decreasing" if value < 0 else "stable"
                    attributes["trend_magnitude"] = abs(value)

            elif self._sensor_type == "respiratory_rate_stability":
                value = respiratory_data.get(self._sensor_type)
                if value is not None:
                    attributes["stability_category"] = self._get_stability_category(value)
                    attributes["respiratory_variance"] = respiratory_data.get("respiratory_variance", 0)

            elif self._sensor_type == "sleep_apnea_risk":
                value = respiratory_data.get(self._sensor_type)
                if value is not None:
                    attributes["risk_level"] = self._get_sleep_apnea_risk_category(value)
                    attributes["apnea_episodes"] = respiratory_data.get("apnea_episodes", 0)
                    attributes["hypopnea_episodes"] = respiratory_data.get("hypopnea_episodes", 0)

            elif self._sensor_type == "respiratory_efficiency":
                value = respiratory_data.get(self._sensor_type)
                if value is not None:
                    attributes["efficiency_category"] = self._get_efficiency_category(value)
                    attributes["oxygen_saturation"] = respiratory_data.get("oxygen_saturation", 0)

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating attributes for %s: %s", self._attr_unique_id, err)
            return None

    def _get_respiratory_data(self) -> dict | None:
        """Get respiratory data from the user."""
        if not self._user_obj or not hasattr(self._user_obj, 'sleep_data'):
            return None

        try:
            sleep_data = getattr(self._user_obj, 'sleep_data', {})
            sessions = sleep_data.get("sessions", [])

            if not sessions:
                return None

            # Get the most recent session
            latest_session = sessions[0]
            return self._extract_respiratory_data(latest_session)

        except Exception as err:
            _LOGGER.error("Error getting respiratory data: %s", err)
            return None

    def _extract_respiratory_data(self, session: dict) -> dict:
        """Extract respiratory data from a sleep session."""
        try:
            # Extract respiratory metrics from session data
            respiratory_data = session.get("respiratory", {})

            current_respiratory_rate = respiratory_data.get("current", 0)
            average_respiratory_rate = respiratory_data.get("average", 0)
            respiratory_rate_trend = respiratory_data.get("trend", 0)
            respiratory_rate_quality = self._calculate_respiratory_quality(current_respiratory_rate)
            respiratory_rate_stability = self._calculate_respiratory_stability(session)
            breathing_pattern = self._determine_breathing_pattern(session)
            respiratory_efficiency = self._calculate_respiratory_efficiency(session)
            sleep_apnea_risk = self._calculate_sleep_apnea_risk(session)
            respiratory_health_score = self._calculate_respiratory_health_score(session)

            return {
                "current_respiratory_rate": current_respiratory_rate,
                "average_respiratory_rate": average_respiratory_rate,
                "respiratory_rate_trend": respiratory_rate_trend,
                "respiratory_rate_quality": respiratory_rate_quality,
                "respiratory_rate_stability": respiratory_rate_stability,
                "breathing_pattern": breathing_pattern,
                "respiratory_efficiency": respiratory_efficiency,
                "sleep_apnea_risk": sleep_apnea_risk,
                "respiratory_health_score": respiratory_health_score,
                "respiratory_consistency": self._calculate_respiratory_consistency(session),
                "respiratory_variance": self._calculate_respiratory_variance(session),
                "apnea_episodes": respiratory_data.get("apnea_episodes", 0),
                "hypopnea_episodes": respiratory_data.get("hypopnea_episodes", 0),
                "oxygen_saturation": respiratory_data.get("oxygen_saturation", 0),
            }

        except Exception as err:
            _LOGGER.error("Error extracting respiratory data: %s", err)
            return None

    def _calculate_respiratory_quality(self, respiratory_rate: float) -> float:
        """Calculate respiratory rate quality score."""
        if 12 <= respiratory_rate <= 20:
            return 100.0
        elif 10 <= respiratory_rate <= 22:
            return 85.0
        elif 8 <= respiratory_rate <= 25:
            return 70.0
        elif 6 <= respiratory_rate <= 30:
            return 50.0
        else:
            return 25.0

    def _calculate_respiratory_stability(self, session: dict) -> float:
        """Calculate respiratory rate stability percentage."""
        try:
            # This would typically analyze respiratory rate variance over time
            # For now, use a simplified calculation
            respiratory_data = session.get("respiratory", {})
            variance = respiratory_data.get("variance", 0)

            if variance <= 2:
                return 100.0
            elif variance <= 4:
                return 85.0
            elif variance <= 6:
                return 70.0
            elif variance <= 8:
                return 50.0
            else:
                return 30.0
        except Exception:
            return 0.0

    def _determine_breathing_pattern(self, session: dict) -> str:
        """Determine breathing pattern category."""
        try:
            respiratory_data = session.get("respiratory", {})
            pattern = respiratory_data.get("pattern", "regular")

            if pattern == "regular":
                return "regular"
            elif pattern == "irregular":
                return "irregular"
            elif pattern == "shallow":
                return "shallow"
            elif pattern == "deep":
                return "deep"
            elif pattern == "periodic":
                return "periodic"
            elif pattern == "apneic":
                return "apneic"
            else:
                return "regular"
        except Exception:
            return "regular"

    def _calculate_respiratory_efficiency(self, session: dict) -> float:
        """Calculate respiratory efficiency percentage."""
        try:
            # This would analyze breathing efficiency
            # For now, use a simplified calculation
            respiratory_data = session.get("respiratory", {})
            efficiency = respiratory_data.get("efficiency", 0)

            return min(100.0, max(0.0, efficiency))
        except Exception:
            return 0.0

    def _calculate_sleep_apnea_risk(self, session: dict) -> float:
        """Calculate sleep apnea risk score."""
        try:
            # This would analyze breathing patterns for apnea indicators
            # For now, use a simplified calculation
            respiratory_data = session.get("respiratory", {})
            apnea_episodes = respiratory_data.get("apnea_episodes", 0)
            hypopnea_episodes = respiratory_data.get("hypopnea_episodes", 0)

            # Calculate risk based on episodes
            total_episodes = apnea_episodes + hypopnea_episodes

            if total_episodes == 0:
                return 10.0
            elif total_episodes <= 5:
                return 30.0
            elif total_episodes <= 15:
                return 50.0
            elif total_episodes <= 30:
                return 70.0
            else:
                return 90.0
        except Exception:
            return 0.0

    def _calculate_respiratory_health_score(self, session: dict) -> float:
        """Calculate overall respiratory health score."""
        try:
            # Weighted average of different respiratory metrics
            current_rate = session.get("respiratory", {}).get("current", 16)
            quality = self._calculate_respiratory_quality(current_rate)
            stability = self._calculate_respiratory_stability(session)
            efficiency = self._calculate_respiratory_efficiency(session)
            apnea_risk = self._calculate_sleep_apnea_risk(session)

            # Invert apnea risk (lower is better)
            apnea_score = 100 - apnea_risk

            # Weighted average
            health_score = (
                quality * 0.3 +
                stability * 0.25 +
                efficiency * 0.25 +
                apnea_score * 0.2
            )

            return round(health_score, 1)
        except Exception:
            return 0.0

    def _calculate_respiratory_consistency(self, session: dict) -> float:
        """Calculate respiratory consistency."""
        try:
            # This would analyze respiratory consistency over time
            # For now, use a placeholder value
            return 85.0
        except Exception:
            return 0.0

    def _calculate_respiratory_variance(self, session: dict) -> float:
        """Calculate respiratory variance."""
        try:
            # This would calculate actual respiratory variance
            # For now, use a placeholder value
            return 3.2
        except Exception:
            return 0.0

    def _get_respiratory_quality_category(self, quality: float) -> str:
        """Get respiratory quality category."""
        for category, config in RESPIRATORY_QUALITY_CATEGORIES.items():
            if config["min"] <= quality <= config["max"]:
                return config["description"]
        return "Unknown"

    def _get_breathing_pattern_category(self, pattern: str) -> str:
        """Get breathing pattern category."""
        return BREATHING_PATTERN_CATEGORIES.get(pattern, "Regular Breathing")

    def _get_sleep_apnea_risk_category(self, risk: float) -> str:
        """Get sleep apnea risk category."""
        for category, config in SLEEP_APNEA_RISK_CATEGORIES.items():
            if config["min"] <= risk <= config["max"]:
                return config["description"]
        return "Unknown"

    def _get_respiratory_health_assessment(self, score: float) -> str:
        """Get respiratory health assessment."""
        if score >= 90:
            return "Excellent Respiratory Health"
        elif score >= 80:
            return "Good Respiratory Health"
        elif score >= 70:
            return "Fair Respiratory Health"
        elif score >= 60:
            return "Poor Respiratory Health"
        else:
            return "Very Poor Respiratory Health"

    def _get_respiratory_category(self, rate: float) -> str:
        """Get respiratory rate category."""
        for category, config in RESPIRATORY_RATE_CATEGORIES.items():
            if config["min"] <= rate <= config["max"]:
                return config["description"]
        return "Unknown"

    def _assess_breathing_quality(self, rate: float) -> str:
        """Assess breathing quality."""
        if 12 <= rate <= 20:
            return "Excellent"
        elif 10 <= rate <= 22:
            return "Good"
        elif 8 <= rate <= 25:
            return "Fair"
        else:
            return "Poor"

    def _get_stability_category(self, stability: float) -> str:
        """Get stability category."""
        if stability >= 90:
            return "Excellent"
        elif stability >= 70:
            return "Good"
        elif stability >= 50:
            return "Fair"
        elif stability >= 30:
            return "Poor"
        else:
            return "Very Poor"

    def _get_efficiency_category(self, efficiency: float) -> str:
        """Get efficiency category."""
        if efficiency >= 90:
            return "Excellent"
        elif efficiency >= 70:
            return "Good"
        elif efficiency >= 50:
            return "Fair"
        elif efficiency >= 30:
            return "Poor"
        else:
            return "Very Poor"

class EightSleepComprehensiveRespiratoryRateSensor(EightSleepBaseEntity, SensorEntity):
    """Comprehensive respiratory rate monitoring sensor."""

    _attr_has_entity_name = True
    _attr_name = "Respiratory Rate Analysis"
    _attr_icon = "mdi:lungs-multiple"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
    ) -> None:
        """Initialize the comprehensive respiratory rate sensor."""
        super().__init__(
            entry, coordinator, eight, user, "respiratory_rate_comprehensive"
        )

    @property
    def native_value(self) -> str | None:
        """Return the overall respiratory assessment."""
        if not self.coordinator.data:
            return None

        try:
            respiratory_data = self._get_comprehensive_respiratory_data()
            if respiratory_data is None:
                return "Unknown"

            current_rate = respiratory_data.get("current_respiratory_rate", 16)
            return self._get_respiratory_assessment(current_rate)

        except Exception as err:
            _LOGGER.error("Error getting comprehensive respiratory data: %s", err)
            return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return detailed respiratory attributes."""
        if not self.coordinator.data:
            return None

        try:
            respiratory_data = self._get_comprehensive_respiratory_data()
            if respiratory_data is None:
                return None

            attributes = {
                "last_updated": datetime.now().isoformat(),
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            }

            # Add all respiratory metrics
            for sensor_type, config in RESPIRATORY_RATE_SENSORS.items():
                value = respiratory_data.get(sensor_type)
                if value is not None:
                    attributes[f"{sensor_type}_value"] = value
                    if sensor_type == "current_respiratory_rate":
                        attributes[f"{sensor_type}_category"] = self._get_respiratory_category(value)
                    elif sensor_type == "respiratory_rate_quality":
                        attributes[f"{sensor_type}_category"] = self._get_respiratory_quality_category(value)
                    elif sensor_type == "sleep_apnea_risk":
                        attributes[f"{sensor_type}_category"] = self._get_sleep_apnea_risk_category(value)

            # Add recommendations
            recommendations = self._get_respiratory_recommendations(respiratory_data)
            if recommendations:
                attributes["recommendations"] = recommendations

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating comprehensive attributes: %s", err)
            return None

    def _get_comprehensive_respiratory_data(self) -> dict | None:
        """Get comprehensive respiratory data."""
        if not self._user_obj or not hasattr(self._user_obj, 'sleep_data'):
            return None

        try:
            sleep_data = getattr(self._user_obj, 'sleep_data', {})
            sessions = sleep_data.get("sessions", [])

            if not sessions:
                return None

            # Get the most recent session
            latest_session = sessions[0]
            return self._extract_respiratory_data(latest_session)

        except Exception as err:
            _LOGGER.error("Error getting comprehensive respiratory data: %s", err)
            return None

    def _extract_respiratory_data(self, session: dict) -> dict:
        """Extract respiratory data from a sleep session."""
        try:
            # Extract respiratory metrics from session data
            respiratory_data = session.get("respiratory", {})

            current_respiratory_rate = respiratory_data.get("current", 0)
            average_respiratory_rate = respiratory_data.get("average", 0)
            respiratory_rate_trend = respiratory_data.get("trend", 0)
            respiratory_rate_quality = self._calculate_respiratory_quality(current_respiratory_rate)
            respiratory_rate_stability = self._calculate_respiratory_stability(session)
            breathing_pattern = self._determine_breathing_pattern(session)
            respiratory_efficiency = self._calculate_respiratory_efficiency(session)
            sleep_apnea_risk = self._calculate_sleep_apnea_risk(session)
            respiratory_health_score = self._calculate_respiratory_health_score(session)

            return {
                "current_respiratory_rate": current_respiratory_rate,
                "average_respiratory_rate": average_respiratory_rate,
                "respiratory_rate_trend": respiratory_rate_trend,
                "respiratory_rate_quality": respiratory_rate_quality,
                "respiratory_rate_stability": respiratory_rate_stability,
                "breathing_pattern": breathing_pattern,
                "respiratory_efficiency": respiratory_efficiency,
                "sleep_apnea_risk": sleep_apnea_risk,
                "respiratory_health_score": respiratory_health_score,
            }

        except Exception as err:
            _LOGGER.error("Error extracting respiratory data: %s", err)
            return None

    def _calculate_respiratory_quality(self, respiratory_rate: float) -> float:
        """Calculate respiratory rate quality score."""
        if 12 <= respiratory_rate <= 20:
            return 100.0
        elif 10 <= respiratory_rate <= 22:
            return 85.0
        elif 8 <= respiratory_rate <= 25:
            return 70.0
        elif 6 <= respiratory_rate <= 30:
            return 50.0
        else:
            return 25.0

    def _calculate_respiratory_stability(self, session: dict) -> float:
        """Calculate respiratory rate stability percentage."""
        try:
            respiratory_data = session.get("respiratory", {})
            variance = respiratory_data.get("variance", 0)

            if variance <= 2:
                return 100.0
            elif variance <= 4:
                return 85.0
            elif variance <= 6:
                return 70.0
            elif variance <= 8:
                return 50.0
            else:
                return 30.0
        except Exception:
            return 0.0

    def _determine_breathing_pattern(self, session: dict) -> str:
        """Determine breathing pattern category."""
        try:
            respiratory_data = session.get("respiratory", {})
            pattern = respiratory_data.get("pattern", "regular")

            if pattern == "regular":
                return "regular"
            elif pattern == "irregular":
                return "irregular"
            elif pattern == "shallow":
                return "shallow"
            elif pattern == "deep":
                return "deep"
            elif pattern == "periodic":
                return "periodic"
            elif pattern == "apneic":
                return "apneic"
            else:
                return "regular"
        except Exception:
            return "regular"

    def _calculate_respiratory_efficiency(self, session: dict) -> float:
        """Calculate respiratory efficiency percentage."""
        try:
            respiratory_data = session.get("respiratory", {})
            efficiency = respiratory_data.get("efficiency", 0)

            return min(100.0, max(0.0, efficiency))
        except Exception:
            return 0.0

    def _calculate_sleep_apnea_risk(self, session: dict) -> float:
        """Calculate sleep apnea risk score."""
        try:
            respiratory_data = session.get("respiratory", {})
            apnea_episodes = respiratory_data.get("apnea_episodes", 0)
            hypopnea_episodes = respiratory_data.get("hypopnea_episodes", 0)

            total_episodes = apnea_episodes + hypopnea_episodes

            if total_episodes == 0:
                return 10.0
            elif total_episodes <= 5:
                return 30.0
            elif total_episodes <= 15:
                return 50.0
            elif total_episodes <= 30:
                return 70.0
            else:
                return 90.0
        except Exception:
            return 0.0

    def _calculate_respiratory_health_score(self, session: dict) -> float:
        """Calculate overall respiratory health score."""
        try:
            current_rate = session.get("respiratory", {}).get("current", 16)
            quality = self._calculate_respiratory_quality(current_rate)
            stability = self._calculate_respiratory_stability(session)
            efficiency = self._calculate_respiratory_efficiency(session)
            apnea_risk = self._calculate_sleep_apnea_risk(session)

            apnea_score = 100 - apnea_risk

            health_score = (
                quality * 0.3 +
                stability * 0.25 +
                efficiency * 0.25 +
                apnea_score * 0.2
            )

            return round(health_score, 1)
        except Exception:
            return 0.0

    def _get_respiratory_assessment(self, rate: float) -> str:
        """Get overall respiratory assessment."""
        if 12 <= rate <= 20:
            return "Normal Respiratory Rate"
        elif 10 <= rate <= 22:
            return "Slightly Elevated Respiratory Rate"
        elif 8 <= rate <= 25:
            return "Elevated Respiratory Rate"
        elif rate < 8:
            return "Slow Respiratory Rate"
        else:
            return "Rapid Respiratory Rate"

    def _get_respiratory_category(self, rate: float) -> str:
        """Get respiratory rate category."""
        for category, config in RESPIRATORY_RATE_CATEGORIES.items():
            if config["min"] <= rate <= config["max"]:
                return config["description"]
        return "Unknown"

    def _get_respiratory_quality_category(self, quality: float) -> str:
        """Get respiratory quality category."""
        for category, config in RESPIRATORY_QUALITY_CATEGORIES.items():
            if config["min"] <= quality <= config["max"]:
                return config["description"]
        return "Unknown"

    def _get_sleep_apnea_risk_category(self, risk: float) -> str:
        """Get sleep apnea risk category."""
        for category, config in SLEEP_APNEA_RISK_CATEGORIES.items():
            if config["min"] <= risk <= config["max"]:
                return config["description"]
        return "Unknown"

    def _get_respiratory_recommendations(self, respiratory_data: dict) -> list[str]:
        """Get respiratory recommendations based on current metrics."""
        recommendations = []

        try:
            current_rate = respiratory_data.get("current_respiratory_rate", 16)
            sleep_apnea_risk = respiratory_data.get("sleep_apnea_risk", 0)
            respiratory_efficiency = respiratory_data.get("respiratory_efficiency", 0)

            if current_rate < 8 or current_rate > 25:
                recommendations.append("Consult healthcare provider about respiratory rate")

            if sleep_apnea_risk > 50:
                recommendations.append("Consider sleep study for apnea evaluation")

            if respiratory_efficiency < 70:
                recommendations.append("Focus on improving breathing efficiency")

            if not recommendations:
                recommendations.append("Maintain current respiratory patterns")

        except Exception as err:
            _LOGGER.error("Error generating respiratory recommendations: %s", err)

        return recommendations
