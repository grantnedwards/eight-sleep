"""Device health sensors for Eight Sleep."""

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
    UnitOfTemperature,
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

# Device health sensor types
DEVICE_HEALTH_SENSORS = {
    "water_level": {
        "name": "Water Level",
        "unit": PERCENTAGE,
        "device_class": None,
        "icon": "mdi:water",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "priming_status": {
        "name": "Priming Status",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:water-sync",
        "state_class": None,
    },
    "device_temperature": {
        "name": "Device Temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "icon": "mdi:thermometer",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "firmware_version": {
        "name": "Firmware Version",
        "unit": None,
        "device_class": None,
        "icon": "mdi:chip",
        "state_class": None,
    },
    "hardware_version": {
        "name": "Hardware Version",
        "unit": None,
        "device_class": None,
        "icon": "mdi:cog",
        "state_class": None,
    },
    "last_maintenance": {
        "name": "Last Maintenance",
        "unit": UnitOfTime.DAYS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:wrench",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "device_uptime": {
        "name": "Device Uptime",
        "unit": UnitOfTime.DAYS,
        "device_class": SensorDeviceClass.DURATION,
        "icon": "mdi:clock-outline",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "error_count": {
        "name": "Error Count",
        "unit": "count",
        "device_class": None,
        "icon": "mdi:alert-circle",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "connection_quality": {
        "name": "Connection Quality",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:wifi",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "battery_level": {
        "name": "Battery Level",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "icon": "mdi:battery",
        "state_class": SensorStateClass.MEASUREMENT,
    },
}

# Priming status categories
PRIMING_STATUS_CATEGORIES = {
    "not_needed": "Not Needed",
    "in_progress": "In Progress",
    "completed": "Completed",
    "failed": "Failed",
    "scheduled": "Scheduled",
}

# Connection quality categories
CONNECTION_QUALITY_CATEGORIES = {
    "excellent": {"min": 90, "max": 100, "color": "#4CAF50"},
    "good": {"min": 70, "max": 89, "color": "#8BC34A"},
    "fair": {"min": 50, "max": 69, "color": "#FFC107"},
    "poor": {"min": 30, "max": 49, "color": "#FF9800"},
    "very_poor": {"min": 0, "max": 29, "color": "#F44336"},
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep device health sensors."""
    config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    eight = config_entry_data.api

    entities = []

    # Create device health sensors for the main device
    for sensor_type in DEVICE_HEALTH_SENSORS:
        entities.append(
            EightSleepDeviceHealthSensor(
                entry,
                config_entry_data.device_coordinator,
                eight,
                None,  # No user for device-level sensors
                sensor_type,
            )
        )

    # Create comprehensive device health sensor
    entities.append(
        EightSleepComprehensiveDeviceHealthSensor(
            entry,
            config_entry_data.device_coordinator,
            eight,
            None,  # No user for device-level sensors
        )
    )

    async_add_entities(entities)

class EightSleepDeviceHealthSensor(EightSleepBaseEntity, SensorEntity):
    """Individual device health monitoring sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser | None,
        sensor_type: str,
    ) -> None:
        """Initialize the device health sensor."""
        super().__init__(
            entry, coordinator, eight, user, f"device_health_{sensor_type}"
        )

        self._sensor_type = sensor_type
        self._sensor_config = DEVICE_HEALTH_SENSORS[sensor_type]

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
        """Return the current device health value."""
        if not self.coordinator.data:
            return None

        try:
            health_data = self._get_device_health_data()
            if health_data is None:
                return None

            value = health_data.get(self._sensor_type)
            if value is None:
                return None

            if self._sensor_type == "priming_status":
                return self._format_priming_status(value)
            elif self._sensor_type == "connection_quality":
                return self._format_connection_quality(value)
            elif self._sensor_type == "firmware_version":
                return str(value)
            elif self._sensor_type == "hardware_version":
                return str(value)
            else:
                return round(float(value), 2)

        except Exception as err:
            _LOGGER.error("Error getting device health data for %s: %s", self._attr_unique_id, err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None

        try:
            health_data = self._get_device_health_data()
            if health_data is None:
                return None

            attributes = {
                "sensor_type": self._sensor_type,
                "last_updated": datetime.now().isoformat(),
            }

            # Add sensor-specific attributes
            if self._sensor_type == "water_level":
                value = health_data.get(self._sensor_type)
                if value is not None:
                    attributes["water_level_category"] = self._get_water_level_category(value)
                    attributes["needs_refill"] = value < 20

            elif self._sensor_type == "priming_status":
                value = health_data.get(self._sensor_type)
                if value is not None:
                    attributes["priming_progress"] = health_data.get("priming_progress", 0)
                    attributes["priming_duration"] = health_data.get("priming_duration", 0)

            elif self._sensor_type == "connection_quality":
                value = health_data.get(self._sensor_type)
                if value is not None:
                    attributes["connection_category"] = self._get_connection_quality_category(value)
                    attributes["signal_strength"] = health_data.get("signal_strength", 0)

            elif self._sensor_type == "device_temperature":
                value = health_data.get(self._sensor_type)
                if value is not None:
                    attributes["temperature_fahrenheit"] = round((value * 9/5) + 32, 2)
                    attributes["temperature_status"] = self._get_temperature_status(value)

            elif self._sensor_type == "error_count":
                value = health_data.get(self._sensor_type)
                if value is not None:
                    attributes["error_types"] = health_data.get("error_types", [])
                    attributes["last_error"] = health_data.get("last_error", None)

            elif self._sensor_type == "battery_level":
                value = health_data.get(self._sensor_type)
                if value is not None:
                    attributes["battery_status"] = self._get_battery_status(value)
                    attributes["charging"] = health_data.get("charging", False)

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating attributes for %s: %s", self._attr_unique_id, err)
            return None

    def _get_device_health_data(self) -> dict | None:
        """Get device health data from the device."""
        if not self._eight or not hasattr(self._eight, 'device_data'):
            return None

        try:
            device_data = self._eight.device_data
            if not device_data:
                return None

            # Extract device health data
            health_data = {
                "water_level": self._eight.has_water,
                "priming_status": self._get_priming_status(),
                "device_temperature": device_data.get("temperature"),
                "firmware_version": device_data.get("firmwareVersion"),
                "hardware_version": device_data.get("sensorInfo", {}).get("hwRevision"),
                "last_maintenance": self._calculate_last_maintenance(),
                "device_uptime": self._calculate_device_uptime(),
                "error_count": self._get_error_count(),
                "connection_quality": self._get_connection_quality(),
                "battery_level": self._get_battery_level(),
            }

            return health_data

        except Exception as err:
            _LOGGER.error("Error getting device health data: %s", err)
            return None

    def _get_priming_status(self) -> str:
        """Get the current priming status."""
        if self._eight.need_priming:
            return "needed"
        elif self._eight.is_priming:
            return "in_progress"
        else:
            return "not_needed"

    def _format_priming_status(self, status: str) -> str:
        """Format priming status for display."""
        return PRIMING_STATUS_CATEGORIES.get(status, "Unknown")

    def _get_connection_quality(self) -> float:
        """Get connection quality percentage."""
        # This would typically come from device data
        # For now, return a placeholder value
        return 85.0

    def _format_connection_quality(self, quality: float) -> str:
        """Format connection quality."""
        if quality >= 90:
            return "Excellent"
        elif quality >= 70:
            return "Good"
        elif quality >= 50:
            return "Fair"
        elif quality >= 30:
            return "Poor"
        else:
            return "Very Poor"

    def _get_connection_quality_category(self, quality: float) -> str:
        """Get connection quality category."""
        for category, config in CONNECTION_QUALITY_CATEGORIES.items():
            if config["min"] <= quality <= config["max"]:
                return category
        return "unknown"

    def _get_water_level_category(self, level: float) -> str:
        """Get water level category."""
        if level >= 80:
            return "Full"
        elif level >= 60:
            return "Good"
        elif level >= 40:
            return "Medium"
        elif level >= 20:
            return "Low"
        else:
            return "Critical"

    def _get_temperature_status(self, temp: float) -> str:
        """Get device temperature status."""
        if temp < 0 or temp > 50:
            return "Critical"
        elif temp < 10 or temp > 40:
            return "Warning"
        else:
            return "Normal"

    def _get_battery_status(self, level: float) -> str:
        """Get battery status."""
        if level >= 80:
            return "Full"
        elif level >= 60:
            return "Good"
        elif level >= 40:
            return "Medium"
        elif level >= 20:
            return "Low"
        else:
            return "Critical"

    def _calculate_last_maintenance(self) -> float | None:
        """Calculate days since last maintenance."""
        # This would typically come from device data
        # For now, return a placeholder value
        return 30.0

    def _calculate_device_uptime(self) -> float | None:
        """Calculate device uptime in days."""
        # This would typically come from device data
        # For now, return a placeholder value
        return 15.0

    def _get_error_count(self) -> int:
        """Get the number of recent errors."""
        # This would typically come from device data
        # For now, return a placeholder value
        return 0

    def _get_battery_level(self) -> float | None:
        """Get battery level percentage."""
        # This would typically come from device data
        # For now, return a placeholder value
        return 95.0

class EightSleepComprehensiveDeviceHealthSensor(EightSleepBaseEntity, SensorEntity):
    """Comprehensive device health monitoring sensor."""

    _attr_has_entity_name = True
    _attr_name = "Device Health Status"
    _attr_icon = "mdi:heart-pulse"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser | None,
    ) -> None:
        """Initialize the comprehensive device health sensor."""
        super().__init__(
            entry, coordinator, eight, user, "device_health_comprehensive"
        )

    @property
    def native_value(self) -> str | None:
        """Return the overall device health assessment."""
        if not self.coordinator.data:
            return None

        try:
            health_data = self._get_comprehensive_health_data()
            if health_data is None:
                return "Unknown"

            return self._get_device_health_assessment(health_data)

        except Exception as err:
            _LOGGER.error("Error getting comprehensive device health: %s", err)
            return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return detailed device health attributes."""
        if not self.coordinator.data:
            return None

        try:
            health_data = self._get_comprehensive_health_data()
            if health_data is None:
                return None

            attributes = {
                "last_updated": datetime.now().isoformat(),
                "assessment_date": datetime.now().strftime("%Y-%m-%d"),
            }

            # Add all health metrics
            for sensor_type, config in DEVICE_HEALTH_SENSORS.items():
                value = health_data.get(sensor_type)
                if value is not None:
                    attributes[f"{sensor_type}_value"] = value
                    if sensor_type == "water_level":
                        attributes[f"{sensor_type}_category"] = self._get_water_level_category(value)
                    elif sensor_type == "connection_quality":
                        attributes[f"{sensor_type}_category"] = self._get_connection_quality_category(value)
                    elif sensor_type == "battery_level":
                        attributes[f"{sensor_type}_status"] = self._get_battery_status(value)

            # Add recommendations
            recommendations = self._get_device_health_recommendations(health_data)
            if recommendations:
                attributes["recommendations"] = recommendations

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating comprehensive attributes: %s", err)
            return None

    def _get_comprehensive_health_data(self) -> dict | None:
        """Get comprehensive device health data."""
        if not self._eight or not hasattr(self._eight, 'device_data'):
            return None

        try:
            device_data = self._eight.device_data
            if not device_data:
                return None

            health_data = {
                "water_level": 100 if self._eight.has_water else 50,  # Simplified
                "priming_status": self._get_priming_status(),
                "device_temperature": device_data.get("temperature", 25),
                "firmware_version": device_data.get("firmwareVersion", "Unknown"),
                "hardware_version": device_data.get("sensorInfo", {}).get("hwRevision", "Unknown"),
                "last_maintenance": 30.0,  # Placeholder
                "device_uptime": 15.0,  # Placeholder
                "error_count": 0,  # Placeholder
                "connection_quality": 85.0,  # Placeholder
                "battery_level": 95.0,  # Placeholder
            }

            return health_data

        except Exception as err:
            _LOGGER.error("Error getting comprehensive health data: %s", err)
            return None

    def _get_priming_status(self) -> str:
        """Get the current priming status."""
        if self._eight.need_priming:
            return "needed"
        elif self._eight.is_priming:
            return "in_progress"
        else:
            return "not_needed"

    def _get_device_health_assessment(self, health_data: dict) -> str:
        """Get overall device health assessment."""
        issues = []

        water_level = health_data.get("water_level")
        if water_level is not None and water_level < 20:
            issues.append("water_level")

        priming_status = health_data.get("priming_status")
        if priming_status == "needed":
            issues.append("priming")

        device_temp = health_data.get("device_temperature")
        if device_temp is not None and (device_temp < 0 or device_temp > 50):
            issues.append("temperature")

        connection_quality = health_data.get("connection_quality")
        if connection_quality is not None and connection_quality < 50:
            issues.append("connection")

        battery_level = health_data.get("battery_level")
        if battery_level is not None and battery_level < 20:
            issues.append("battery")

        if not issues:
            return "Excellent"
        elif len(issues) == 1:
            return f"Good ({issues[0].replace('_', ' ').title()} needs attention)"
        else:
            return f"Needs Maintenance ({len(issues)} issues)"

    def _get_water_level_category(self, level: float) -> str:
        """Get water level category."""
        if level >= 80:
            return "Full"
        elif level >= 60:
            return "Good"
        elif level >= 40:
            return "Medium"
        elif level >= 20:
            return "Low"
        else:
            return "Critical"

    def _get_connection_quality_category(self, quality: float) -> str:
        """Get connection quality category."""
        for category, config in CONNECTION_QUALITY_CATEGORIES.items():
            if config["min"] <= quality <= config["max"]:
                return category
        return "unknown"

    def _get_battery_status(self, level: float) -> str:
        """Get battery status."""
        if level >= 80:
            return "Full"
        elif level >= 60:
            return "Good"
        elif level >= 40:
            return "Medium"
        elif level >= 20:
            return "Low"
        else:
            return "Critical"

    def _get_device_health_recommendations(self, health_data: dict) -> list[str]:
        """Get device health recommendations based on current conditions."""
        recommendations = []

        try:
            water_level = health_data.get("water_level")
            priming_status = health_data.get("priming_status")
            device_temp = health_data.get("device_temperature")
            connection_quality = health_data.get("connection_quality")
            battery_level = health_data.get("battery_level")

            if water_level is not None and water_level < 20:
                recommendations.append("Refill water tank soon")

            if priming_status == "needed":
                recommendations.append("Run priming cycle")

            if device_temp is not None and (device_temp < 0 or device_temp > 50):
                recommendations.append("Check device temperature")

            if connection_quality is not None and connection_quality < 50:
                recommendations.append("Check device connection")

            if battery_level is not None and battery_level < 20:
                recommendations.append("Check device power")

            if not recommendations:
                recommendations.append("Device is operating normally")

        except Exception as err:
            _LOGGER.error("Error generating device health recommendations: %s", err)

        return recommendations
