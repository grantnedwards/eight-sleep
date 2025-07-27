"""Connection status sensor for Eight Sleep integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import EightSleepBaseEntity
from .const import DOMAIN
from .util import EightSleepOfflineManager

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Eight Sleep connection status sensor."""
    config_entry_data = hass.data[DOMAIN][config_entry.entry_id]
    eight = config_entry_data.api
    offline_manager = config_entry_data.offline_manager

    # Create connection status sensor
    async_add_entities([
        EightSleepConnectionStatusSensor(
            config_entry,
            config_entry_data.device_coordinator,
            eight,
            None,
            "connection_status",
            offline_manager
        )
    ])

class EightSleepConnectionStatusSensor(EightSleepBaseEntity, SensorEntity):
    """Connection status sensor for Eight Sleep."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        coordinator,
        eight,
        user,
        sensor: str,
        offline_manager: EightSleepOfflineManager,
    ) -> None:
        """Initialize the connection status sensor."""
        super().__init__(config_entry, coordinator, eight, user, sensor)
        self._offline_manager = offline_manager
        self._attr_device_class = "connectivity"
        self._attr_icon = "mdi:connection"
        self._attr_entity_category = "diagnostic"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Connection Status"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self._offline_manager.connection_status.is_online:
            return "online"
        return "offline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        health_metrics = self._offline_manager.get_health_report()
        connection_status = health_metrics["connection_status"]
        cache_stats = health_metrics["cache_stats"]

        return {
            "status_message": self._offline_manager.get_offline_status_message(),
            "is_online": self._offline_manager.connection_status.is_online,
            "last_online": connection_status["last_online"],
            "last_check": connection_status["last_check"],
            "connection_errors": connection_status["connection_errors"],
            "successful_requests": connection_status["successful_requests"],
            "failed_requests": connection_status["failed_requests"],
            "success_rate": connection_status["success_rate"],
            "average_response_time": connection_status["average_response_time"],
            "cache_hit_rate": cache_stats["hit_rate"],
            "cache_size": cache_stats["cache_size"],
            "recovery_attempts": health_metrics["recovery_attempts"],
            "max_recovery_attempts": health_metrics["max_recovery_attempts"],
        }

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        if self._offline_manager.connection_status.is_online:
            return "mdi:connection"
        return "mdi:connection-off"

    @property
    def state_class(self) -> str:
        """Return the state class of the sensor."""
        return None  # This is a categorical sensor, not a measurement
