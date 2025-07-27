"""Support for Eight Sleep Device Monitoring sensors."""

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

# Device Monitoring Sensor Types
DEVICE_MONITORING_SENSORS = [
    "water_level",
    "priming_status",
    "priming_needed",
    "last_prime_time",
    "device_online",
    "device_health",
    "connection_status",
    "device_temperature",
    "device_humidity",
    "device_pressure",
    "device_firmware_version",
    "device_model",
    "device_serial",
    "device_manufacturer",
    "device_capabilities",
    "device_features",
    "device_settings",
    "device_configuration",
    "device_analytics",
    "device_insights",
    "device_maintenance",
    "device_warranty",
    "device_support",
    "device_updates",
    "device_errors",
    "device_warnings",
    "device_notifications",
    "device_alerts",
    "device_status",
    "device_state",
]

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep Device Monitoring sensors."""
    config_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    coordinator = config_data.coordinator
    eight = config_data.eight

    entities = []

    # Add device monitoring sensors
    for sensor_type in DEVICE_MONITORING_SENSORS:
        entities.append(
            EightDeviceMonitoringSensor(
                entry,
                coordinator,
                eight,
                sensor_type,
            )
        )

    async_add_entities(entities)


class EightDeviceMonitoringSensor(EightSleepBaseEntity, SensorEntity):
    """Representation of an Eight Sleep Device Monitoring sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        sensor_type: str,
    ) -> None:
        """Initialize the device monitoring sensor."""
        super().__init__(entry, coordinator, eight, None)  # No user for device sensors
        self._sensor_type = sensor_type
        self._attr_name = f"Eight Sleep {self._get_sensor_name(sensor_type)}"
        self._attr_unique_id = f"device_{sensor_type}"
        
        # Set device class and unit based on sensor type
        self._set_sensor_properties(sensor_type)

    def _get_sensor_name(self, sensor_type: str) -> str:
        """Get the display name for the sensor type."""
        name_map = {
            "water_level": "Water Level",
            "priming_status": "Priming Status",
            "priming_needed": "Priming Needed",
            "last_prime_time": "Last Prime Time",
            "device_online": "Device Online",
            "device_health": "Device Health",
            "connection_status": "Connection Status",
            "device_temperature": "Device Temperature",
            "device_humidity": "Device Humidity",
            "device_pressure": "Device Pressure",
            "device_firmware_version": "Firmware Version",
            "device_model": "Device Model",
            "device_serial": "Device Serial",
            "device_manufacturer": "Device Manufacturer",
            "device_capabilities": "Device Capabilities",
            "device_features": "Device Features",
            "device_settings": "Device Settings",
            "device_configuration": "Device Configuration",
            "device_analytics": "Device Analytics",
            "device_insights": "Device Insights",
            "device_maintenance": "Device Maintenance",
            "device_warranty": "Device Warranty",
            "device_support": "Device Support",
            "device_updates": "Device Updates",
            "device_errors": "Device Errors",
            "device_warnings": "Device Warnings",
            "device_notifications": "Device Notifications",
            "device_alerts": "Device Alerts",
            "device_status": "Device Status",
            "device_state": "Device State",
        }
        return name_map.get(sensor_type, sensor_type.replace("_", " ").title())

    def _set_sensor_properties(self, sensor_type: str) -> None:
        """Set device class, unit, and state class based on sensor type."""
        if "temperature" in sensor_type.lower():
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "humidity" in sensor_type.lower():
            self._attr_device_class = SensorDeviceClass.HUMIDITY
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "pressure" in sensor_type.lower():
            self._attr_device_class = SensorDeviceClass.PRESSURE
            self._attr_native_unit_of_measurement = "hPa"
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "level" in sensor_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "status" in sensor_type.lower() or "state" in sensor_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = None
        else:
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> str | int | float | None:
        """Return the state of the sensor."""
        if not self._eight:
            return None

        try:
            if self._sensor_type == "water_level":
                return self._get_water_level()
            elif self._sensor_type == "priming_status":
                return self._eight.is_priming
            elif self._sensor_type == "priming_needed":
                return self._eight.need_priming
            elif self._sensor_type == "last_prime_time":
                return self._get_last_prime_time()
            elif self._sensor_type == "device_online":
                return self._get_device_online_status()
            elif self._sensor_type == "device_health":
                return self._get_device_health()
            elif self._sensor_type == "connection_status":
                return self._get_connection_status()
            elif self._sensor_type == "device_temperature":
                return self._get_device_temperature()
            elif self._sensor_type == "device_humidity":
                return self._get_device_humidity()
            elif self._sensor_type == "device_pressure":
                return self._get_device_pressure()
            elif self._sensor_type == "device_firmware_version":
                return self._get_device_firmware_version()
            elif self._sensor_type == "device_model":
                return self._get_device_model()
            elif self._sensor_type == "device_serial":
                return self._get_device_serial()
            elif self._sensor_type == "device_manufacturer":
                return "Eight Sleep"
            elif self._sensor_type == "device_capabilities":
                return self._get_device_capabilities()
            elif self._sensor_type == "device_features":
                return self._get_device_features()
            elif self._sensor_type == "device_settings":
                return self._get_device_settings()
            elif self._sensor_type == "device_configuration":
                return self._get_device_configuration()
            elif self._sensor_type == "device_analytics":
                return self._get_device_analytics()
            elif self._sensor_type == "device_insights":
                return self._get_device_insights()
            elif self._sensor_type == "device_maintenance":
                return self._get_device_maintenance()
            elif self._sensor_type == "device_warranty":
                return self._get_device_warranty()
            elif self._sensor_type == "device_support":
                return self._get_device_support()
            elif self._sensor_type == "device_updates":
                return self._get_device_updates()
            elif self._sensor_type == "device_errors":
                return self._get_device_errors()
            elif self._sensor_type == "device_warnings":
                return self._get_device_warnings()
            elif self._sensor_type == "device_notifications":
                return self._get_device_notifications()
            elif self._sensor_type == "device_alerts":
                return self._get_device_alerts()
            elif self._sensor_type == "device_status":
                return self._get_device_status()
            elif self._sensor_type == "device_state":
                return self._get_device_state()
            else:
                return None
        except Exception as e:
            _LOGGER.error(f"Error getting {self._sensor_type} value: {e}")
            return None

    def _get_water_level(self) -> int | None:
        """Get water level percentage."""
        try:
            if self._eight.device_data:
                # Calculate water level based on device data
                has_water = self._eight.has_water
                if has_water:
                    return 100  # Full
                else:
                    return 0  # Empty
        except Exception as e:
            _LOGGER.error(f"Error getting water level: {e}")
        return None

    def _get_last_prime_time(self) -> str | None:
        """Get last prime time."""
        try:
            last_prime = self._eight.last_prime
            if last_prime:
                return last_prime.isoformat()
        except Exception as e:
            _LOGGER.error(f"Error getting last prime time: {e}")
        return None

    def _get_device_online_status(self) -> bool | None:
        """Get device online status."""
        try:
            # Check if device is responding to API calls
            return self._eight.device_data is not None
        except Exception as e:
            _LOGGER.error(f"Error getting device online status: {e}")
        return None

    def _get_device_health(self) -> str | None:
        """Get device health status."""
        try:
            if self._eight.device_data:
                # Check various health indicators
                health_indicators = []
                if self._eight.need_priming:
                    health_indicators.append("Needs Priming")
                if not self._eight.has_water:
                    health_indicators.append("Low Water")
                if self._eight.is_priming:
                    health_indicators.append("Priming")
                
                if not health_indicators:
                    return "Healthy"
                else:
                    return ", ".join(health_indicators)
        except Exception as e:
            _LOGGER.error(f"Error getting device health: {e}")
        return None

    def _get_connection_status(self) -> str | None:
        """Get connection status."""
        try:
            if self._eight.device_data:
                return "Connected"
            else:
                return "Disconnected"
        except Exception as e:
            _LOGGER.error(f"Error getting connection status: {e}")
        return None

    def _get_device_temperature(self) -> float | None:
        """Get device temperature."""
        try:
            if self._eight.device_data:
                # Extract temperature from device data if available
                return self._eight.device_data.get("temperature")
        except Exception as e:
            _LOGGER.error(f"Error getting device temperature: {e}")
        return None

    def _get_device_humidity(self) -> float | None:
        """Get device humidity."""
        try:
            if self._eight.device_data:
                # Extract humidity from device data if available
                return self._eight.device_data.get("humidity")
        except Exception as e:
            _LOGGER.error(f"Error getting device humidity: {e}")
        return None

    def _get_device_pressure(self) -> float | None:
        """Get device pressure."""
        try:
            if self._eight.device_data:
                # Extract pressure from device data if available
                return self._eight.device_data.get("pressure")
        except Exception as e:
            _LOGGER.error(f"Error getting device pressure: {e}")
        return None

    def _get_device_firmware_version(self) -> str | None:
        """Get device firmware version."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("firmwareVersion")
        except Exception as e:
            _LOGGER.error(f"Error getting device firmware version: {e}")
        return None

    def _get_device_model(self) -> str | None:
        """Get device model."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("model")
        except Exception as e:
            _LOGGER.error(f"Error getting device model: {e}")
        return None

    def _get_device_serial(self) -> str | None:
        """Get device serial number."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("serialNumber")
        except Exception as e:
            _LOGGER.error(f"Error getting device serial: {e}")
        return None

    def _get_device_capabilities(self) -> str | None:
        """Get device capabilities."""
        try:
            capabilities = []
            if self._eight.is_pod:
                capabilities.append("Pod")
            if self._eight.has_base:
                capabilities.append("Base")
            if capabilities:
                return ", ".join(capabilities)
        except Exception as e:
            _LOGGER.error(f"Error getting device capabilities: {e}")
        return None

    def _get_device_features(self) -> str | None:
        """Get device features."""
        try:
            features = []
            if self._eight.is_pod:
                features.append("Cooling")
            if self._eight.has_base:
                features.append("Elevation")
            if features:
                return ", ".join(features)
        except Exception as e:
            _LOGGER.error(f"Error getting device features: {e}")
        return None

    def _get_device_settings(self) -> str | None:
        """Get device settings."""
        try:
            if self._eight.device_data:
                return str(self._eight.device_data.get("settings", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting device settings: {e}")
        return None

    def _get_device_configuration(self) -> str | None:
        """Get device configuration."""
        try:
            if self._eight.device_data:
                return str(self._eight.device_data.get("configuration", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting device configuration: {e}")
        return None

    def _get_device_analytics(self) -> str | None:
        """Get device analytics."""
        try:
            if self._eight.device_data:
                return str(self._eight.device_data.get("analytics", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting device analytics: {e}")
        return None

    def _get_device_insights(self) -> str | None:
        """Get device insights."""
        try:
            if self._eight.device_data:
                return str(self._eight.device_data.get("insights", {}))
        except Exception as e:
            _LOGGER.error(f"Error getting device insights: {e}")
        return None

    def _get_device_maintenance(self) -> str | None:
        """Get device maintenance status."""
        try:
            maintenance_items = []
            if self._eight.need_priming:
                maintenance_items.append("Priming Required")
            if not self._eight.has_water:
                maintenance_items.append("Water Refill Required")
            if maintenance_items:
                return ", ".join(maintenance_items)
            else:
                return "No Maintenance Required"
        except Exception as e:
            _LOGGER.error(f"Error getting device maintenance: {e}")
        return None

    def _get_device_warranty(self) -> str | None:
        """Get device warranty status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("warranty", "Unknown")
        except Exception as e:
            _LOGGER.error(f"Error getting device warranty: {e}")
        return None

    def _get_device_support(self) -> str | None:
        """Get device support status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("support", "Available")
        except Exception as e:
            _LOGGER.error(f"Error getting device support: {e}")
        return None

    def _get_device_updates(self) -> str | None:
        """Get device update status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("updates", "Up to Date")
        except Exception as e:
            _LOGGER.error(f"Error getting device updates: {e}")
        return None

    def _get_device_errors(self) -> str | None:
        """Get device errors."""
        try:
            if self._eight.device_data:
                errors = self._eight.device_data.get("errors", [])
                if errors:
                    return ", ".join(errors)
                else:
                    return "No Errors"
        except Exception as e:
            _LOGGER.error(f"Error getting device errors: {e}")
        return None

    def _get_device_warnings(self) -> str | None:
        """Get device warnings."""
        try:
            if self._eight.device_data:
                warnings = self._eight.device_data.get("warnings", [])
                if warnings:
                    return ", ".join(warnings)
                else:
                    return "No Warnings"
        except Exception as e:
            _LOGGER.error(f"Error getting device warnings: {e}")
        return None

    def _get_device_notifications(self) -> str | None:
        """Get device notifications."""
        try:
            if self._eight.device_data:
                notifications = self._eight.device_data.get("notifications", [])
                if notifications:
                    return ", ".join(notifications)
                else:
                    return "No Notifications"
        except Exception as e:
            _LOGGER.error(f"Error getting device notifications: {e}")
        return None

    def _get_device_alerts(self) -> str | None:
        """Get device alerts."""
        try:
            if self._eight.device_data:
                alerts = self._eight.device_data.get("alerts", [])
                if alerts:
                    return ", ".join(alerts)
                else:
                    return "No Alerts"
        except Exception as e:
            _LOGGER.error(f"Error getting device alerts: {e}")
        return None

    def _get_device_status(self) -> str | None:
        """Get device status."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("status", "Unknown")
        except Exception as e:
            _LOGGER.error(f"Error getting device status: {e}")
        return None

    def _get_device_state(self) -> str | None:
        """Get device state."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("state", "Unknown")
        except Exception as e:
            _LOGGER.error(f"Error getting device state: {e}")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if not self._eight:
            return None

        attrs = {
            "sensor_type": self._sensor_type,
            "device_id": self._eight.device_id,
            "is_pod": self._eight.is_pod,
            "has_base": self._eight.has_base,
        }

        # Add device-specific attributes
        if "water" in self._sensor_type.lower():
            attrs["has_water"] = self._eight.has_water
            attrs["water_level_percentage"] = self._get_water_level()
        elif "priming" in self._sensor_type.lower():
            attrs["is_priming"] = self._eight.is_priming
            attrs["need_priming"] = self._eight.need_priming
            attrs["last_prime_time"] = self._get_last_prime_time()
        elif "health" in self._sensor_type.lower():
            attrs["device_health"] = self._get_device_health()
            attrs["connection_status"] = self._get_connection_status()
            attrs["device_online"] = self._get_device_online_status()

        return attrs 