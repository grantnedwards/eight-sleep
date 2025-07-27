"""Support for Eight Sleep Number entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
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
from .pyEight.user import EightUser
from .pyEight.eight import EightSleep

_LOGGER = logging.getLogger(__name__)

# Number Entity Types
NUMBER_ENTITIES = [
    "target_heating_level",
    "heating_level",
    "target_temperature",
    "current_temperature",
    "room_temperature",
    "water_level",
    "priming_progress",
    "firmware_version",
    "device_temperature",
    "device_humidity",
    "device_pressure",
    "sleep_duration",
    "sleep_latency",
    "sleep_efficiency",
    "sleep_quality",
    "sleep_score",
    "heart_rate",
    "respiratory_rate",
    "hrv_value",
    "presence_duration",
    "away_duration",
    "alarm_snooze_duration",
    "alarm_volume",
    "alarm_brightness",
    "notification_count",
    "alert_count",
    "error_count",
    "warning_count",
    "update_progress",
    "maintenance_progress",
    "analytics_score",
    "insights_score",
    "trends_score",
    "history_score",
    "settings_score",
    "configuration_score",
    "schedule_score",
    "routine_score",
]

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep Number entities."""
    config_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    coordinator = config_data.coordinator
    eight = config_data.eight

    entities = []

    # Add number entities for each user
    for user in eight.users.values():
        for entity_type in NUMBER_ENTITIES:
            entities.append(
                EightNumberEntity(
                    entry,
                    coordinator,
                    eight,
                    user,
                    entity_type,
                )
            )

    # Add device-level number entities
    for entity_type in ["water_level", "priming_progress", "firmware_version", "device_temperature", "device_humidity", "device_pressure", "notification_count", "alert_count", "error_count", "warning_count", "update_progress", "maintenance_progress", "analytics_score", "insights_score", "trends_score", "history_score", "settings_score", "configuration_score", "schedule_score", "routine_score"]:
        entities.append(
            EightDeviceNumberEntity(
                entry,
                coordinator,
                eight,
                entity_type,
            )
        )

    async_add_entities(entities)


class EightNumberEntity(EightSleepBaseEntity, NumberEntity):
    """Representation of an Eight Sleep Number entity."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
        entity_type: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(entry, coordinator, eight, user)
        self._entity_type = entity_type
        self._attr_name = f"{self._user.side} {self._get_entity_name(entity_type)}"
        self._attr_unique_id = f"{self._user.user_id}_{entity_type}"
        
        # Set device class, unit, and mode based on entity type
        self._set_entity_properties(entity_type)

    def _get_entity_name(self, entity_type: str) -> str:
        """Get the display name for the entity type."""
        name_map = {
            "target_heating_level": "Target Heating Level",
            "heating_level": "Heating Level",
            "target_temperature": "Target Temperature",
            "current_temperature": "Current Temperature",
            "room_temperature": "Room Temperature",
            "water_level": "Water Level",
            "priming_progress": "Priming Progress",
            "firmware_version": "Firmware Version",
            "device_temperature": "Device Temperature",
            "device_humidity": "Device Humidity",
            "device_pressure": "Device Pressure",
            "sleep_duration": "Sleep Duration",
            "sleep_latency": "Sleep Latency",
            "sleep_efficiency": "Sleep Efficiency",
            "sleep_quality": "Sleep Quality",
            "sleep_score": "Sleep Score",
            "heart_rate": "Heart Rate",
            "respiratory_rate": "Respiratory Rate",
            "hrv_value": "HRV Value",
            "presence_duration": "Presence Duration",
            "away_duration": "Away Duration",
            "alarm_snooze_duration": "Alarm Snooze Duration",
            "alarm_volume": "Alarm Volume",
            "alarm_brightness": "Alarm Brightness",
            "notification_count": "Notification Count",
            "alert_count": "Alert Count",
            "error_count": "Error Count",
            "warning_count": "Warning Count",
            "update_progress": "Update Progress",
            "maintenance_progress": "Maintenance Progress",
            "analytics_score": "Analytics Score",
            "insights_score": "Insights Score",
            "trends_score": "Trends Score",
            "history_score": "History Score",
            "settings_score": "Settings Score",
            "configuration_score": "Configuration Score",
            "schedule_score": "Schedule Score",
            "routine_score": "Routine Score",
        }
        return name_map.get(entity_type, entity_type.replace("_", " ").title())

    def _set_entity_properties(self, entity_type: str) -> None:
        """Set device class, unit, and mode based on entity type."""
        if "temperature" in entity_type.lower():
            self._attr_device_class = NumberDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_mode = NumberMode.SLIDER
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 50.0
            self._attr_native_step = 0.5
        elif "duration" in entity_type.lower() or "latency" in entity_type.lower():
            self._attr_device_class = NumberDeviceClass.DURATION
            self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
            self._attr_mode = NumberMode.BOX
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 86400.0  # 24 hours
            self._attr_native_step = 1.0
        elif "level" in entity_type.lower() or "progress" in entity_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_mode = NumberMode.SLIDER
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 100.0
            self._attr_native_step = 1.0
        elif "rate" in entity_type.lower() or "hrv" in entity_type.lower():
            self._attr_device_class = NumberDeviceClass.FREQUENCY
            self._attr_native_unit_of_measurement = "bpm" if "rate" in entity_type.lower() else "ms"
            self._attr_mode = NumberMode.BOX
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 200.0 if "rate" in entity_type.lower() else 1000.0
            self._attr_native_step = 1.0
        elif "score" in entity_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_mode = NumberMode.BOX
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 100.0
            self._attr_native_step = 1.0
        elif "count" in entity_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = "count"
            self._attr_mode = NumberMode.BOX
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 1000.0
            self._attr_native_step = 1.0
        else:
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = None
            self._attr_mode = NumberMode.BOX
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 100.0
            self._attr_native_step = 1.0

    @property
    def native_value(self) -> float | None:
        """Return the value of the number entity."""
        if not self._user:
            return None

        try:
            if self._entity_type == "target_heating_level":
                return self._user.target_heating_level
            elif self._entity_type == "heating_level":
                return self._user.heating_level
            elif self._entity_type == "target_temperature":
                return self._user.target_bed_temperature
            elif self._entity_type == "current_temperature":
                return self._user.current_bed_temperature
            elif self._entity_type == "room_temperature":
                return self._eight.room_temperature
            elif self._entity_type == "sleep_duration":
                return self._user.time_slept
            elif self._entity_type == "sleep_latency":
                return self._get_sleep_latency()
            elif self._entity_type == "sleep_efficiency":
                return self._get_sleep_efficiency()
            elif self._entity_type == "sleep_quality":
                return self._user.current_sleep_quality_score
            elif self._entity_type == "sleep_score":
                return self._user.current_sleep_fitness_score
            elif self._entity_type == "heart_rate":
                return self._user.current_heart_rate
            elif self._entity_type == "respiratory_rate":
                return self._user.current_resp_rate
            elif self._entity_type == "hrv_value":
                return self._user.current_hrv
            elif self._entity_type == "presence_duration":
                return self._get_presence_duration()
            elif self._entity_type == "away_duration":
                return self._get_away_duration()
            elif self._entity_type == "alarm_snooze_duration":
                return self._get_alarm_snooze_duration()
            elif self._entity_type == "alarm_volume":
                return self._get_alarm_volume()
            elif self._entity_type == "alarm_brightness":
                return self._get_alarm_brightness()
            else:
                return None
        except Exception as e:
            _LOGGER.error(f"Error getting {self._entity_type} value: {e}")
            return None

    def _get_sleep_latency(self) -> float | None:
        """Get sleep latency."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepLatency")
        except Exception as e:
            _LOGGER.error(f"Error getting sleep latency: {e}")
        return None

    def _get_sleep_efficiency(self) -> float | None:
        """Get sleep efficiency."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("sleepEfficiency")
        except Exception as e:
            _LOGGER.error(f"Error getting sleep efficiency: {e}")
        return None

    def _get_presence_duration(self) -> float | None:
        """Get presence duration."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("presenceDuration")
        except Exception as e:
            _LOGGER.error(f"Error getting presence duration: {e}")
        return None

    def _get_away_duration(self) -> float | None:
        """Get away duration."""
        try:
            if self._user.trends and len(self._user.trends) > 0:
                current_trend = self._user.trends[-1]
                return current_trend.get("awayDuration")
        except Exception as e:
            _LOGGER.error(f"Error getting away duration: {e}")
        return None

    def _get_alarm_snooze_duration(self) -> float | None:
        """Get alarm snooze duration."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("snoozeDuration", 0)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm snooze duration: {e}")
        return None

    def _get_alarm_volume(self) -> float | None:
        """Get alarm volume."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("volume", 50)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm volume: {e}")
        return None

    def _get_alarm_brightness(self) -> float | None:
        """Get alarm brightness."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    return side_alarms[0].get("brightness", 50)
        except Exception as e:
            _LOGGER.error(f"Error getting alarm brightness: {e}")
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value of the number entity."""
        try:
            if self._entity_type == "target_heating_level":
                await self._user.set_heating_level(int(value))
            elif self._entity_type == "target_temperature":
                await self._user.set_target_bed_temperature(value)
            elif self._entity_type == "alarm_snooze_duration":
                await self._user.alarm_snooze(int(value))
            elif self._entity_type == "alarm_volume":
                await self._set_alarm_volume(int(value))
            elif self._entity_type == "alarm_brightness":
                await self._set_alarm_brightness(int(value))
        except Exception as e:
            _LOGGER.error(f"Error setting {self._entity_type} value: {e}")

    async def _set_alarm_volume(self, volume: int) -> None:
        """Set alarm volume."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    side_alarms[0]["volume"] = volume
        except Exception as e:
            _LOGGER.error(f"Error setting alarm volume: {e}")

    async def _set_alarm_brightness(self, brightness: int) -> None:
        """Set alarm brightness."""
        try:
            if self._eight.device_data:
                alarms = self._eight.device_data.get("alarms", {})
                side_alarms = alarms.get(self._user.side, [])
                if side_alarms:
                    side_alarms[0]["brightness"] = brightness
        except Exception as e:
            _LOGGER.error(f"Error setting alarm brightness: {e}")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if not self._user:
            return None

        attrs = {
            "side": self._user.side,
            "user_id": self._user.user_id,
            "entity_type": self._entity_type,
        }

        return attrs


class EightDeviceNumberEntity(EightSleepBaseEntity, NumberEntity):
    """Representation of an Eight Sleep Device Number entity."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        entity_type: str,
    ) -> None:
        """Initialize the device number entity."""
        super().__init__(entry, coordinator, eight, None)  # No user for device entities
        self._entity_type = entity_type
        self._attr_name = f"Eight Sleep {self._get_entity_name(entity_type)}"
        self._attr_unique_id = f"device_{entity_type}"
        
        # Set device class, unit, and mode based on entity type
        self._set_entity_properties(entity_type)

    def _get_entity_name(self, entity_type: str) -> str:
        """Get the display name for the entity type."""
        name_map = {
            "water_level": "Water Level",
            "priming_progress": "Priming Progress",
            "firmware_version": "Firmware Version",
            "device_temperature": "Device Temperature",
            "device_humidity": "Device Humidity",
            "device_pressure": "Device Pressure",
            "notification_count": "Notification Count",
            "alert_count": "Alert Count",
            "error_count": "Error Count",
            "warning_count": "Warning Count",
            "update_progress": "Update Progress",
            "maintenance_progress": "Maintenance Progress",
            "analytics_score": "Analytics Score",
            "insights_score": "Insights Score",
            "trends_score": "Trends Score",
            "history_score": "History Score",
            "settings_score": "Settings Score",
            "configuration_score": "Configuration Score",
            "schedule_score": "Schedule Score",
            "routine_score": "Routine Score",
        }
        return name_map.get(entity_type, entity_type.replace("_", " ").title())

    def _set_entity_properties(self, entity_type: str) -> None:
        """Set device class, unit, and mode based on entity type."""
        if "temperature" in entity_type.lower():
            self._attr_device_class = NumberDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_mode = NumberMode.BOX
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 50.0
            self._attr_native_step = 0.5
        elif "humidity" in entity_type.lower():
            self._attr_device_class = NumberDeviceClass.HUMIDITY
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_mode = NumberMode.BOX
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 100.0
            self._attr_native_step = 1.0
        elif "pressure" in entity_type.lower():
            self._attr_device_class = NumberDeviceClass.PRESSURE
            self._attr_native_unit_of_measurement = "hPa"
            self._attr_mode = NumberMode.BOX
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 2000.0
            self._attr_native_step = 1.0
        elif "level" in entity_type.lower() or "progress" in entity_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_mode = NumberMode.BOX
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 100.0
            self._attr_native_step = 1.0
        elif "count" in entity_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = "count"
            self._attr_mode = NumberMode.BOX
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 1000.0
            self._attr_native_step = 1.0
        elif "score" in entity_type.lower():
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_mode = NumberMode.BOX
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 100.0
            self._attr_native_step = 1.0
        else:
            self._attr_device_class = None
            self._attr_native_unit_of_measurement = None
            self._attr_mode = NumberMode.BOX
            self._attr_native_min_value = 0.0
            self._attr_native_max_value = 100.0
            self._attr_native_step = 1.0

    @property
    def native_value(self) -> float | None:
        """Return the value of the number entity."""
        if not self._eight:
            return None

        try:
            if self._entity_type == "water_level":
                return self._get_water_level()
            elif self._entity_type == "priming_progress":
                return self._get_priming_progress()
            elif self._entity_type == "firmware_version":
                return self._get_firmware_version()
            elif self._entity_type == "device_temperature":
                return self._get_device_temperature()
            elif self._entity_type == "device_humidity":
                return self._get_device_humidity()
            elif self._entity_type == "device_pressure":
                return self._get_device_pressure()
            elif self._entity_type == "notification_count":
                return self._get_notification_count()
            elif self._entity_type == "alert_count":
                return self._get_alert_count()
            elif self._entity_type == "error_count":
                return self._get_error_count()
            elif self._entity_type == "warning_count":
                return self._get_warning_count()
            elif self._entity_type == "update_progress":
                return self._get_update_progress()
            elif self._entity_type == "maintenance_progress":
                return self._get_maintenance_progress()
            elif self._entity_type == "analytics_score":
                return self._get_analytics_score()
            elif self._entity_type == "insights_score":
                return self._get_insights_score()
            elif self._entity_type == "trends_score":
                return self._get_trends_score()
            elif self._entity_type == "history_score":
                return self._get_history_score()
            elif self._entity_type == "settings_score":
                return self._get_settings_score()
            elif self._entity_type == "configuration_score":
                return self._get_configuration_score()
            elif self._entity_type == "schedule_score":
                return self._get_schedule_score()
            elif self._entity_type == "routine_score":
                return self._get_routine_score()
            else:
                return None
        except Exception as e:
            _LOGGER.error(f"Error getting {self._entity_type} value: {e}")
            return None

    def _get_water_level(self) -> float | None:
        """Get water level percentage."""
        try:
            if self._eight.has_water:
                return 100.0
            else:
                return 0.0
        except Exception as e:
            _LOGGER.error(f"Error getting water level: {e}")
        return None

    def _get_priming_progress(self) -> float | None:
        """Get priming progress percentage."""
        try:
            if self._eight.is_priming:
                return 50.0  # Estimated progress
            elif self._eight.need_priming:
                return 0.0
            else:
                return 100.0
        except Exception as e:
            _LOGGER.error(f"Error getting priming progress: {e}")
        return None

    def _get_firmware_version(self) -> float | None:
        """Get firmware version as number."""
        try:
            if self._eight.device_data:
                version_str = self._eight.device_data.get("firmwareVersion", "0.0.0")
                # Convert version string to number (e.g., "1.2.3" -> 1.23)
                parts = version_str.split(".")
                if len(parts) >= 2:
                    return float(f"{parts[0]}.{parts[1]}")
        except Exception as e:
            _LOGGER.error(f"Error getting firmware version: {e}")
        return None

    def _get_device_temperature(self) -> float | None:
        """Get device temperature."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("temperature")
        except Exception as e:
            _LOGGER.error(f"Error getting device temperature: {e}")
        return None

    def _get_device_humidity(self) -> float | None:
        """Get device humidity."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("humidity")
        except Exception as e:
            _LOGGER.error(f"Error getting device humidity: {e}")
        return None

    def _get_device_pressure(self) -> float | None:
        """Get device pressure."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("pressure")
        except Exception as e:
            _LOGGER.error(f"Error getting device pressure: {e}")
        return None

    def _get_notification_count(self) -> float | None:
        """Get notification count."""
        try:
            if self._eight.device_data:
                notifications = self._eight.device_data.get("notifications", [])
                return float(len(notifications))
        except Exception as e:
            _LOGGER.error(f"Error getting notification count: {e}")
        return None

    def _get_alert_count(self) -> float | None:
        """Get alert count."""
        try:
            if self._eight.device_data:
                alerts = self._eight.device_data.get("alerts", [])
                return float(len(alerts))
        except Exception as e:
            _LOGGER.error(f"Error getting alert count: {e}")
        return None

    def _get_error_count(self) -> float | None:
        """Get error count."""
        try:
            if self._eight.device_data:
                errors = self._eight.device_data.get("errors", [])
                return float(len(errors))
        except Exception as e:
            _LOGGER.error(f"Error getting error count: {e}")
        return None

    def _get_warning_count(self) -> float | None:
        """Get warning count."""
        try:
            if self._eight.device_data:
                warnings = self._eight.device_data.get("warnings", [])
                return float(len(warnings))
        except Exception as e:
            _LOGGER.error(f"Error getting warning count: {e}")
        return None

    def _get_update_progress(self) -> float | None:
        """Get update progress."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("updateProgress", 0.0)
        except Exception as e:
            _LOGGER.error(f"Error getting update progress: {e}")
        return None

    def _get_maintenance_progress(self) -> float | None:
        """Get maintenance progress."""
        try:
            if self._eight.need_priming:
                return 0.0
            elif self._eight.is_priming:
                return 50.0
            else:
                return 100.0
        except Exception as e:
            _LOGGER.error(f"Error getting maintenance progress: {e}")
        return None

    def _get_analytics_score(self) -> float | None:
        """Get analytics score."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("analyticsScore", 0.0)
        except Exception as e:
            _LOGGER.error(f"Error getting analytics score: {e}")
        return None

    def _get_insights_score(self) -> float | None:
        """Get insights score."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("insightsScore", 0.0)
        except Exception as e:
            _LOGGER.error(f"Error getting insights score: {e}")
        return None

    def _get_trends_score(self) -> float | None:
        """Get trends score."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("trendsScore", 0.0)
        except Exception as e:
            _LOGGER.error(f"Error getting trends score: {e}")
        return None

    def _get_history_score(self) -> float | None:
        """Get history score."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("historyScore", 0.0)
        except Exception as e:
            _LOGGER.error(f"Error getting history score: {e}")
        return None

    def _get_settings_score(self) -> float | None:
        """Get settings score."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("settingsScore", 0.0)
        except Exception as e:
            _LOGGER.error(f"Error getting settings score: {e}")
        return None

    def _get_configuration_score(self) -> float | None:
        """Get configuration score."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("configurationScore", 0.0)
        except Exception as e:
            _LOGGER.error(f"Error getting configuration score: {e}")
        return None

    def _get_schedule_score(self) -> float | None:
        """Get schedule score."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("scheduleScore", 0.0)
        except Exception as e:
            _LOGGER.error(f"Error getting schedule score: {e}")
        return None

    def _get_routine_score(self) -> float | None:
        """Get routine score."""
        try:
            if self._eight.device_data:
                return self._eight.device_data.get("routineScore", 0.0)
        except Exception as e:
            _LOGGER.error(f"Error getting routine score: {e}")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if not self._eight:
            return None

        attrs = {
            "entity_type": self._entity_type,
            "device_id": self._eight.device_id,
            "is_pod": self._eight.is_pod,
            "has_base": self._eight.has_base,
        }

        return attrs
