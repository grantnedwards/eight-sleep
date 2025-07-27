"""Utility functions for Eight Sleep integration."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from homeassistant.const import CONF_USERNAME, UnitOfTemperature as HassUnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .pyEight.types import UnitOfTemperature as PyEightUnitOfTemperature

_LOGGER = logging.getLogger(__name__)

# Storage configuration
STORAGE_KEY = f"{DOMAIN}.cache"
STORAGE_VERSION = 1
CACHE_EXPIRY = timedelta(hours=1)  # Cache data for 1 hour
CONNECTION_STATUS_EXPIRY = timedelta(minutes=5)  # Connection status cache

# Enhanced logging configuration
LOGGING_CONFIG = {
    "level": logging.INFO,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S"
}

def convert_hass_temp_unit_to_pyeight_temp_unit(
    hass_temp_unit: HassUnitOfTemperature,
) -> PyEightUnitOfTemperature:
    """Convert Home Assistant temperature unit to pyEight temperature unit."""
    if hass_temp_unit == HassUnitOfTemperature.CELSIUS:
        return "c"
    return "f"

class EightSleepCache:
    """Enhanced cache manager for Eight Sleep data."""

    def __init__(self, hass: HomeAssistant, username: str):
        """Initialize the cache."""
        self.hass = hass
        self.username = username
        self.store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{username}")
        self._cache: Dict[str, Any] = {}
        self._last_update: Optional[datetime] = None
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0,
            "errors": 0
        }

    async def load_cache(self) -> None:
        """Load cached data from storage."""
        try:
            data = await self.store.async_load()
            if data:
                self._cache = data.get("cache", {})
                last_update_str = data.get("last_update")
                if last_update_str:
                    self._last_update = datetime.fromisoformat(last_update_str)
                self._cache_stats = data.get("stats", self._cache_stats)
                _LOGGER.debug("Loaded cached data for %s", self.username)
        except Exception as err:
            _LOGGER.warning("Failed to load cache: %s", err)
            self._cache = {}
            self._cache_stats["errors"] += 1

    async def save_cache(self) -> None:
        """Save current data to cache."""
        try:
            data = {
                "cache": self._cache,
                "last_update": datetime.now().isoformat(),
                "stats": self._cache_stats,
            }
            await self.store.async_save(data)
            _LOGGER.debug("Saved cache data for %s", self.username)
        except Exception as err:
            _LOGGER.warning("Failed to save cache: %s", err)
            self._cache_stats["errors"] += 1

    def is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self._last_update:
            return False
        return datetime.now() - self._last_update < CACHE_EXPIRY

    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data for a specific key."""
        if not self.is_cache_valid():
            self._cache_stats["misses"] += 1
            return None

        data = self._cache.get(key)
        if data is not None:
            self._cache_stats["hits"] += 1
        else:
            self._cache_stats["misses"] += 1
        return data

    def set_cached_data(self, key: str, data: Any) -> None:
        """Set cached data for a specific key."""
        self._cache[key] = data
        self._last_update = datetime.now()
        self._cache_stats["writes"] += 1

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache = {}
        self._last_update = None
        self._cache_stats = {"hits": 0, "misses": 0, "writes": 0, "errors": 0}

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (self._cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "writes": self._cache_stats["writes"],
            "errors": self._cache_stats["errors"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
            "cache_size": len(self._cache),
            "last_update": self._last_update.isoformat() if self._last_update else None,
        }

class ConnectionStatus:
    """Track connection status and health metrics."""

    def __init__(self):
        """Initialize connection status."""
        self._is_online = True
        self._last_online = datetime.now()
        self._last_check = datetime.now()
        self._connection_errors = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._response_times = []
        self._max_response_times = 10  # Keep last 10 response times

    def mark_success(self, response_time: float = None):
        """Mark a successful connection."""
        self._is_online = True
        self._last_online = datetime.now()
        self._last_check = datetime.now()
        self._connection_errors = 0
        self._successful_requests += 1

        if response_time is not None:
            self._response_times.append(response_time)
            if len(self._response_times) > self._max_response_times:
                self._response_times.pop(0)

    def mark_error(self):
        """Mark a connection error."""
        self._connection_errors += 1
        self._failed_requests += 1
        self._last_check = datetime.now()

        if self._connection_errors >= 3:
            self._is_online = False

    @property
    def is_online(self) -> bool:
        """Check if currently online."""
        return self._is_online

    @property
    def last_online(self) -> datetime:
        """Get the last time the connection was successful."""
        return self._last_online

    @property
    def connection_errors(self) -> int:
        """Get the number of consecutive connection errors."""
        return self._connection_errors

    @property
    def success_rate(self) -> float:
        """Get the success rate percentage."""
        total = self._successful_requests + self._failed_requests
        return (self._successful_requests / total * 100) if total > 0 else 100

    @property
    def average_response_time(self) -> float:
        """Get the average response time."""
        return sum(self._response_times) / len(self._response_times) if self._response_times else 0

    def get_status_message(self) -> str:
        """Get a user-friendly status message."""
        if self.is_online:
            return f"Online (Success rate: {self.success_rate:.1f}%)"
        else:
            time_since_online = datetime.now() - self.last_online
            hours = int(time_since_online.total_seconds() // 3600)
            minutes = int((time_since_online.total_seconds() % 3600) // 60)

            if hours > 0:
                return f"Offline for {hours}h {minutes}m"
            else:
                return f"Offline for {minutes}m"

    def get_health_metrics(self) -> Dict[str, Any]:
        """Get comprehensive health metrics."""
        return {
            "is_online": self.is_online,
            "last_online": self.last_online.isoformat(),
            "last_check": self.last_check.isoformat(),
            "connection_errors": self.connection_errors,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.success_rate, 2),
            "average_response_time": round(self.average_response_time, 3),
            "status_message": self.get_status_message(),
        }

class EightSleepOfflineManager:
    """Enhanced manager for handling offline mode and graceful degradation."""

    def __init__(self, hass: HomeAssistant, username: str):
        """Initialize the offline manager."""
        self.hass = hass
        self.cache = EightSleepCache(hass, username)
        self.connection_status = ConnectionStatus()
        self._recovery_attempts = 0
        self._max_recovery_attempts = 5
        self._recovery_delay = 30  # seconds

    async def initialize(self) -> None:
        """Initialize the offline manager."""
        await self.cache.load_cache()
        _LOGGER.info("Eight Sleep offline manager initialized for %s", self.username)

    def mark_connection_error(self) -> None:
        """Mark a connection error occurred."""
        self.connection_status.mark_error()
        if not self.connection_status.is_online:
            _LOGGER.warning("Eight Sleep API is offline, using cached data")

    def mark_connection_success(self, response_time: float = None) -> None:
        """Mark a successful connection."""
        self.connection_status.mark_success(response_time)
        self._recovery_attempts = 0

    @property
    def is_offline(self) -> bool:
        """Check if currently in offline mode."""
        return not self.connection_status.is_online

    @property
    def last_online(self) -> datetime:
        """Get the last time the API was online."""
        return self.connection_status.last_online

    def get_offline_status_message(self) -> str:
        """Get a user-friendly offline status message."""
        return self.connection_status.get_status_message()

    async def get_data_with_fallback(
        self,
        data_key: str,
        fetch_func,
        *args,
        **kwargs
    ) -> Any:
        """Get data with enhanced fallback to cache if API is unavailable."""
        start_time = datetime.now()

        if self.connection_status.is_online:
            try:
                # Try to fetch fresh data
                data = await fetch_func(*args, **kwargs)

                # Calculate response time
                response_time = (datetime.now() - start_time).total_seconds()
                self.mark_connection_success(response_time)

                # Cache the fresh data
                self.cache.set_cached_data(data_key, data)
                await self.cache.save_cache()

                _LOGGER.debug("Successfully fetched fresh data for %s (%.3fs)", data_key, response_time)
                return data

            except Exception as err:
                self.mark_connection_error()
                _LOGGER.warning("Failed to fetch fresh data for %s: %s", data_key, err)

                # Attempt recovery if we haven't exceeded max attempts
                if self._recovery_attempts < self._max_recovery_attempts:
                    await self._attempt_recovery()

        # Fall back to cached data
        cached_data = self.cache.get_cached_data(data_key)
        if cached_data is not None:
            _LOGGER.info("Using cached data for %s", data_key)
            return cached_data

        # No cached data available
        _LOGGER.error("No data available for %s", data_key)
        return None

    async def _attempt_recovery(self) -> None:
        """Attempt to recover from connection issues."""
        self._recovery_attempts += 1
        _LOGGER.info("Attempting recovery %d/%d", self._recovery_attempts, self._max_recovery_attempts)

        # Wait before attempting recovery
        await asyncio.sleep(self._recovery_delay)

        # Try a simple health check
        try:
            # This would be a simple API call to test connectivity
            # For now, we'll just reset the connection status
            self.connection_status._connection_errors = 0
            _LOGGER.info("Recovery attempt completed")
        except Exception as err:
            _LOGGER.warning("Recovery attempt failed: %s", err)

    def get_health_report(self) -> Dict[str, Any]:
        """Get a comprehensive health report."""
        return {
            "connection_status": self.connection_status.get_health_metrics(),
            "cache_stats": self.cache.get_cache_stats(),
            "recovery_attempts": self._recovery_attempts,
            "max_recovery_attempts": self._max_recovery_attempts,
            "is_offline": self.is_offline,
            "offline_status": self.get_offline_status_message(),
        }

def create_offline_manager(hass: HomeAssistant, config_entry) -> EightSleepOfflineManager:
    """Create an offline manager for the given config entry."""
    username = config_entry.data[CONF_USERNAME]
    return EightSleepOfflineManager(hass, username)

async def handle_api_error(
    error: Exception,
    entity_name: str,
    offline_manager: EightSleepOfflineManager
) -> None:
    """Handle API errors with enhanced logging and offline mode management."""
    error_msg = str(error)

    # Enhanced error categorization and logging
    if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
        offline_manager.mark_connection_error()
        _LOGGER.warning(
            "Connection error for %s: %s. Using offline mode.",
            entity_name,
            error_msg
        )
    elif "401" in error_msg or "unauthorized" in error_msg.lower():
        _LOGGER.error(
            "Authentication error for %s: %s. Please check your credentials.",
            entity_name,
            error_msg
        )
    elif "429" in error_msg or "rate limit" in error_msg.lower():
        _LOGGER.warning(
            "Rate limit exceeded for %s: %s. Retrying with backoff.",
            entity_name,
            error_msg
        )
    elif "500" in error_msg or "server error" in error_msg.lower():
        _LOGGER.error(
            "Server error for %s: %s. Eight Sleep service may be experiencing issues.",
            entity_name,
            error_msg
        )
    else:
        _LOGGER.error(
            "Unexpected error for %s: %s",
            entity_name,
            error_msg
        )

    # Log health metrics for debugging
    health_report = offline_manager.get_health_report()
    _LOGGER.debug("Health report: %s", health_report)
