"""User-friendly error messages for Eight Sleep integration."""

from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Error message templates
ERROR_MESSAGES = {
    "authentication_failed": {
        "title": "Authentication Failed",
        "message": "Unable to connect to Eight Sleep. Please check your username and password.",
        "suggestion": "Verify your credentials in the integration settings and try again.",
        "severity": "error",
    },
    "connection_timeout": {
        "title": "Connection Timeout",
        "message": "The connection to Eight Sleep timed out.",
        "suggestion": "Check your internet connection and try again in a few minutes.",
        "severity": "warning",
    },
    "rate_limit_exceeded": {
        "title": "Rate Limit Exceeded",
        "message": "Too many requests to Eight Sleep API.",
        "suggestion": "The integration will automatically retry. Please wait a few minutes.",
        "severity": "warning",
    },
    "api_unavailable": {
        "title": "Eight Sleep Service Unavailable",
        "message": "Eight Sleep services are currently unavailable.",
        "suggestion": "The integration will use cached data. Please try again later.",
        "severity": "warning",
    },
    "device_not_found": {
        "title": "Device Not Found",
        "message": "Your Eight Sleep device could not be found.",
        "suggestion": "Ensure your device is connected and try restarting the integration.",
        "severity": "error",
    },
    "data_sync_failed": {
        "title": "Data Sync Failed",
        "message": "Unable to sync sleep data from Eight Sleep.",
        "suggestion": "Check your device connection and try refreshing the integration.",
        "severity": "warning",
    },
    "offline_mode": {
        "title": "Using Offline Mode",
        "message": "Eight Sleep API is unavailable. Using cached data.",
        "suggestion": "Some features may be limited. Data will sync when connection is restored.",
        "severity": "info",
    },
    "invalid_credentials": {
        "title": "Invalid Credentials",
        "message": "Your Eight Sleep credentials are invalid.",
        "suggestion": "Please update your username and password in the integration settings.",
        "severity": "error",
    },
    "network_error": {
        "title": "Network Error",
        "message": "Network connection to Eight Sleep failed.",
        "suggestion": "Check your internet connection and firewall settings.",
        "severity": "warning",
    },
    "service_unavailable": {
        "title": "Service Temporarily Unavailable",
        "message": "Eight Sleep services are temporarily unavailable.",
        "suggestion": "Please try again in a few minutes.",
        "severity": "warning",
    },
    "data_parsing_error": {
        "title": "Data Processing Error",
        "message": "Unable to process sleep data from Eight Sleep.",
        "suggestion": "Try restarting the integration or contact support if the issue persists.",
        "severity": "error",
    },
    "device_offline": {
        "title": "Device Offline",
        "message": "Your Eight Sleep device appears to be offline.",
        "suggestion": "Check your device's power and internet connection.",
        "severity": "warning",
    },
    "permission_denied": {
        "title": "Access Denied",
        "message": "You don't have permission to access this Eight Sleep account.",
        "suggestion": "Check your account permissions or contact Eight Sleep support.",
        "severity": "error",
    },
    "account_locked": {
        "title": "Account Locked",
        "message": "Your Eight Sleep account has been temporarily locked.",
        "suggestion": "Please contact Eight Sleep support to unlock your account.",
        "severity": "error",
    },
    "maintenance_mode": {
        "title": "Eight Sleep Maintenance",
        "message": "Eight Sleep is currently undergoing maintenance.",
        "suggestion": "Please try again later when maintenance is complete.",
        "severity": "info",
    },
}

# Error categories for grouping
ERROR_CATEGORIES = {
    "connection": [
        "connection_timeout",
        "network_error",
        "api_unavailable",
        "service_unavailable",
    ],
    "authentication": [
        "authentication_failed",
        "invalid_credentials",
        "permission_denied",
        "account_locked",
    ],
    "device": [
        "device_not_found",
        "device_offline",
    ],
    "data": [
        "data_sync_failed",
        "data_parsing_error",
    ],
    "system": [
        "rate_limit_exceeded",
        "offline_mode",
        "maintenance_mode",
    ],
}

def get_error_message(error_type: str, **kwargs: Any) -> dict[str, Any]:
    """Get a user-friendly error message for the given error type."""
    if error_type not in ERROR_MESSAGES:
        # Default error message
        return {
            "title": "Unknown Error",
            "message": f"An unexpected error occurred: {error_type}",
            "suggestion": "Please try again or contact support if the issue persists.",
            "severity": "error",
        }

    message = ERROR_MESSAGES[error_type].copy()

    # Replace placeholders with provided values
    for key, value in kwargs.items():
        if isinstance(message.get("message"), str):
            message["message"] = message["message"].replace(f"{{{key}}}", str(value))
        if isinstance(message.get("suggestion"), str):
            message["suggestion"] = message["suggestion"].replace(f"{{{key}}}", str(value))

    return message

def categorize_error(error_type: str) -> str:
    """Categorize an error type into a general category."""
    for category, error_types in ERROR_CATEGORIES.items():
        if error_type in error_types:
            return category
    return "unknown"

def get_error_severity(error_type: str) -> str:
    """Get the severity level for an error type."""
    message = get_error_message(error_type)
    return message.get("severity", "error")

def format_error_for_logging(error_type: str, error_details: str = "", **kwargs: Any) -> str:
    """Format an error message for logging."""
    message = get_error_message(error_type, **kwargs)

    log_message = f"{message['title']}: {message['message']}"
    if error_details:
        log_message += f" (Details: {error_details})"
    if kwargs:
        log_message += f" (Context: {kwargs})"

    return log_message

def get_user_friendly_error(error: Exception, context: str = "") -> dict[str, Any]:
    """Convert an exception to a user-friendly error message."""
    error_str = str(error).lower()

    # Map common error patterns to user-friendly messages
    if "timeout" in error_str or "timed out" in error_str:
        return get_error_message("connection_timeout")
    elif "401" in error_str or "unauthorized" in error_str:
        return get_error_message("invalid_credentials")
    elif "403" in error_str or "forbidden" in error_str:
        return get_error_message("permission_denied")
    elif "404" in error_str or "not found" in error_str:
        return get_error_message("device_not_found")
    elif "429" in error_str or "rate limit" in error_str:
        return get_error_message("rate_limit_exceeded")
    elif "500" in error_str or "server error" in error_str:
        return get_error_message("service_unavailable")
    elif "connection" in error_str or "network" in error_str:
        return get_error_message("network_error")
    elif "authentication" in error_str or "login" in error_str:
        return get_error_message("authentication_failed")
    elif "maintenance" in error_str:
        return get_error_message("maintenance_mode")
    elif "offline" in error_str:
        return get_error_message("device_offline")
    else:
        # Generic error message
        return {
            "title": "Integration Error",
            "message": f"An error occurred while communicating with Eight Sleep: {str(error)}",
            "suggestion": "Please try again or restart the integration. If the problem persists, contact support.",
            "severity": "error",
        }

def create_notification_data(error_type: str, entity_id: str = "", **kwargs: Any) -> dict[str, Any]:
    """Create notification data for displaying error messages to users."""
    error_message = get_error_message(error_type, **kwargs)

    notification_data = {
        "title": error_message["title"],
        "message": error_message["message"],
        "data": {
            "suggestion": error_message["suggestion"],
            "severity": error_message["severity"],
            "error_type": error_type,
            "entity_id": entity_id,
            "category": categorize_error(error_type),
        }
    }

    return notification_data
