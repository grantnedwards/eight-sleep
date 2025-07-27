"""Heart rate variability sensors for Eight Sleep."""

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

# Heart rate variability sensor types
HRV_SENSORS = {
    "current_hrv": {
        "name": "Current Heart Rate Variability",
        "unit": "ms",
        "device_class": None,
        "icon": "mdi:heart-pulse",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "average_hrv": {
        "name": "Average Heart Rate Variability",
        "unit": "ms",
        "device_class": None,
        "icon": "mdi:heart-pulse",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "hrv_trend": {
        "name": "Heart Rate Variability Trend",
        "unit": "ms",
        "device_class": None,
        "icon": "mdi:trending-up",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "hrv_quality": {
        "name": "Heart Rate Variability Quality",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:heart-check",
        "state_class": None,
    },
    "hrv_stability": {
        "name": "Heart Rate Variability Stability",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:heart-stable",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "hrv_recovery": {
        "name": "Heart Rate Variability Recovery",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:heart-plus",
        "state_class": None,
    },
    "hrv_stress_index": {
        "name": "Heart Rate Variability Stress Index",
        "unit": None,
        "device_class": None,
        "icon": "mdi:heart-alert",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "hrv_balance": {
        "name": "Heart Rate Variability Balance",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:heart-balance",
        "state_class": None,
    },
}

# HRV quality categories
HRV_QUALITY_CATEGORIES = {
    "excellent": {"min": 100, "max": 200, "description": "Excellent (> 100ms)"},
    "good": {"min": 70, "max": 99, "description": "Good (70-99ms)"},
    "fair": {"min": 50, "max": 69, "description": "Fair (50-69ms)"},
    "poor": {"min": 30, "max": 49, "description": "Poor (30-49ms)"},
    "very_poor": {"min": 0, "max": 29, "description": "Very Poor (< 30ms)"},
}

# HRV stress index categories
HRV_STRESS_CATEGORIES = {
    "low": {"min": 0, "max": 30, "description": "Low Stress"},
    "moderate": {"min": 31, "max": 60, "description": "Moderate Stress"},
    "high": {"min": 61, "max": 80, "description": "High Stress"},
    "very_high": {"min": 81, "max": 100, "description": "Very High Stress"},
}

# HRV recovery categories
HRV_RECOVERY_CATEGORIES = {
    "excellent": {"min": 80, "max": 100, "description": "Excellent Recovery"},
    "good": {"min": 60, "max": 79, "description": "Good Recovery"},
    "fair": {"min": 40, "max": 59, "description": "Fair Recovery"},
    "poor": {"min": 20, "max": 39, "description": "Poor Recovery"},
    "very_poor": {"min": 0, "max": 19, "description": "Very Poor Recovery"},
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep heart rate variability sensors."""
    config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    eight = config_entry_data.api

    entities = []

    # Create HRV sensors for each user
    for user in eight.users.values():
        for sensor_type in HRV_SENSORS:
            entities.append(
                EightSleepHRVSensor(
                    entry,
                    config_entry_data.user_coordinator,
                    eight,
                    user,
                    sensor_type,
                )
            )

        # Create comprehensive HRV sensor
        entities.append(
            EightSleepComprehensiveHRVSensor(
                entry,
                config_entry_data.user_coordinator,
                eight,
                user,
            )
        )

    async_add_entities(entities)

class EightSleepHRVSensor(EightSleepBaseEntity, SensorEntity):
    """Individual heart rate variability sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        sensor_type: str,
    ) -> None:
        """Initialize the HRV sensor."""
        super().__init__(
            entry, coordinator, eight, user, f"hrv_{sensor_type}"
        )

        self._sensor_type = sensor_type
        self._sensor_config = HRV_SENSORS[sensor_type]

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
        """Return the current HRV value."""
        if not self.coordinator.data:
            return None

        try:
            hrv_data = self._get_hrv_data()
            if hrv_data is None:
                return None

            value = hrv_data.get(self._sensor_type)
            if value is None:
                return None

            if self._sensor_type == "hrv_quality":
                return self._get_hrv_quality_category(value)
            elif self._sensor_type == "hrv_recovery":
                return self._get_hrv_recovery_category(value)
            elif self._sensor_type == "hrv_stress_index":
                return self._get_hrv_stress_category(value)
            elif self._sensor_type == "hrv_balance":
                return self._get_hrv_balance_assessment(value)
            else:
                return round(float(value), 2)

        except Exception as err:
            _LOGGER.error("Error getting HRV data for %s: %s", self._attr_unique_id, err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None

        try:
            hrv_data = self._get_hrv_data()
            if hrv_data is None:
                return None

            attributes = {
                "sensor_type": self._sensor_type,
                "last_updated": datetime.now().isoformat(),
            }

            # Add HRV-specific attributes
            if self._sensor_type == "current_hrv":
                value = hrv_data.get(self._sensor_type)
                if value is not None:
                    attributes["hrv_quality"] = self._get_hrv_quality_category(value)
                    attributes["hrv_category"] = self._get_hrv_category(value)
                    attributes["is_optimal_hrv"] = 70 <= value <= 100

            elif self._sensor_type == "average_hrv":
                value = hrv_data.get(self._sensor_type)
                if value is not None:
                    attributes["average_hrv_trend"] = hrv_data.get("hrv_trend", 0)
                    attributes["hrv_consistency"] = hrv_data.get("hrv_consistency", 0)

            elif self._sensor_type == "hrv_trend":
                value = hrv_data.get(self._sensor_type)
                if value is not None:
                    attributes["trend_direction"] = "improving" if value > 0 else "declining" if value < 0 else "stable"
                    attributes["trend_magnitude"] = abs(value)

            elif self._sensor_type == "hrv_stability":
                value = hrv_data.get(self._sensor_type)
                if value is not None:
                    attributes["stability_category"] = self._get_stability_category(value)
                    attributes["hrv_variance"] = hrv_data.get("hrv_variance", 0)

            elif self._sensor_type == "hrv_stress_index":
                value = hrv_data.get(self._sensor_type)
                if value is not None:
                    attributes["stress_level"] = self._get_hrv_stress_category(value)
                    attributes["recovery_needed"] = value > 60

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating attributes for %s: %s", self._attr_unique_id, err)
            return None

    def _get_hrv_data(self) -> dict | None:
        """Get HRV data from the user."""
        if not self._user_obj or not hasattr(self._user_obj, 'sleep_data'):
            return None

        try:
            sleep_data = getattr(self._user_obj, 'sleep_data', {})
            sessions = sleep_data.get("sessions", [])

            if not sessions:
                return None

            # Get the most recent session
            latest_session = sessions[0]
            return self._extract_hrv_data(latest_session)

        except Exception as err:
            _LOGGER.error("Error getting HRV data: %s", err)
            return None

    def _extract_hrv_data(self, session: dict) -> dict:
        """Extract HRV data from a sleep session."""
        try:
            # Extract HRV metrics from session data
            hrv_data = session.get("hrv", {})

            current_hrv = hrv_data.get("current", 0)
            average_hrv = hrv_data.get("average", 0)
            hrv_trend = hrv_data.get("trend", 0)
            hrv_quality = self._calculate_hrv_quality(current_hrv)
            hrv_stability = self._calculate_hrv_stability(session)
            hrv_recovery = self._calculate_hrv_recovery(session)
            hrv_stress_index = self._calculate_hrv_stress_index(session)
            hrv_balance = self._calculate_hrv_balance(session)

            return {
                "current_hrv": current_hrv,
                "average_hrv": average_hrv,
                "hrv_trend": hrv_trend,
                "hrv_quality": hrv_quality,
                "hrv_stability": hrv_stability,
                "hrv_recovery": hrv_recovery,
                "hrv_stress_index": hrv_stress_index,
                "hrv_balance": hrv_balance,
                "hrv_consistency": self._calculate_hrv_consistency(session),
                "hrv_variance": self._calculate_hrv_variance(session),
            }

        except Exception as err:
            _LOGGER.error("Error extracting HRV data: %s", err)
            return None

    def _calculate_hrv_quality(self, hrv_value: float) -> float:
        """Calculate HRV quality score."""
        if hrv_value >= 100:
            return 100.0
        elif hrv_value >= 70:
            return 85.0
        elif hrv_value >= 50:
            return 70.0
        elif hrv_value >= 30:
            return 50.0
        else:
            return 25.0

    def _calculate_hrv_stability(self, session: dict) -> float:
        """Calculate HRV stability percentage."""
        try:
            # This would typically analyze HRV variance over time
            # For now, use a simplified calculation
            hrv_data = session.get("hrv", {})
            variance = hrv_data.get("variance", 0)

            if variance <= 5:
                return 100.0
            elif variance <= 10:
                return 85.0
            elif variance <= 15:
                return 70.0
            elif variance <= 20:
                return 50.0
            else:
                return 30.0
        except Exception:
            return 0.0

    def _calculate_hrv_recovery(self, session: dict) -> float:
        """Calculate HRV recovery score."""
        try:
            # This would analyze HRV recovery patterns
            # For now, use a simplified calculation
            hrv_data = session.get("hrv", {})
            recovery_score = hrv_data.get("recovery", 0)

            if recovery_score >= 80:
                return 100.0
            elif recovery_score >= 60:
                return 85.0
            elif recovery_score >= 40:
                return 70.0
            elif recovery_score >= 20:
                return 50.0
            else:
                return 25.0
        except Exception:
            return 0.0

    def _calculate_hrv_stress_index(self, session: dict) -> float:
        """Calculate HRV stress index."""
        try:
            # This would analyze HRV patterns to determine stress
            # For now, use a simplified calculation
            hrv_data = session.get("hrv", {})
            stress_score = hrv_data.get("stress", 0)

            return min(100.0, max(0.0, stress_score))
        except Exception:
            return 0.0

    def _calculate_hrv_balance(self, session: dict) -> float:
        """Calculate HRV balance score."""
        try:
            # This would analyze HRV balance between sympathetic and parasympathetic
            # For now, use a simplified calculation
            hrv_data = session.get("hrv", {})
            balance_score = hrv_data.get("balance", 0)

            return min(100.0, max(0.0, balance_score))
        except Exception:
            return 0.0

    def _calculate_hrv_consistency(self, session: dict) -> float:
        """Calculate HRV consistency."""
        try:
            # This would analyze HRV consistency over time
            # For now, use a placeholder value
            return 85.0
        except Exception:
            return 0.0

    def _calculate_hrv_variance(self, session: dict) -> float:
        """Calculate HRV variance."""
        try:
            # This would calculate actual HRV variance
            # For now, use a placeholder value
            return 8.5
        except Exception:
            return 0.0

    def _get_hrv_quality_category(self, quality: float) -> str:
        """Get HRV quality category."""
        for category, config in HRV_QUALITY_CATEGORIES.items():
            if config["min"] <= quality <= config["max"]:
                return config["description"]
        return "Unknown"

    def _get_hrv_recovery_category(self, recovery: float) -> str:
        """Get HRV recovery category."""
        for category, config in HRV_RECOVERY_CATEGORIES.items():
            if config["min"] <= recovery <= config["max"]:
                return config["description"]
        return "Unknown"

    def _get_hrv_stress_category(self, stress: float) -> str:
        """Get HRV stress category."""
        for category, config in HRV_STRESS_CATEGORIES.items():
            if config["min"] <= stress <= config["max"]:
                return config["description"]
        return "Unknown"

    def _get_hrv_balance_assessment(self, balance: float) -> str:
        """Get HRV balance assessment."""
        if balance >= 80:
            return "Excellent Balance"
        elif balance >= 60:
            return "Good Balance"
        elif balance >= 40:
            return "Fair Balance"
        elif balance >= 20:
            return "Poor Balance"
        else:
            return "Very Poor Balance"

    def _get_hrv_category(self, hrv_value: float) -> str:
        """Get HRV category."""
        if hrv_value >= 100:
            return "Excellent"
        elif hrv_value >= 70:
            return "Good"
        elif hrv_value >= 50:
            return "Fair"
        elif hrv_value >= 30:
            return "Poor"
        else:
            return "Very Poor"

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

class EightSleepComprehensiveHRVSensor(EightSleepBaseEntity, SensorEntity):
    """Comprehensive heart rate variability sensor."""

    _attr_has_entity_name = True
    _attr_name = "Heart Rate Variability Analysis"
    _attr_icon = "mdi:heart-multiple"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
    ) -> None:
        """Initialize the comprehensive HRV sensor."""
        super().__init__(
            entry, coordinator, eight, user, "hrv_comprehensive"
        )

    @property
    def native_value(self) -> str | None:
        """Return the overall HRV assessment."""
        if not self.coordinator.data:
            return None

        try:
            hrv_data = self._get_comprehensive_hrv_data()
            if hrv_data is None:
                return "Unknown"

            current_hrv = hrv_data.get("current_hrv", 0)
            return self._get_hrv_assessment(current_hrv)

        except Exception as err:
            _LOGGER.error("Error getting comprehensive HRV data: %s", err)
            return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return detailed HRV attributes."""
        if not self.coordinator.data:
            return None

        try:
            hrv_data = self._get_comprehensive_hrv_data()
            if hrv_data is None:
                return None

            attributes = {
                "last_updated": datetime.now().isoformat(),
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            }

            # Add all HRV metrics
            for sensor_type, config in HRV_SENSORS.items():
                value = hrv_data.get(sensor_type)
                if value is not None:
                    attributes[f"{sensor_type}_value"] = value
                    if sensor_type == "current_hrv":
                        attributes[f"{sensor_type}_category"] = self._get_hrv_category(value)
                    elif sensor_type == "hrv_quality":
                        attributes[f"{sensor_type}_category"] = self._get_hrv_quality_category(value)
                    elif sensor_type == "hrv_stress_index":
                        attributes[f"{sensor_type}_category"] = self._get_hrv_stress_category(value)

            # Add recommendations
            recommendations = self._get_hrv_recommendations(hrv_data)
            if recommendations:
                attributes["recommendations"] = recommendations

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating comprehensive attributes: %s", err)
            return None

    def _get_comprehensive_hrv_data(self) -> dict | None:
        """Get comprehensive HRV data."""
        if not self._user_obj or not hasattr(self._user_obj, 'sleep_data'):
            return None

        try:
            sleep_data = getattr(self._user_obj, 'sleep_data', {})
            sessions = sleep_data.get("sessions", [])

            if not sessions:
                return None

            # Get the most recent session
            latest_session = sessions[0]
            return self._extract_hrv_data(latest_session)

        except Exception as err:
            _LOGGER.error("Error getting comprehensive HRV data: %s", err)
            return None

    def _extract_hrv_data(self, session: dict) -> dict:
        """Extract HRV data from a sleep session."""
        try:
            # Extract HRV metrics from session data
            hrv_data = session.get("hrv", {})

            current_hrv = hrv_data.get("current", 0)
            average_hrv = hrv_data.get("average", 0)
            hrv_trend = hrv_data.get("trend", 0)
            hrv_quality = self._calculate_hrv_quality(current_hrv)
            hrv_stability = self._calculate_hrv_stability(session)
            hrv_recovery = self._calculate_hrv_recovery(session)
            hrv_stress_index = self._calculate_hrv_stress_index(session)
            hrv_balance = self._calculate_hrv_balance(session)

            return {
                "current_hrv": current_hrv,
                "average_hrv": average_hrv,
                "hrv_trend": hrv_trend,
                "hrv_quality": hrv_quality,
                "hrv_stability": hrv_stability,
                "hrv_recovery": hrv_recovery,
                "hrv_stress_index": hrv_stress_index,
                "hrv_balance": hrv_balance,
            }

        except Exception as err:
            _LOGGER.error("Error extracting HRV data: %s", err)
            return None

    def _calculate_hrv_quality(self, hrv_value: float) -> float:
        """Calculate HRV quality score."""
        if hrv_value >= 100:
            return 100.0
        elif hrv_value >= 70:
            return 85.0
        elif hrv_value >= 50:
            return 70.0
        elif hrv_value >= 30:
            return 50.0
        else:
            return 25.0

    def _calculate_hrv_stability(self, session: dict) -> float:
        """Calculate HRV stability percentage."""
        try:
            hrv_data = session.get("hrv", {})
            variance = hrv_data.get("variance", 0)

            if variance <= 5:
                return 100.0
            elif variance <= 10:
                return 85.0
            elif variance <= 15:
                return 70.0
            elif variance <= 20:
                return 50.0
            else:
                return 30.0
        except Exception:
            return 0.0

    def _calculate_hrv_recovery(self, session: dict) -> float:
        """Calculate HRV recovery score."""
        try:
            hrv_data = session.get("hrv", {})
            recovery_score = hrv_data.get("recovery", 0)

            if recovery_score >= 80:
                return 100.0
            elif recovery_score >= 60:
                return 85.0
            elif recovery_score >= 40:
                return 70.0
            elif recovery_score >= 20:
                return 50.0
            else:
                return 25.0
        except Exception:
            return 0.0

    def _calculate_hrv_stress_index(self, session: dict) -> float:
        """Calculate HRV stress index."""
        try:
            hrv_data = session.get("hrv", {})
            stress_score = hrv_data.get("stress", 0)

            return min(100.0, max(0.0, stress_score))
        except Exception:
            return 0.0

    def _calculate_hrv_balance(self, session: dict) -> float:
        """Calculate HRV balance score."""
        try:
            hrv_data = session.get("hrv", {})
            balance_score = hrv_data.get("balance", 0)

            return min(100.0, max(0.0, balance_score))
        except Exception:
            return 0.0

    def _get_hrv_assessment(self, hrv_value: float) -> str:
        """Get overall HRV assessment."""
        if hrv_value >= 100:
            return "Excellent Heart Rate Variability"
        elif hrv_value >= 70:
            return "Good Heart Rate Variability"
        elif hrv_value >= 50:
            return "Fair Heart Rate Variability"
        elif hrv_value >= 30:
            return "Poor Heart Rate Variability"
        else:
            return "Very Poor Heart Rate Variability"

    def _get_hrv_category(self, hrv_value: float) -> str:
        """Get HRV category."""
        if hrv_value >= 100:
            return "Excellent"
        elif hrv_value >= 70:
            return "Good"
        elif hrv_value >= 50:
            return "Fair"
        elif hrv_value >= 30:
            return "Poor"
        else:
            return "Very Poor"

    def _get_hrv_quality_category(self, quality: float) -> str:
        """Get HRV quality category."""
        for category, config in HRV_QUALITY_CATEGORIES.items():
            if config["min"] <= quality <= config["max"]:
                return config["description"]
        return "Unknown"

    def _get_hrv_stress_category(self, stress: float) -> str:
        """Get HRV stress category."""
        for category, config in HRV_STRESS_CATEGORIES.items():
            if config["min"] <= stress <= config["max"]:
                return config["description"]
        return "Unknown"

    def _get_hrv_recommendations(self, hrv_data: dict) -> list[str]:
        """Get HRV recommendations based on current metrics."""
        recommendations = []

        try:
            current_hrv = hrv_data.get("current_hrv", 0)
            hrv_stress_index = hrv_data.get("hrv_stress_index", 0)
            hrv_recovery = hrv_data.get("hrv_recovery", 0)

            if current_hrv < 50:
                recommendations.append("Focus on improving heart rate variability")

            if hrv_stress_index > 60:
                recommendations.append("Work on reducing stress levels")

            if hrv_recovery < 60:
                recommendations.append("Improve recovery through better sleep and rest")

            if not recommendations:
                recommendations.append("Maintain current heart rate variability patterns")

        except Exception as err:
            _LOGGER.error("Error generating HRV recommendations: %s", err)

        return recommendations
