"""Diagnostic information and troubleshooting tools for Eight Sleep integration."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.entity_registry import RegistryEntry

from . import EightSleepConfigEntryData
from .const import DOMAIN
from .error_messages import get_error_message, categorize_error
from .util import EightSleepOfflineManager

_LOGGER = logging.getLogger(__name__)

class EightSleepDiagnostics:
    """Diagnostic information collector for Eight Sleep integration."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        """Initialize the diagnostics collector."""
        self.hass = hass
        self.config_entry = config_entry
        self.diagnostics_data: Dict[str, Any] = {}

    async def collect_diagnostics(self) -> Dict[str, Any]:
        """Collect comprehensive diagnostic information."""
        try:
            self.diagnostics_data = {
                "integration_info": await self._get_integration_info(),
                "config_entry_info": await self._get_config_entry_info(),
                "device_info": await self._get_device_info(),
                "entity_info": await self._get_entity_info(),
                "api_status": await self._get_api_status(),
                "connection_info": await self._get_connection_info(),
                "error_history": await self._get_error_history(),
                "performance_metrics": await self._get_performance_metrics(),
                "troubleshooting_suggestions": await self._get_troubleshooting_suggestions(),
                "timestamp": datetime.now().isoformat(),
            }

            return self.diagnostics_data

        except Exception as err:
            _LOGGER.error("Error collecting diagnostics: %s", err)
            return {"error": str(err), "timestamp": datetime.now().isoformat()}

    async def _get_integration_info(self) -> Dict[str, Any]:
        """Get basic integration information."""
        return {
            "domain": DOMAIN,
            "version": "1.0.0",  # This should come from manifest
            "config_entry_id": self.config_entry.entry_id,
            "config_entry_title": self.config_entry.title,
            "config_entry_source": self.config_entry.source,
            "config_entry_state": self.config_entry.state.value,
            "config_entry_disabled_by": self.config_entry.disabled_by,
            "config_entry_pref_disable_new_entities": self.config_entry.pref_disable_new_entities,
            "config_entry_pref_disable_polling": self.config_entry.pref_disable_polling,
        }

    async def _get_config_entry_info(self) -> Dict[str, Any]:
        """Get configuration entry information."""
        data = self.config_entry.data
        return {
            "username": data.get(CONF_USERNAME, "not_set"),
            "has_password": bool(data.get("password")),
            "has_client_id": bool(data.get("client_id")),
            "has_client_secret": bool(data.get("client_secret")),
            "timezone": self.hass.config.time_zone,
            "latitude": self.hass.config.latitude,
            "longitude": self.hass.config.longitude,
        }

    async def _get_device_info(self) -> Dict[str, Any]:
        """Get device registry information."""
        device_registry = dr.async_get(self.hass)
        devices = []

        for device in device_registry.devices.values():
            if DOMAIN in device.identifiers:
                device_info = {
                    "device_id": device.id,
                    "name": device.name,
                    "model": device.model,
                    "manufacturer": device.manufacturer,
                    "sw_version": device.sw_version,
                    "hw_version": device.hw_version,
                    "config_entries": list(device.config_entries),
                    "connections": list(device.connections),
                    "identifiers": list(device.identifiers),
                    "disabled_by": device.disabled_by,
                    "entry_type": device.entry_type,
                }
                devices.append(device_info)

        return {"devices": devices, "total_devices": len(devices)}

    async def _get_entity_info(self) -> Dict[str, Any]:
        """Get entity registry information."""
        entity_registry = er.async_get(self.hass)
        entities = []

        for entity in entity_registry.entities.values():
            if entity.platform == DOMAIN:
                entity_info = {
                    "entity_id": entity.entity_id,
                    "unique_id": entity.unique_id,
                    "name": entity.name,
                    "original_name": entity.original_name,
                    "device_id": entity.device_id,
                    "platform": entity.platform,
                    "disabled_by": entity.disabled_by,
                    "hidden_by": entity.hidden_by,
                    "capabilities": entity.capabilities,
                    "supported_features": entity.supported_features,
                    "unit_of_measurement": entity.unit_of_measurement,
                    "device_class": entity.device_class,
                    "state_class": entity.state_class,
                }
                entities.append(entity_info)

        return {"entities": entities, "total_entities": len(entities)}

    async def _get_api_status(self) -> Dict[str, Any]:
        """Get API connection status and health."""
        try:
            config_entry_data: EightSleepConfigEntryData = self.hass.data[DOMAIN][self.config_entry.entry_id]
            eight = config_entry_data.api
            offline_manager = config_entry_data.offline_manager

            api_status = {
                "is_online": not offline_manager.is_offline,
                "last_online": offline_manager.last_online.isoformat() if offline_manager.last_online else None,
                "connection_errors": getattr(offline_manager, '_connection_errors', 0),
                "device_id": eight.device_id,
                "user_count": len(eight.users) if eight.users else 0,
                "has_device_data": bool(eight.device_data),
                "has_base_user": bool(eight.base_user),
                "is_pod": eight.is_pod,
                "has_base": eight.has_base,
                "need_priming": eight.need_priming,
                "is_priming": eight.is_priming,
                "has_water": eight.has_water,
            }

            # Test API connectivity
            try:
                # Simple API test
                await eight.update_device_data()
                api_status["api_test"] = "success"
            except Exception as err:
                api_status["api_test"] = f"failed: {str(err)}"

            return api_status

        except Exception as err:
            return {"error": str(err)}

    async def _get_connection_info(self) -> Dict[str, Any]:
        """Get connection and network information."""
        try:
            config_entry_data: EightSleepConfigEntryData = self.hass.data[DOMAIN][self.config_entry.entry_id]
            offline_manager = config_entry_data.offline_manager

            return {
                "offline_mode": offline_manager.is_offline,
                "offline_status_message": offline_manager.get_offline_status_message(),
                "cache_valid": offline_manager.cache.is_cache_valid(),
                "cache_last_update": offline_manager.cache._last_update.isoformat() if offline_manager.cache._last_update else None,    
                "cache_size": len(offline_manager.cache._cache),
                "connection_errors": getattr(offline_manager, '_connection_errors', 0),
                "max_connection_errors": getattr(offline_manager, '_max_connection_errors', 3),
            }

        except Exception as err:
            return {"error": str(err)}

    async def _get_error_history(self) -> Dict[str, Any]:
        """Get recent error history and patterns."""
        # This would typically come from a persistent error log
        # For now, we'll return a placeholder structure
        return {
            "recent_errors": [],
            "error_patterns": {},
            "most_common_errors": [],
            "error_frequency": {},
        }

    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance and timing metrics."""
        try:
            config_entry_data: EightSleepConfigEntryData = self.hass.data[DOMAIN][self.config_entry.entry_id]

            return {
                "device_coordinator_last_update": config_entry_data.device_coordinator.last_update_success.isoformat() if config_entry_data.device_coordinator.last_update_success else None,    
                "user_coordinator_last_update": config_entry_data.user_coordinator.last_update_success.isoformat() if config_entry_data.user_coordinator.last_update_success else None,    
                "base_coordinator_last_update": config_entry_data.base_coordinator.last_update_success.isoformat() if config_entry_data.base_coordinator.last_update_success else None,    
                "device_coordinator_update_interval": str(config_entry_data.device_coordinator.update_interval),
                "user_coordinator_update_interval": str(config_entry_data.user_coordinator.update_interval),
                "base_coordinator_update_interval": str(config_entry_data.base_coordinator.update_interval),
            }

        except Exception as err:
            return {"error": str(err)}

    async def _get_troubleshooting_suggestions(self) -> Dict[str, Any]:
        """Get troubleshooting suggestions based on current state."""
        suggestions = []

        try:
            config_entry_data: EightSleepConfigEntryData = self.hass.data[DOMAIN][self.config_entry.entry_id]
            offline_manager = config_entry_data.offline_manager

            # Check for common issues and provide suggestions
            if offline_manager.is_offline:
                suggestions.append({
                    "issue": "API is offline",
                    "suggestion": "Check internet connection and Eight Sleep service status",
                    "severity": "warning"
                })

            if getattr(offline_manager, '_connection_errors', 0) > 0:
                suggestions.append({
                    "issue": "Connection errors detected",
                    "suggestion": "Check network connectivity and firewall settings",
                    "severity": "warning"
                })

            if not config_entry_data.api.device_data:
                suggestions.append({
                    "issue": "No device data available",
                    "suggestion": "Verify device is connected and try restarting the integration",
                    "severity": "error"
                })

            if not config_entry_data.api.users:
                suggestions.append({
                    "issue": "No user data available",
                    "suggestion": "Check account permissions and device setup",
                    "severity": "error"
                })

            # Add general suggestions
            suggestions.extend([
                {
                    "issue": "General maintenance",
                    "suggestion": "Restart Home Assistant if experiencing persistent issues",
                    "severity": "info"
                },
                {
                    "issue": "Log analysis",
                    "suggestion": "Check Home Assistant logs for detailed error information",
                    "severity": "info"
                }
            ])

        except Exception as err:
            suggestions.append({
                "issue": "Diagnostic error",
                "suggestion": f"Error collecting diagnostics: {str(err)}",
                "severity": "error"
            })

        return {"suggestions": suggestions, "total_suggestions": len(suggestions)}

async def create_diagnostic_report(hass: HomeAssistant, config_entry: ConfigEntry) -> Dict[str, Any]:
    """Create a comprehensive diagnostic report."""
    diagnostics = EightSleepDiagnostics(hass, config_entry)
    return await diagnostics.collect_diagnostics()

async def export_diagnostics_to_file(hass: HomeAssistant, config_entry: ConfigEntry, file_path: str) -> bool:
    """Export diagnostic information to a JSON file."""
    try:
        diagnostics = await create_diagnostic_report(hass, config_entry)

        with open(file_path, 'w') as f:
            json.dump(diagnostics, f, indent=2, default=str)

        _LOGGER.info("Diagnostic report exported to %s", file_path)
        return True

    except Exception as err:
        _LOGGER.error("Failed to export diagnostics: %s", err)
        return False

def get_quick_diagnostics(hass: HomeAssistant, config_entry: ConfigEntry) -> Dict[str, Any]:
    """Get quick diagnostic information without async operations."""
    try:
        config_entry_data: EightSleepConfigEntryData = hass.data[DOMAIN][config_entry.entry_id]
        offline_manager = config_entry_data.offline_manager

        return {
            "integration_status": "loaded" if DOMAIN in hass.data else "not_loaded",
            "config_entry_state": config_entry.state.value,
            "offline_mode": offline_manager.is_offline,
            "connection_errors": getattr(offline_manager, '_connection_errors', 0),
            "device_count": len(dr.async_get(hass).devices),
            "entity_count": len(er.async_get(hass).entities),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as err:
        return {"error": str(err), "timestamp": datetime.now().isoformat()}
