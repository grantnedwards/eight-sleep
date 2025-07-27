"""Error reporting system for Eight Sleep integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
import voluptuous as vol

from .const import DOMAIN
from .error_messages import get_error_message, categorize_error, get_user_friendly_error
from .util import EightSleepOfflineManager

_LOGGER = logging.getLogger(__name__)

# Service schemas
ERROR_REPORT_SCHEMA = vol.Schema({
    vol.Optional("include_history", default=True): cv.boolean,
    vol.Optional("include_diagnostics", default=False): cv.boolean,
})

ERROR_NOTIFICATION_SCHEMA = vol.Schema({
    vol.Required("error_type"): cv.string,
    vol.Optional("entity_id", default=""): cv.string,
    vol.Optional("error_details", default=""): cv.string,
    vol.Optional("severity", default="warning"): vol.In(["info", "warning", "error"]),
})

class ErrorReport:
    """Represents an error report with metadata."""

    def __init__(self, error_type: str, message: str, severity: str = "warning"):
        """Initialize the error report."""
        self.error_type = error_type
        self.message = message
        self.severity = severity
        self.timestamp = datetime.now()
        self.entity_id = ""
        self.error_details = ""
        self.resolved = False
        self.resolution_time = None

    def resolve(self):
        """Mark the error as resolved."""
        self.resolved = True
        self.resolution_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "entity_id": self.entity_id,
            "error_details": self.error_details,
            "resolved": self.resolved,
            "resolution_time": self.resolution_time.isoformat() if self.resolution_time else None,
        }

class EightSleepErrorReporter:
    """Error reporter for Eight Sleep integration."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        """Initialize the error reporter."""
        self.hass = hass
        self.config_entry = config_entry
        self._error_reports: List[ErrorReport] = []
        self._notification_history: List[Dict[str, Any]] = []
        self._max_error_history = 50
        self._max_notification_history = 20

    def add_error_report(
        self,
        error_type: str,
        message: str,
        severity: str = "warning",
        entity_id: str = "",
        error_details: str = ""
    ) -> ErrorReport:
        """Add a new error report."""
        error_report = ErrorReport(error_type, message, severity)
        error_report.entity_id = entity_id
        error_report.error_details = error_details

        self._error_reports.append(error_report)

        # Keep only the most recent error reports
        if len(self._error_reports) > self._max_error_history:
            self._error_reports.pop(0)

        _LOGGER.debug("Added error report: %s - %s", error_type, message)
        return error_report

    def add_notification(
        self,
        error_type: str,
        entity_id: str = "",
        error_details: str = "",
        severity: str = "warning"
    ) -> Dict[str, Any]:
        """Add a notification for the user interface."""
        error_message = get_error_message(error_type)

        notification_data = {
            "title": error_message["title"],
            "message": error_message["message"],
            "suggestion": error_message["suggestion"],
            "severity": severity,
            "error_type": error_type,
            "entity_id": entity_id,
            "error_details": error_details,
            "category": categorize_error(error_type),
            "timestamp": datetime.now().isoformat(),
        }

        self._notification_history.append(notification_data)

        # Keep only the most recent notifications
        if len(self._notification_history) > self._max_notification_history:
            self._notification_history.pop(0)

        _LOGGER.info("Added notification: %s - %s", error_type, error_message["message"])
        return notification_data

    def get_active_errors(self) -> List[ErrorReport]:
        """Get all active (unresolved) error reports."""
        return [report for report in self._error_reports if not report.resolved]

    def get_error_history(self, days: int = 7) -> List[ErrorReport]:
        """Get error reports from the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [
            report for report in self._error_reports
            if report.timestamp >= cutoff_date
        ]

    def get_notification_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get notification history from the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [
            notification for notification in self._notification_history
            if datetime.fromisoformat(notification["timestamp"]) >= cutoff_date
        ]

    def resolve_error(self, error_type: str, entity_id: str = "") -> bool:
        """Resolve an error by type and optionally entity_id."""
        resolved_count = 0

        for report in self._error_reports:
            if (report.error_type == error_type and
                (not entity_id or report.entity_id == entity_id) and
                not report.resolved):
                report.resolve()
                resolved_count += 1

        if resolved_count > 0:
            _LOGGER.info("Resolved %d error(s) of type: %s", resolved_count, error_type)

        return resolved_count > 0

    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of error statistics."""
        total_errors = len(self._error_reports)
        active_errors = len(self.get_active_errors())
        resolved_errors = total_errors - active_errors

        # Count by severity
        severity_counts = {"info": 0, "warning": 0, "error": 0}
        for report in self._error_reports:
            severity_counts[report.severity] += 1

        # Count by category
        category_counts = {}
        for report in self._error_reports:
            category = categorize_error(report.error_type)
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "total_errors": total_errors,
            "active_errors": active_errors,
            "resolved_errors": resolved_errors,
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "resolution_rate": (resolved_errors / total_errors * 100) if total_errors > 0 else 0,
        }

    async def generate_error_report(
        self,
        include_history: bool = True,
        include_diagnostics: bool = False
    ) -> Dict[str, Any]:
        """Generate a comprehensive error report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "config_entry_id": self.config_entry.entry_id,
            "error_summary": self.get_error_summary(),
            "active_errors": [report.to_dict() for report in self.get_active_errors()],
            "recent_notifications": self.get_notification_history(1),  # Last 24 hours
        }

        if include_history:
            report["error_history"] = [report.to_dict() for report in self.get_error_history()]
            report["notification_history"] = self.get_notification_history()

        if include_diagnostics:
            try:
                from .diagnostics import create_diagnostic_report
                report["diagnostics"] = await create_diagnostic_report(
                    self.hass, self.config_entry
                )
            except Exception as err:
                report["diagnostics_error"] = str(err)

        return report

    def clear_old_errors(self, days: int = 30) -> int:
        """Clear error reports older than N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        original_count = len(self._error_reports)

        self._error_reports = [
            report for report in self._error_reports
            if report.timestamp >= cutoff_date
        ]

        cleared_count = original_count - len(self._error_reports)
        if cleared_count > 0:
            _LOGGER.info("Cleared %d old error reports", cleared_count)

        return cleared_count

class EightSleepErrorReportingEntity(Entity):
    """Entity for displaying error reporting information."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        """Initialize the error reporting entity."""
        self.hass = hass
        self.config_entry = config_entry
        self._attr_name = "Eight Sleep Error Reporting"
        self._attr_unique_id = f"{config_entry.entry_id}_error_reporting"
        self._attr_icon = "mdi:alert-circle"
        self._attr_entity_category = "diagnostic"

    @property
    def state(self) -> str:
        """Return the state of the entity."""
        try:
            config_entry_data = self.hass.data[DOMAIN][self.config_entry.entry_id]
            offline_manager = config_entry_data.offline_manager

            if offline_manager.is_offline:
                return "offline"
            elif offline_manager.connection_status.connection_errors > 0:
                return "degraded"
            else:
                return "healthy"
        except Exception:
            return "unknown"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        try:
            config_entry_data = self.hass.data[DOMAIN][self.config_entry.entry_id]
            offline_manager = config_entry_data.offline_manager

            return {
                "connection_status": offline_manager.get_offline_status_message(),
                "connection_errors": offline_manager.connection_status.connection_errors,
                "success_rate": offline_manager.connection_status.success_rate,
                "last_online": offline_manager.connection_status.last_online.isoformat(),
                "cache_hit_rate": offline_manager.cache.get_cache_stats()["hit_rate"],
            }
        except Exception:
            return {}

async def async_setup_error_reporting_services(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Set up error reporting services."""

    error_reporter = EightSleepErrorReporter(hass, config_entry)

    async def error_report_service(call: ServiceCall) -> None:
        """Service to generate error report."""
        include_history = call.data.get("include_history", True)
        include_diagnostics = call.data.get("include_diagnostics", False)

        report = error_reporter.generate_error_report(include_history, include_diagnostics)

        # Store report in hass data for potential UI access
        hass.data.setdefault(f"{DOMAIN}_error_reports", {})
        hass.data[f"{DOMAIN}_error_reports"][config_entry.entry_id] = report

        _LOGGER.info("Error report generated with %d active errors",
                    report["error_summary"]["active_errors"])

    async def error_notification_service(call: ServiceCall) -> None:
        """Service to add error notification."""
        error_type = call.data["error_type"]
        entity_id = call.data.get("entity_id", "")
        error_details = call.data.get("error_details", "")
        severity = call.data.get("severity", "warning")

        notification = error_reporter.add_notification(
            error_type, entity_id, error_details, severity
        )

        # Store notification in hass data for potential UI access
        hass.data.setdefault(f"{DOMAIN}_notifications", {})
        if config_entry.entry_id not in hass.data[f"{DOMAIN}_notifications"]:
            hass.data[f"{DOMAIN}_notifications"][config_entry.entry_id] = []
        hass.data[f"{DOMAIN}_notifications"][config_entry.entry_id].append(notification)

        _LOGGER.info("Error notification added: %s", notification["title"])

    # Register services
    hass.services.async_register(
        DOMAIN,
        "error_report",
        error_report_service,
        schema=ERROR_REPORT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "error_notification",
        error_notification_service,
        schema=ERROR_NOTIFICATION_SCHEMA,
    )
