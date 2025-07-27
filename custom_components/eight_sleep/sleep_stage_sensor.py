"""Enhanced sleep stage tracking sensor for Eight Sleep."""

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
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import EightSleepBaseEntity, EightSleepConfigEntryData
from .const import DOMAIN
from .pyEight.eight import EightSleep
from .pyEight.user import EightUser

_LOGGER = logging.getLogger(__name__)

# Sleep stage constants
SLEEP_STAGES = {
    "awake": "Awake",
    "light": "Light Sleep",
    "deep": "Deep Sleep",
    "rem": "REM Sleep",
    "unknown": "Unknown",
}

SLEEP_STAGE_ICONS = {
    "awake": "mdi:eye",
    "light": "mdi:bed",
    "deep": "mdi:bed-deep",
    "rem": "mdi:brain",
    "unknown": "mdi:help-circle",
}

SLEEP_STAGE_COLORS = {
    "awake": "#FF9800",
    "light": "#4CAF50",
    "deep": "#2196F3",
    "rem": "#9C27B0",
    "unknown": "#757575",
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Eight Sleep sleep stage sensors."""
    config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
    eight = config_entry_data.api

    entities = []

    # Create sleep stage sensors for each user
    for user in eight.users.values():
        entities.append(
            EightSleepStageSensor(
                entry,
                config_entry_data.user_coordinator,
                eight,
                user,
            )
        )

        # Create detailed sleep stage breakdown sensors
        entities.append(
            EightSleepStageBreakdownSensor(
                entry,
                config_entry_data.user_coordinator,
                eight,
                user,
            )
        )

    async_add_entities(entities)

class EightSleepStageSensor(EightSleepBaseEntity, SensorEntity):
    """Enhanced sleep stage tracking sensor."""

    _attr_has_entity_name = True
    _attr_name = "Sleep Stage"
    _attr_icon = "mdi:bed"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(SLEEP_STAGES.values())

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
    ) -> None:
        """Initialize the sleep stage sensor."""
        super().__init__(entry, coordinator, eight, user, "sleep_stage_enhanced")
        self._attr_unique_id = f"{self._attr_unique_id}_enhanced"
        self._last_stage_change = None
        self._stage_duration = timedelta(0)

    @property
    def native_value(self) -> str | None:
        """Return the current sleep stage."""
        if not self._user_obj:
            return None

        current_stage = self._user_obj.current_sleep_stage
        if not current_stage:
            return "Unknown"

        # Map the stage to a more user-friendly name
        stage_mapping = {
            "awake": "Awake",
            "light": "Light Sleep",
            "deep": "Deep Sleep",
            "rem": "REM Sleep",
        }

        return stage_mapping.get(current_stage, "Unknown")

    @property
    def icon(self) -> str:
        """Return the icon for the current sleep stage."""
        if not self._user_obj:
            return "mdi:help-circle"

        current_stage = self._user_obj.current_sleep_stage
        return SLEEP_STAGE_ICONS.get(current_stage, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return detailed sleep stage attributes."""
        if not self._user_obj:
            return None

        current_stage = self._user_obj.current_sleep_stage
        current_values = self._user_obj.current_values

        if not current_values:
            return None

        # Calculate stage duration
        now = datetime.now()
        if self._last_stage_change is None:
            self._last_stage_change = now
            self._stage_duration = timedelta(0)
        elif current_stage != getattr(self, '_last_stage', None):
            # Stage changed, reset duration
            self._last_stage_change = now
            self._stage_duration = timedelta(0)
        else:
            # Same stage, update duration
            self._stage_duration = now - self._last_stage_change

        self._last_stage = current_stage

        # Get sleep metrics
        breakdown = current_values.get("breakdown", {})
        total_sleep_time = sum(breakdown.values()) - breakdown.get("awake", 0)

        # Calculate stage percentages
        stage_percentages = {}
        if total_sleep_time > 0:
            for stage, duration in breakdown.items():
                if stage != "awake":
                    percentage = (duration / total_sleep_time) * 100
                    stage_percentages[f"{stage}_percentage"] = round(percentage, 1)

        # Get current biometrics
        heart_rate = current_values.get("heart_rate")
        resp_rate = current_values.get("resp_rate")
        room_temp = current_values.get("room_temp")
        bed_temp = current_values.get("bed_temp")

        attributes = {
            "current_stage": current_stage,
            "stage_duration_minutes": int(self._stage_duration.total_seconds() / 60),
            "stage_duration_seconds": int(self._stage_duration.total_seconds()),
            "stage_color": SLEEP_STAGE_COLORS.get(current_stage, "#757575"),
            "total_sleep_time_minutes": int(total_sleep_time / 60) if total_sleep_time else 0,
            "session_start": current_values.get("date"),
            "processing": current_values.get("processing", False),
            "tosses_and_turns": current_values.get("tnt", 0),
        }

        # Add stage percentages
        attributes.update(stage_percentages)

        # Add current biometrics
        if heart_rate is not None:
            attributes["current_heart_rate"] = heart_rate
        if resp_rate is not None:
            attributes["current_respiratory_rate"] = resp_rate
        if room_temp is not None:
            attributes["current_room_temperature"] = room_temp
        if bed_temp is not None:
            attributes["current_bed_temperature"] = bed_temp

        # Add stage history (last 5 stage changes)
        if not hasattr(self, '_stage_history'):
            self._stage_history = []

        if current_stage != getattr(self, '_last_reported_stage', None):
            self._stage_history.append({
                "stage": current_stage,
                "timestamp": now.isoformat(),
                "duration_minutes": int(self._stage_duration.total_seconds() / 60) if self._stage_duration else 0,
            })
            # Keep only last 5 entries
            self._stage_history = self._stage_history[-5:]
            self._last_reported_stage = current_stage

        attributes["stage_history"] = self._stage_history

        return attributes

class EightSleepStageBreakdownSensor(EightSleepBaseEntity, SensorEntity):
    """Detailed sleep stage breakdown sensor."""

    _attr_has_entity_name = True
    _attr_name = "Sleep Stage Breakdown"
    _attr_icon = "mdi:chart-pie"
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser,
    ) -> None:
        """Initialize the sleep stage breakdown sensor."""
        super().__init__(entry, coordinator, eight, user, "sleep_stage_breakdown")
        self._attr_unique_id = f"{self._attr_unique_id}_breakdown"

    @property
    def native_value(self) -> float | None:
        """Return the dominant sleep stage percentage."""
        if not self._user_obj:
            return None

        current_values = self._user_obj.current_values
        if not current_values:
            return None

        breakdown = current_values.get("breakdown", {})
        total_sleep_time = sum(breakdown.values()) - breakdown.get("awake", 0)

        if total_sleep_time <= 0:
            return None

        # Find the dominant stage (excluding awake)
        dominant_stage = None
        max_duration = 0

        for stage, duration in breakdown.items():
            if stage != "awake" and duration > max_duration:
                max_duration = duration
                dominant_stage = stage

        if dominant_stage:
            percentage = (max_duration / total_sleep_time) * 100
            return round(percentage, 1)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return detailed sleep stage breakdown."""
        if not self._user_obj:
            return None

        current_values = self._user_obj.current_values
        if not current_values:
            return None

        breakdown = current_values.get("breakdown", {})
        total_sleep_time = sum(breakdown.values()) - breakdown.get("awake", 0)

        if total_sleep_time <= 0:
            return None

        # Calculate percentages for each stage
        stage_breakdown = {}
        for stage, duration in breakdown.items():
            if stage != "awake":
                percentage = (duration / total_sleep_time) * 100
                stage_breakdown[f"{stage}_percentage"] = round(percentage, 1)
                stage_breakdown[f"{stage}_minutes"] = int(duration / 60)

        # Add awake time
        awake_time = breakdown.get("awake", 0)
        if awake_time > 0:
            stage_breakdown["awake_minutes"] = int(awake_time / 60)

        # Add total sleep time
        stage_breakdown["total_sleep_minutes"] = int(total_sleep_time / 60)
        stage_breakdown["total_sleep_hours"] = round(total_sleep_time / 3600, 1)

        # Add sleep efficiency
        total_time = sum(breakdown.values())
        if total_time > 0:
            sleep_efficiency = ((total_time - awake_time) / total_time) * 100
            stage_breakdown["sleep_efficiency_percentage"] = round(sleep_efficiency, 1)

        # Add stage colors for UI
        stage_breakdown["stage_colors"] = SLEEP_STAGE_COLORS

        return stage_breakdown
