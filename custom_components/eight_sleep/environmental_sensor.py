"""Environmental monitoring sensors for Eight Sleep."""

from __future__ import annotations

import logging
from datetime import datetime
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
    UnitOfPressure,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import EightSleepBaseEntity, EightSleepConfigEntryData
from .const import DOMAIN
from .pyEight.eight import EightSleep
from .pyEight.user import EightUser

_LOGGER = logging.getLogger(__name__)

# Environmental sensor types
ENVIRONMENTAL_SENSORS = {
    "room_temperature": {
        "name": "Room Temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "icon": "mdi:thermometer",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "room_humidity": {
        "name": "Room Humidity",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.HUMIDITY,
        "icon": "mdi:water-percent",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "room_pressure": {
        "name": "Room Pressure",
        "unit": UnitOfPressure.HPA,
        "device_class": SensorDeviceClass.PRESSURE,
        "icon": "mdi:gauge",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "air_quality": {
        "name": "Air Quality",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:air-filter",
        "state_class": None,
    },
    "noise_level": {
        "name": "Noise Level",
        "unit": "dB",
        "device_class": None,
        "icon": "mdi:volume-high",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "light_level": {
        "name": "Light Level",
        "unit": "lux",
        "device_class": SensorDeviceClass.ILLUMINANCE,
        "icon": "mdi:lightbulb",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "co2_level": {
        "name": "CO2 Level",
        "unit": "ppm",
        "device_class": None,
        "icon": "mdi:molecule-co2",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "voc_level": {
        "name": "VOC Level",
        "unit": "ppb",
        "device_class": None,
        "icon": "mdi:air-purifier",
        "state_class": SensorStateClass.MEASUREMENT,
    },
}

# Air quality categories
AIR_QUALITY_CATEGORIES = {
    "excellent": {"min": 0, "max": 50, "color": "#00E400"},
    "good": {"min": 51, "max": 100, "color": "#FFFF00"},
    "moderate": {"min": 101, "max": 150, "color": "#FF7E00"},
    "poor": {"min": 151, "max": 200, "color": "#FF0000"},
    "very_poor": {"min": 201, "max": 300, "color": "#8F3F97"},
    "hazardous": {"min": 301, "max": 500, "color": "#7E0023"},
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep environmental sensors."""
    config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    eight = config_entry_data.api

    entities = []

    # Create environmental sensors for each user
    for user in eight.users.values():
        for sensor_type in ENVIRONMENTAL_SENSORS:
            entities.append(
                EightSleepEnvironmentalSensor(
                    entry,
                    config_entry_data.device_coordinator,
                    eight,
                    user,
                    sensor_type,
                )
            )

        # Create comprehensive environmental sensor
        entities.append(
            EightSleepComprehensiveEnvironmentalSensor(
                entry,
                config_entry_data.device_coordinator,
                eight,
                user,
            )
        )

    async_add_entities(entities)

class EightSleepEnvironmentalSensor(EightSleepBaseEntity, SensorEntity):
    """Individual environmental monitoring sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        sensor_type: str,
    ) -> None:
        """Initialize the environmental sensor."""
        super().__init__(
            entry, coordinator, eight, user, f"environmental_{sensor_type}"
        )

        self._sensor_type = sensor_type
        self._sensor_config = ENVIRONMENTAL_SENSORS[sensor_type]

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
        """Return the current environmental value."""
        if not self.coordinator.data:
            return None

        try:
            env_data = self._get_environmental_data()
            if env_data is None:
                return None

            value = env_data.get(self._sensor_type)
            if value is None:
                return None

            if self._sensor_type == "air_quality":
                return self._format_air_quality(value)
            else:
                return round(float(value), 2)

        except Exception as err:
            _LOGGER.error("Error getting environmental data for %s: %s", self._attr_unique_id, err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None

        try:
            env_data = self._get_environmental_data()
            if env_data is None:
                return None

            attributes = {
                "sensor_type": self._sensor_type,
                "last_updated": datetime.now().isoformat(),
            }

            # Add sensor-specific attributes
            if self._sensor_type == "air_quality":
                value = env_data.get(self._sensor_type)
                if value is not None:
                    attributes["air_quality_index"] = value
                    attributes["air_quality_category"] = self._get_air_quality_category(value)

            elif self._sensor_type == "room_temperature":
                value = env_data.get(self._sensor_type)
                if value is not None:
                    attributes["temperature_fahrenheit"] = round((value * 9/5) + 32, 2)

            elif self._sensor_type == "noise_level":
                value = env_data.get(self._sensor_type)
                if value is not None:
                    attributes["noise_level_category"] = self._get_noise_level_category(value)

            elif self._sensor_type == "light_level":
                value = env_data.get(self._sensor_type)
                if value is not None:
                    attributes["light_level_category"] = self._get_light_level_category(value)

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating attributes for %s: %s", self._attr_unique_id, err)
            return None

    def _get_environmental_data(self) -> dict | None:
        """Get environmental data from the device."""
        if not self._eight or not hasattr(self._eight, 'device_data'):
            return None

        try:
            device_data = self._eight.device_data
            if not device_data:
                return None

            # Extract environmental data from device data
            environmental_data = device_data.get("environmentalData", {})
            if not environmental_data:
                # Fallback to room temperature from the main device data
                room_temp = self._eight.room_temperature
                if room_temp is not None:
                    return {"room_temperature": room_temp}

            return environmental_data

        except Exception as err:
            _LOGGER.error("Error getting environmental data: %s", err)
            return None

    def _format_air_quality(self, aqi: float) -> str:
        """Format air quality index."""
        if aqi <= 50:
            return "Excellent"
        elif aqi <= 100:
            return "Good"
        elif aqi <= 150:
            return "Moderate"
        elif aqi <= 200:
            return "Poor"
        elif aqi <= 300:
            return "Very Poor"
        else:
            return "Hazardous"

    def _get_air_quality_category(self, aqi: float) -> str:
        """Get air quality category."""
        for category, config in AIR_QUALITY_CATEGORIES.items():
            if config["min"] <= aqi <= config["max"]:
                return category
        return "unknown"

    def _get_noise_level_category(self, noise_level: float) -> str:
        """Get noise level category."""
        if noise_level <= 30:
            return "Very Quiet"
        elif noise_level <= 50:
            return "Quiet"
        elif noise_level <= 70:
            return "Moderate"
        elif noise_level <= 85:
            return "Loud"
        else:
            return "Very Loud"

    def _get_light_level_category(self, light_level: float) -> str:
        """Get light level category."""
        if light_level <= 10:
            return "Very Dark"
        elif light_level <= 50:
            return "Dark"
        elif light_level <= 200:
            return "Dim"
        elif light_level <= 1000:
            return "Normal"
        elif light_level <= 5000:
            return "Bright"
        else:
            return "Very Bright"

class EightSleepComprehensiveEnvironmentalSensor(EightSleepBaseEntity, SensorEntity):
    """Comprehensive environmental monitoring sensor."""

    _attr_has_entity_name = True
    _attr_name = "Environmental Conditions"
    _attr_icon = "mdi:home-thermometer"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
    ) -> None:
        """Initialize the comprehensive environmental sensor."""
        super().__init__(
            entry, coordinator, eight, user, "environmental_comprehensive"
        )

    @property
    def native_value(self) -> str | None:
        """Return the overall environmental assessment."""
        if not self.coordinator.data:
            return None

        try:
            env_data = self._get_comprehensive_environmental_data()
            if env_data is None:
                return "Unknown"

            return self._get_environmental_assessment(env_data)

        except Exception as err:
            _LOGGER.error("Error getting comprehensive environmental data: %s", err)
            return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return detailed environmental attributes."""
        if not self.coordinator.data:
            return None

        try:
            env_data = self._get_comprehensive_environmental_data()
            if env_data is None:
                return None

            attributes = {
                "last_updated": datetime.now().isoformat(),
                "assessment_date": datetime.now().strftime("%Y-%m-%d"),
            }

            # Add all environmental metrics
            for sensor_type, config in ENVIRONMENTAL_SENSORS.items():
                value = env_data.get(sensor_type)
                if value is not None:
                    attributes[f"{sensor_type}_value"] = value
                    if sensor_type == "air_quality":
                        attributes[f"{sensor_type}_category"] = self._get_air_quality_category(value)
                    elif sensor_type == "noise_level":
                        attributes[f"{sensor_type}_category"] = self._get_noise_level_category(value)
                    elif sensor_type == "light_level":
                        attributes[f"{sensor_type}_category"] = self._get_light_level_category(value)

            # Add recommendations
            recommendations = self._get_environmental_recommendations(env_data)
            if recommendations:
                attributes["recommendations"] = recommendations

            return attributes

        except Exception as err:
            _LOGGER.error("Error calculating comprehensive attributes: %s", err)
            return None

    def _get_comprehensive_environmental_data(self) -> dict | None:
        """Get comprehensive environmental data."""
        if not self._eight or not hasattr(self._eight, 'device_data'):
            return None

        try:
            device_data = self._eight.device_data
            if not device_data:
                return None

            environmental_data = device_data.get("environmentalData", {})
            if not environmental_data:
                # Fallback to basic environmental data
                room_temp = self._eight.room_temperature
                if room_temp is not None:
                    return {"room_temperature": room_temp}

            return environmental_data

        except Exception as err:
            _LOGGER.error("Error getting comprehensive environmental data: %s", err)
            return None

    def _get_environmental_assessment(self, env_data: dict) -> str:
        """Get overall environmental assessment."""
        # Simple assessment based on available data
        issues = []

        temp = env_data.get("room_temperature")
        if temp is not None:
            if temp < 16 or temp > 26:
                issues.append("temperature")

        humidity = env_data.get("room_humidity")
        if humidity is not None:
            if humidity < 30 or humidity > 60:
                issues.append("humidity")

        air_quality = env_data.get("air_quality")
        if air_quality is not None and air_quality > 100:
            issues.append("air_quality")

        noise = env_data.get("noise_level")
        if noise is not None and noise > 70:
            issues.append("noise")

        if not issues:
            return "Optimal"
        elif len(issues) == 1:
            return f"Good ({issues[0].replace('_', ' ').title()} needs attention)"
        else:
            return f"Needs Improvement ({len(issues)} issues)"

    def _get_air_quality_category(self, aqi: float) -> str:
        """Get air quality category."""
        for category, config in AIR_QUALITY_CATEGORIES.items():
            if config["min"] <= aqi <= config["max"]:
                return category
        return "unknown"

    def _get_noise_level_category(self, noise_level: float) -> str:
        """Get noise level category."""
        if noise_level <= 30:
            return "Very Quiet"
        elif noise_level <= 50:
            return "Quiet"
        elif noise_level <= 70:
            return "Moderate"
        elif noise_level <= 85:
            return "Loud"
        else:
            return "Very Loud"

    def _get_light_level_category(self, light_level: float) -> str:
        """Get light level category."""
        if light_level <= 10:
            return "Very Dark"
        elif light_level <= 50:
            return "Dark"
        elif light_level <= 200:
            return "Dim"
        elif light_level <= 1000:
            return "Normal"
        elif light_level <= 5000:
            return "Bright"
        else:
            return "Very Bright"

    def _get_environmental_recommendations(self, env_data: dict) -> list[str]:
        """Get environmental recommendations based on current conditions."""
        recommendations = []

        try:
            temp = env_data.get("room_temperature")
            humidity = env_data.get("room_humidity")
            air_quality = env_data.get("air_quality")
            noise = env_data.get("noise_level")
            light = env_data.get("light_level")

            if temp is not None:
                if temp < 16:
                    recommendations.append("Consider increasing room temperature")
                elif temp > 26:
                    recommendations.append("Consider decreasing room temperature")

            if humidity is not None:
                if humidity < 30:
                    recommendations.append("Consider using a humidifier")
                elif humidity > 60:
                    recommendations.append("Consider using a dehumidifier")

            if air_quality is not None and air_quality > 100:
                recommendations.append("Consider improving air ventilation")

            if noise is not None and noise > 70:
                recommendations.append("Consider reducing noise levels")

            if light is not None and light > 1000:
                recommendations.append("Consider reducing light levels for better sleep")

            if not recommendations:
                recommendations.append("Environmental conditions are optimal for sleep")

        except Exception as err:
            _LOGGER.error("Error generating environmental recommendations: %s", err)

        return recommendations
