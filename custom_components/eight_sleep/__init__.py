"""Support for Eight smart mattress covers and mattresses."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from .pyEight.eight import EightSleep
from .pyEight.exceptions import RequestError
from .pyEight.user import EightUser
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_HW_VERSION,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SW_VERSION,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.httpx_client import get_async_client
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import async_get
from homeassistant.helpers.typing import UNDEFINED, ConfigType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, NAME_MAP
from . import device_actions
from .util import create_offline_manager, handle_api_error
from .error_messages import get_user_friendly_error, create_notification_data, get_error_message, categorize_error

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

# Import sensor modules - these are used by the platform setup

DEVICE_SCAN_INTERVAL = timedelta(seconds=60)
USER_SCAN_INTERVAL = timedelta(seconds=300)
BASE_SCAN_INTERVAL = timedelta(seconds=60)

# Retry configuration
MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0
MAX_RETRY_DELAY = 30.0

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_CLIENT_ID): cv.string,
                vol.Optional(CONF_CLIENT_SECRET): cv.string,
            }
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

@dataclass
class EightSleepConfigEntryData:
    """Data used for all entities for a given config entry."""

    api: EightSleep
    device_coordinator: DataUpdateCoordinator
    user_coordinator: DataUpdateCoordinator
    base_coordinator: DataUpdateCoordinator
    offline_manager: Any = None
    device_actions: Any = None

def _get_device_unique_id(
    eight: EightSleep,
    user_obj: EightUser | None = None,
    base_entity: bool = False
) -> str:
    """Get the device's unique ID."""
    unique_id = eight.device_id
    assert unique_id

    if base_entity:
        return f"{unique_id}.base"

    if user_obj:
        return f"{unique_id}.{user_obj.user_id}"

    return unique_id

async def _async_retry_with_backoff(
    func,
    *args,
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_RETRY_DELAY,
    max_delay: float = MAX_RETRY_DELAY,
    **kwargs
):
    """Retry a function with exponential backoff."""
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except (RequestError, ConnectionError, asyncio.TimeoutError) as err:
            last_exception = err

            if attempt == max_retries:
                _LOGGER.error(
                    "Failed after %d attempts: %s",
                    max_retries + 1,
                    err,
                )
                raise

            # Calculate exponential backoff delay with jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = delay * 0.1 * (asyncio.get_event_loop().time() % 1)
            delay += jitter

            _LOGGER.warning(
                "Attempt %d/%d failed: %s. Retrying in %.1f seconds...",
                attempt + 1,
                max_retries + 1,
                err,
                delay,
            )

            await asyncio.sleep(delay)

    # This should never be reached, but just in case
    raise last_exception

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Eight Sleep component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Eight Sleep config entry."""
    if CONF_CLIENT_ID in entry.data:
        client_id = entry.data[CONF_CLIENT_ID]
    else:
        client_id = None
    if CONF_CLIENT_SECRET in entry.data:
        client_secret = entry.data[CONF_CLIENT_SECRET]
    else:
        client_secret = None

    # Create offline manager
    offline_manager = create_offline_manager(hass, entry)
    await offline_manager.initialize()

    eight = EightSleep(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        hass.config.time_zone,
        client_id,
        client_secret,
        client_session=async_get_clientsession(hass),
        httpx_client=get_async_client(hass)
    )

    # Authenticate with retry logic
    try:
        success = await _async_retry_with_backoff(eight.start)
        offline_manager.mark_connection_success()
    except Exception as err:
        offline_manager.mark_connection_error()

        # Get user-friendly error message
        error_info = get_user_friendly_error(err, "Eight Sleep API")
        _LOGGER.error(
            "%s: %s. %s",
            error_info["title"],
            error_info["message"],
            error_info["suggestion"]
        )

        # Create notification for user
        notification_data = create_notification_data(
            categorize_error(str(err)),
            entity_id="",
            error_details=str(err)
        )

        # Log the notification data for debugging
        _LOGGER.debug("Error notification data: %s", notification_data)

        await handle_api_error(err, "Eight Sleep API", offline_manager)
        raise ConfigEntryNotReady from err

    if not success:
        error_info = get_error_message("authentication_failed")
        _LOGGER.error(
            "%s: %s. %s",
            error_info["title"],
            error_info["message"],
            error_info["suggestion"]
        )
        return False

    # Initialize hass.data[DOMAIN] if it doesn't exist
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Create coordinators with enhanced error handling and offline support
    async def device_update_method():
        """Update device data with retry logic and offline support."""
        try:
            return await offline_manager.get_data_with_fallback(
                "device_data",
                _async_retry_with_backoff,
                eight.update_device_data
            )
        except Exception as err:
            error_info = get_user_friendly_error(err, "device data")
            _LOGGER.warning(
                "%s: %s. %s",
                error_info["title"],
                error_info["message"],
                error_info["suggestion"]
            )
            await handle_api_error(err, "device data", offline_manager)
            raise

    async def user_update_method():
        """Update user data with retry logic and offline support."""
        try:
            return await offline_manager.get_data_with_fallback(
                "user_data",
                _async_retry_with_backoff,
                eight.update_user_data
            )
        except Exception as err:
            error_info = get_user_friendly_error(err, "user data")
            _LOGGER.warning(
                "%s: %s. %s",
                error_info["title"],
                error_info["message"],
                error_info["suggestion"]
            )
            await handle_api_error(err, "user data", offline_manager)
            raise

    async def base_update_method():
        """Update base data with retry logic and offline support."""
        try:
            return await offline_manager.get_data_with_fallback(
                "base_data",
                _async_retry_with_backoff,
                eight.update_base_data
            )
        except Exception as err:
            error_info = get_user_friendly_error(err, "base data")
            _LOGGER.warning(
                "%s: %s. %s",
                error_info["title"],
                error_info["message"],
                error_info["suggestion"]
            )
            await handle_api_error(err, "base data", offline_manager)
            raise

    device_coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_device",
        update_interval=DEVICE_SCAN_INTERVAL,
        update_method=device_update_method,
    )
    user_coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_user",
        update_interval=USER_SCAN_INTERVAL,
        update_method=user_update_method,
    )
    base_coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_base",
        update_interval=BASE_SCAN_INTERVAL,
        update_method=base_update_method,
    )

    # Initialize coordinators with retry logic
    try:
        await _async_retry_with_backoff(device_coordinator.async_config_entry_first_refresh)
        await _async_retry_with_backoff(user_coordinator.async_config_entry_first_refresh)
        await _async_retry_with_backoff(base_coordinator.async_config_entry_first_refresh)
    except Exception as err:
        _LOGGER.error("Failed to initialize coordinators: %s", err)
        raise ConfigEntryNotReady from err

    if not eight.users:
        _LOGGER.error("No users found for Eight Sleep device")
        return False

    dev_reg = async_get(hass)
    assert eight.device_data
    device_data = {
        ATTR_MANUFACTURER: "Eight Sleep",
        ATTR_MODEL: eight.device_data.get("modelString", UNDEFINED),
        ATTR_HW_VERSION: eight.device_data.get("sensorInfo", {}).get(
            "hwRevision", UNDEFINED
        ),
        ATTR_SW_VERSION: eight.device_data.get("firmwareVersion", UNDEFINED),
    }
    dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, _get_device_unique_id(eight))},
        name=f"{entry.data[CONF_USERNAME]}'s Eight Sleep",
        **device_data,
    )
    for user in eight.users.values():
        assert user.user_profile

        dev_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, _get_device_unique_id(eight, user))},
            name=f"{user.user_profile['firstName']}'s Eight Sleep Side",
            via_device=(DOMAIN, _get_device_unique_id(eight)),
            **device_data,
        )

    if eight.base_user:
        base_hardware_info = eight.base_user.base_data.get("hardwareInfo", {})
        base_device_data = {
            ATTR_MANUFACTURER: "Eight Sleep",
            ATTR_MODEL: base_hardware_info['sku'],
            ATTR_HW_VERSION: base_hardware_info['hardwareVersion'],
            ATTR_SW_VERSION: base_hardware_info['softwareVersion'],
        }

        dev_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, _get_device_unique_id(eight, base_entity=True))},
            name=f"{entry.data[CONF_USERNAME]}'s Base",
            via_device=(DOMAIN, _get_device_unique_id(eight)),
            **base_device_data,
        )

    hass.data[DOMAIN][entry.entry_id] = EightSleepConfigEntryData(
        eight, device_coordinator, user_coordinator, base_coordinator, offline_manager
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register device actions
    hass.data[DOMAIN][entry.entry_id].device_actions = device_actions

    # Set up health check and error reporting services
    from .health_check import async_setup_health_services
    from .error_reporting import async_setup_error_reporting_services

    await async_setup_health_services(hass, entry)
    await async_setup_error_reporting_services(hass, entry)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # stop the API before unloading everything
        config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][entry.entry_id]
        await config_entry_data.api.stop()
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok

class EightSleepBaseEntity(CoordinatorEntity[DataUpdateCoordinator]):
    """The base Eight Sleep entity class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator,
        eight: EightSleep,
        user: EightUser | None,
        sensor_name: str,
        base_entity: bool = False
    ) -> None:
        """Initialize the data object."""
        super().__init__(coordinator)
        self._config_entry = entry
        self._eight = eight
        self._sensor = sensor_name
        self._user_obj = user

        self._attr_name = str(NAME_MAP.get(sensor_name, sensor_name.replace("_", " ").title()))

        device_id = _get_device_unique_id(eight, self._user_obj, base_entity)
        self._attr_unique_id = f"{device_id}.{sensor_name}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})

    async def _generic_service_call(self, service_method):
        """Generic service call with retry logic."""
        if self._user_obj is None:
            error_info = get_error_message("device_not_found")
            raise HomeAssistantError(
                f"{error_info['title']}: {error_info['message']}. {error_info['suggestion']}"
            )

        try:
            return await _async_retry_with_backoff(service_method)
        except Exception as err:
            error_info = get_user_friendly_error(err, self._attr_unique_id)
            _LOGGER.error(
                "Service call failed for %s: %s. %s",
                self._attr_unique_id,
                error_info["message"],
                error_info["suggestion"]
            )
            raise HomeAssistantError(
                f"{error_info['title']}: {error_info['message']}. {error_info['suggestion']}"
            ) from err

    async def async_heat_set(
        self, target: int, duration: int, sleep_stage: str
    ) -> None:
        """Set the bed temperature."""
        await self._generic_service_call(
            lambda: self._user_obj.heat_set(target, duration, sleep_stage)
        )

    async def async_heat_increment(self, target: int) -> None:
        """Increment the bed temperature."""
        await self._generic_service_call(
            lambda: self._user_obj.heat_increment(target)
        )

    async def async_side_off(
        self,
    ) -> None:
        """Turn off the bed side."""
        await self._generic_service_call(
            lambda: self._user_obj.side_off()
        )

    async def async_side_on(
        self,
    ) -> None:
        """Turn on the bed side."""
        await self._generic_service_call(
            lambda: self._user_obj.side_on()
        )

    async def async_alarm_snooze(self, duration: int) -> None:
        """Snooze the alarm."""
        await self._generic_service_call(
            lambda: self._user_obj.alarm_snooze(duration)
        )

    async def async_alarm_stop(self) -> None:
        """Stop the alarm."""
        await self._generic_service_call(
            lambda: self._user_obj.alarm_stop()
        )

    async def async_alarm_dismiss(self) -> None:
        """Dismiss the alarm."""
        await self._generic_service_call(
            lambda: self._user_obj.alarm_dismiss()
        )

    async def async_start_away_mode(
        self,
    ) -> None:
        """Start away mode."""
        await self._generic_service_call(
            lambda: self._user_obj.start_away_mode()
        )

    async def async_stop_away_mode(
        self,
    ) -> None:
        """Stop away mode."""
        await self._generic_service_call(
            lambda: self._user_obj.stop_away_mode()
        )

    async def async_prime_pod(
        self,
    ) -> None:
        """Prime the pod."""
        await self._generic_service_call(
            lambda: self._user_obj.prime_pod()
        )

    async def async_set_bed_side(self, bed_side_state: str) -> None:
        """Set the bed side state."""
        await self._generic_service_call(
            lambda: self._user_obj.set_bed_side(bed_side_state)
        )
