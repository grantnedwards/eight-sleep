"""Health check system for Eight Sleep integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN
from .util import EightSleepOfflineManager
from .diagnostics import create_diagnostic_report

_LOGGER = logging.getLogger(__name__)

# Service schemas
HEALTH_CHECK_SCHEMA = vol.Schema({
    vol.Optional("detailed", default=False): cv.boolean,
})

PERFORMANCE_CHECK_SCHEMA = vol.Schema({
    vol.Optional("include_cache", default=True): cv.boolean,
    vol.Optional("include_connection", default=True): cv.boolean,
})

CACHE_CLEAR_SCHEMA = vol.Schema({
    vol.Optional("confirm", default=False): cv.boolean,
})

# Health check thresholds
HEALTH_THRESHOLDS = {
    "max_response_time": 5.0,  # seconds
    "min_success_rate": 80.0,  # percentage
    "max_connection_errors": 5,
    "max_cache_errors": 10,
}

class EightSleepHealthChecker:
    """Health checker for Eight Sleep integration."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        """Initialize the health checker."""
        self.hass = hass
        self.config_entry = config_entry
        self._last_health_check = None
        self._health_history = []

    async def perform_health_check(self, detailed: bool = False) -> Dict[str, Any]:
        """Perform a comprehensive health check."""
        try:
            config_entry_data = self.hass.data[DOMAIN][self.config_entry.entry_id]
            offline_manager = config_entry_data.offline_manager

            # Basic health metrics
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "integration_status": "healthy",
                "connection_status": "unknown",
                "cache_status": "unknown",
                "performance_status": "unknown",
                "overall_score": 0,
                "issues": [],
                "recommendations": [],
            }

            # Check connection health
            connection_health = await self._check_connection_health(offline_manager)
            health_report.update(connection_health)

            # Check cache health
            cache_health = await self._check_cache_health(offline_manager)
            health_report.update(cache_health)

            # Check performance
            performance_health = await self._check_performance_health(offline_manager)
            health_report.update(performance_health)

            # Calculate overall score
            health_report["overall_score"] = self._calculate_health_score(health_report)

            # Determine overall status
            if health_report["overall_score"] >= 90:
                health_report["integration_status"] = "excellent"
            elif health_report["overall_score"] >= 75:
                health_report["integration_status"] = "good"
            elif health_report["overall_score"] >= 50:
                health_report["integration_status"] = "fair"
            else:
                health_report["integration_status"] = "poor"

            # Add detailed diagnostics if requested
            if detailed:
                health_report["detailed_diagnostics"] = await create_diagnostic_report(
                    self.hass, self.config_entry
                )

            # Store health check history
            self._last_health_check = datetime.now()
            self._health_history.append(health_report)

            # Keep only last 10 health checks
            if len(self._health_history) > 10:
                self._health_history.pop(0)

            _LOGGER.info("Health check completed: %s (Score: %d)",
                        health_report["integration_status"],
                        health_report["overall_score"])

            return health_report

        except Exception as err:
            _LOGGER.error("Health check failed: %s", err)
            return {
                "timestamp": datetime.now().isoformat(),
                "integration_status": "error",
                "error": str(err),
                "overall_score": 0,
            }

    async def _check_connection_health(self, offline_manager: EightSleepOfflineManager) -> Dict[str, Any]:
        """Check connection health."""
        health_metrics = offline_manager.get_health_report()
        connection_status = health_metrics["connection_status"]

        issues = []
        recommendations = []
        score = 100

        # Check if online
        if not connection_status["is_online"]:
            issues.append("API is offline")
            score -= 30
            recommendations.append("Check internet connection and Eight Sleep service status")

        # Check success rate
        success_rate = connection_status["success_rate"]
        if success_rate < HEALTH_THRESHOLDS["min_success_rate"]:
            issues.append(f"Low success rate: {success_rate:.1f}%")
            score -= 20
            recommendations.append("Check network stability and API rate limits")

        # Check response time
        avg_response_time = connection_status["average_response_time"]
        if avg_response_time > HEALTH_THRESHOLDS["max_response_time"]:
            issues.append(f"Slow response time: {avg_response_time:.2f}s")
            score -= 15
            recommendations.append("Check network latency and API performance")

        # Check connection errors
        connection_errors = connection_status["connection_errors"]
        if connection_errors > HEALTH_THRESHOLDS["max_connection_errors"]:
            issues.append(f"High connection errors: {connection_errors}")
            score -= 25
            recommendations.append("Check network connectivity and firewall settings")

        return {
            "connection_status": "healthy" if score >= 70 else "degraded" if score >= 40 else "poor",
            "connection_score": max(0, score),
            "connection_issues": issues,
            "connection_recommendations": recommendations,
        }

    async def _check_cache_health(self, offline_manager: EightSleepOfflineManager) -> Dict[str, Any]:
        """Check cache health."""
        health_metrics = offline_manager.get_health_report()
        cache_stats = health_metrics["cache_stats"]

        issues = []
        recommendations = []
        score = 100

        # Check cache hit rate
        hit_rate = cache_stats["hit_rate"]
        if hit_rate < 50:
            issues.append(f"Low cache hit rate: {hit_rate:.1f}%")
            score -= 20
            recommendations.append("Consider adjusting cache settings or API polling frequency")

        # Check cache errors
        cache_errors = cache_stats["errors"]
        if cache_errors > HEALTH_THRESHOLDS["max_cache_errors"]:
            issues.append(f"Cache errors: {cache_errors}")
            score -= 30
            recommendations.append("Check storage permissions and disk space")

        # Check cache size
        cache_size = cache_stats["cache_size"]
        if cache_size == 0:
            issues.append("No cached data available")
            score -= 10
            recommendations.append("Integration may not have cached data yet")

        return {
            "cache_status": "healthy" if score >= 70 else "degraded" if score >= 40 else "poor",
            "cache_score": max(0, score),
            "cache_issues": issues,
            "cache_recommendations": recommendations,
        }

    async def _check_performance_health(self, offline_manager: EightSleepOfflineManager) -> Dict[str, Any]:
        """Check performance health."""
        health_metrics = offline_manager.get_health_report()

        issues = []
        recommendations = []
        score = 100

        # Check recovery attempts
        recovery_attempts = health_metrics["recovery_attempts"]
        if recovery_attempts > 0:
            issues.append(f"Recovery attempts: {recovery_attempts}")
            score -= recovery_attempts * 10
            recommendations.append("Monitor connection stability and consider network improvements")

        # Check if using offline mode
        if health_metrics["is_offline"]:
            issues.append("Currently in offline mode")
            score -= 15
            recommendations.append("Check API connectivity and service status")

        return {
            "performance_status": "healthy" if score >= 70 else "degraded" if score >= 40 else "poor",
            "performance_score": max(0, score),
            "performance_issues": issues,
            "performance_recommendations": recommendations,
        }

    def _calculate_health_score(self, health_report: Dict[str, Any]) -> int:
        """Calculate overall health score."""
        scores = [
            health_report.get("connection_score", 0),
            health_report.get("cache_score", 0),
            health_report.get("performance_score", 0),
        ]

        # Weight the scores (connection is most important)
        weighted_score = (
            scores[0] * 0.5 +  # Connection: 50%
            scores[1] * 0.3 +  # Cache: 30%
            scores[2] * 0.2    # Performance: 20%
        )

        return int(weighted_score)

    async def clear_cache(self, confirm: bool = False) -> Dict[str, Any]:
        """Clear the integration cache."""
        if not confirm:
            return {
                "success": False,
                "message": "Cache clear not confirmed. Set confirm: true to proceed.",
            }

        try:
            config_entry_data = self.hass.data[DOMAIN][self.config_entry.entry_id]
            offline_manager = config_entry_data.offline_manager

            # Clear cache
            offline_manager.cache.clear_cache()
            await offline_manager.cache.save_cache()

            _LOGGER.info("Cache cleared successfully")

            return {
                "success": True,
                "message": "Cache cleared successfully",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as err:
            _LOGGER.error("Failed to clear cache: %s", err)
            return {
                "success": False,
                "message": f"Failed to clear cache: {str(err)}",
                "timestamp": datetime.now().isoformat(),
            }

    def get_health_history(self) -> list[Dict[str, Any]]:
        """Get health check history."""
        return self._health_history.copy()

async def async_setup_health_services(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Set up health check services."""

    health_checker = EightSleepHealthChecker(hass, config_entry)

    async def health_check_service(call: ServiceCall) -> None:
        """Service to perform health check."""
        detailed = call.data.get("detailed", False)
        result = await health_checker.perform_health_check(detailed)

        # Log the result
        _LOGGER.info("Health check result: %s (Score: %d)",
                    result["integration_status"],
                    result["overall_score"])

        # Store result in hass data for potential UI access
        hass.data.setdefault(f"{DOMAIN}_health", {})
        hass.data[f"{DOMAIN}_health"][config_entry.entry_id] = result

    async def performance_check_service(call: ServiceCall) -> None:
        """Service to perform performance check."""
        include_cache = call.data.get("include_cache", True)
        include_connection = call.data.get("include_connection", True)

        result = await health_checker.perform_health_check(detailed=True)

        # Filter results based on parameters
        if not include_cache:
            result.pop("cache_status", None)
            result.pop("cache_score", None)
            result.pop("cache_issues", None)
            result.pop("cache_recommendations", None)

        if not include_connection:
            result.pop("connection_status", None)
            result.pop("connection_score", None)
            result.pop("connection_issues", None)
            result.pop("connection_recommendations", None)

        _LOGGER.info("Performance check completed")
        hass.data.setdefault(f"{DOMAIN}_health", {})
        hass.data[f"{DOMAIN}_health"][config_entry.entry_id] = result

    async def clear_cache_service(call: ServiceCall) -> None:
        """Service to clear integration cache."""
        confirm = call.data.get("confirm", False)
        result = await health_checker.clear_cache(confirm)

        if result["success"]:
            _LOGGER.info("Cache cleared successfully")
        else:
            _LOGGER.warning("Cache clear failed: %s", result["message"])

    # Register services
    hass.services.async_register(
        DOMAIN,
        "health_check",
        health_check_service,
        schema=HEALTH_CHECK_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "performance_check",
        performance_check_service,
        schema=PERFORMANCE_CHECK_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "clear_cache",
        clear_cache_service,
        schema=CACHE_CLEAR_SCHEMA,
    )
