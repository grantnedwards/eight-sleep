#!/usr/bin/env python3
"""
Enhanced Eight Sleep API Explorer
Comprehensive reverse engineering of the Eight Sleep API to discover ALL available entities
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
import httpx
from dataclasses import dataclass, asdict
from pathlib import Path
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DiscoveredEntity:
    """Represents a discovered entity from the API"""
    name: str
    type: str
    source_endpoint: str
    description: str
    data_type: str
    example_value: Any
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    path: str = ""
    is_array: bool = False
    array_length: Optional[int] = None

@dataclass
class APIEndpoint:
    """Represents an API endpoint with its metadata"""
    method: str
    url: str
    description: str
    parameters: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    discovered_entities: Optional[List[str]] = None
    status_code: Optional[int] = None
    response_size: Optional[int] = None

class EnhancedEightSleepAPIExplorer:
    """Enhanced API explorer that discovers ALL available entities"""
    
    def __init__(self, email: str, password: str, timezone: str = "UTC"):
        self.email = email
        self.password = password
        self.timezone = timezone
        self.client_id = "0894c7f33bb94800a03f1f4df13a4f38"
        self.client_secret = "f0954a3ed5763ba3d06834c73731a32f15f168f47d4f164751275def86db0c76"
        self.auth_url = "https://auth-api.8slp.net/v1/tokens"
        self.client_api_url = "https://client-api.8slp.net/v1"
        self.app_api_url = "https://app-api.8slp.net"
        
        self._token = None
        self._token_expiration = None
        self._user_id = None
        self._device_ids = []
        self._is_pod = False
        self._has_base = False
        
        self.discovered_entities = []
        self.api_endpoints = []
        self.explored_urls = set()
        self.discovered_urls = set()
        
    async def authenticate(self) -> bool:
        """Authenticate with the Eight Sleep API"""
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "password",
                "username": self.email,
                "password": self.password,
            }
            
            headers = {
                "content-type": "application/json",
                "user-agent": "EnhancedEightSleepAPIExplorer/1.0",
                "accept-encoding": "gzip",
                "accept": "application/json",
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.auth_url,
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    auth_data = response.json()
                    self._token = auth_data["access_token"]
                    self._token_expiration = float(auth_data["expires_in"]) + datetime.now().timestamp()
                    self._user_id = auth_data["userId"]
                    logger.info(f"Successfully authenticated as user {self._user_id}")
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        return {
            "content-type": "application/json",
            "connection": "keep-alive",
            "user-agent": "EnhancedEightSleepAPIExplorer/1.0",
            "accept-encoding": "gzip",
            "accept": "application/json",
            "authorization": f"Bearer {self._token}",
        }
    
    async def api_request(self, method: str, url: str, params: Optional[Dict] = None, 
                         data: Optional[Dict] = None) -> Optional[Dict]:
        """Make an API request with error handling"""
        try:
            headers = self._get_auth_headers()
            
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code == 401:
                    logger.warning("Token expired, attempting to re-authenticate")
                    if await self.authenticate():
                        headers = self._get_auth_headers()
                        response = await client.request(
                            method,
                            url,
                            headers=headers,
                            params=params,
                            json=data,
                            timeout=30.0
                        )
                    else:
                        return None
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"API request failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"API request error: {e}")
            return None
    
    async def explore_api_comprehensive(self) -> None:
        """Comprehensive API exploration"""
        logger.info("Starting comprehensive API exploration...")
        
        # Step 1: Basic discovery
        await self._explore_user_profile()
        await self._explore_device_data()
        await self._explore_user_data()
        
        # Step 2: Enhanced discovery
        await self._explore_additional_endpoints()
        await self._explore_historical_data()
        await self._explore_settings_and_preferences()
        await self._explore_analytics_and_metrics()
        await self._explore_notifications_and_alerts()
        await self._explore_device_management()
        await self._explore_user_management()
        
        # Step 3: Deep discovery
        await self._explore_nested_endpoints()
        await self._explore_alternative_api_versions()
        await self._explore_experimental_endpoints()
        
        # Step 4: Cross-reference discovery
        await self._cross_reference_discoveries()
    
    async def _explore_user_profile(self) -> None:
        """Explore user profile and device information"""
        logger.info("Exploring user profile...")
        
        url = f"{self.client_api_url}/users/me"
        data = await self.api_request("GET", url)
        
        if data:
            self._record_endpoint("GET", url, "User profile and device information", data)
            user_data = data.get("user", {})
            self._device_ids = user_data.get("devices", [])
            self._is_pod = "cooling" in user_data.get("features", [])
            self._has_base = "elevation" in user_data.get("features", [])
            
            logger.info(f"Discovered devices: {self._device_ids}")
            logger.info(f"Is Pod: {self._is_pod}")
            logger.info(f"Has Base: {self._has_base}")
            
            self._extract_entities_from_data("user_profile", data, "User Profile")
    
    async def _explore_device_data(self) -> None:
        """Explore device-specific data"""
        if not self._device_ids:
            logger.warning("No device IDs available")
            return
            
        device_id = self._device_ids[0]
        logger.info(f"Exploring device data for device {device_id}...")
        
        # Get device details
        url = f"{self.client_api_url}/devices/{device_id}"
        data = await self.api_request("GET", url)
        
        if data:
            self._record_endpoint("GET", url, "Device details and status", data)
            self._extract_entities_from_data("device_status", data.get("result", {}), "Device Status")
            
            # Get device with specific filters
            url_with_filter = f"{self.client_api_url}/devices/{device_id}?filter=leftUserId,rightUserId,awaySides"
            data_with_filter = await self.api_request("GET", url_with_filter)
            
            if data_with_filter:
                self._record_endpoint("GET", url_with_filter, "Device user assignments and away status", data_with_filter)
                self._extract_entities_from_data("device_users", data_with_filter.get("result", {}), "Device User Assignments")
    
    async def _explore_user_data(self) -> None:
        """Explore user-specific data for each user"""
        if not self._device_ids:
            return
            
        device_id = self._device_ids[0]
        
        # Get device user assignments
        url = f"{self.client_api_url}/devices/{device_id}?filter=leftUserId,rightUserId,awaySides"
        data = await self.api_request("GET", url)
        
        if not data:
            return
            
        result = data.get("result", {})
        user_ids = set([
            result.get("leftUserId"),
            result.get("rightUserId"),
            *result.get("awaySides", {}).values()
        ])
        
        # Explore data for each user
        for user_id in filter(None, user_ids):
            await self._explore_single_user_data(user_id)
    
    async def _explore_single_user_data(self, user_id: str) -> None:
        """Explore data for a single user"""
        logger.info(f"Exploring data for user {user_id}...")
        
        # Get user profile
        url = f"{self.client_api_url}/users/{user_id}"
        data = await self.api_request("GET", url)
        
        if data:
            self._record_endpoint("GET", url, f"User profile for user {user_id}", data)
            self._extract_entities_from_data(f"user_{user_id}_profile", data, f"User {user_id} Profile")
        
        # Get user trends (sleep data)
        await self._explore_user_trends(user_id)
        
        # Get user routines (alarms)
        await self._explore_user_routines(user_id)
        
        # Get temperature settings
        await self._explore_user_temperature(user_id)
        
        # Get base data if available
        if self._has_base:
            await self._explore_user_base(user_id)
    
    async def _explore_user_trends(self, user_id: str) -> None:
        """Explore user trends (sleep data)"""
        url = f"{self.client_api_url}/users/{user_id}/trends"
        
        # Get trends for the last 30 days to get more data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        params = {
            "tz": self.timezone,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "include-main": "false",
            "include-all-sessions": "true",
            "model-version": "v2",
        }
        
        data = await self.api_request("GET", url, params=params)
        
        if data:
            self._record_endpoint("GET", url, f"Sleep trends for user {user_id}", data, params)
            self._extract_entities_from_data(f"user_{user_id}_trends", data, f"User {user_id} Sleep Trends")
    
    async def _explore_user_routines(self, user_id: str) -> None:
        """Explore user routines (alarms)"""
        url = f"{self.app_api_url}/v2/users/{user_id}/routines"
        data = await self.api_request("GET", url)
        
        if data:
            self._record_endpoint("GET", url, f"Routines and alarms for user {user_id}", data)
            self._extract_entities_from_data(f"user_{user_id}_routines", data, f"User {user_id} Routines")
    
    async def _explore_user_temperature(self, user_id: str) -> None:
        """Explore user temperature settings"""
        url = f"{self.app_api_url}/v1/users/{user_id}/temperature"
        data = await self.api_request("GET", url)
        
        if data:
            self._record_endpoint("GET", url, f"Temperature settings for user {user_id}", data)
            self._extract_entities_from_data(f"user_{user_id}_temperature", data, f"User {user_id} Temperature")
    
    async def _explore_user_base(self, user_id: str) -> None:
        """Explore user base data (if available)"""
        url = f"{self.app_api_url}/v1/users/{user_id}/base"
        data = await self.api_request("GET", url)
        
        if data:
            self._record_endpoint("GET", url, f"Base settings for user {user_id}", data)
            self._extract_entities_from_data(f"user_{user_id}_base", data, f"User {user_id} Base")
    
    async def _explore_additional_endpoints(self) -> None:
        """Explore additional endpoints that might exist"""
        if not self._user_id:
            return
            
        logger.info("Exploring additional endpoints...")
        
        # Explore potential additional endpoints
        additional_endpoints = [
            f"{self.client_api_url}/users/{self._user_id}/sessions",
            f"{self.client_api_url}/users/{self._user_id}/metrics",
            f"{self.client_api_url}/users/{self._user_id}/stats",
            f"{self.client_api_url}/users/{self._user_id}/analytics",
            f"{self.client_api_url}/users/{self._user_id}/insights",
            f"{self.app_api_url}/v1/users/{self._user_id}/settings",
            f"{self.app_api_url}/v1/users/{self._user_id}/preferences",
            f"{self.app_api_url}/v1/users/{self._user_id}/notifications",
            f"{self.app_api_url}/v1/users/{self._user_id}/profile",
            f"{self.app_api_url}/v1/users/{self._user_id}/account",
        ]
        
        for url in additional_endpoints:
            data = await self.api_request("GET", url)
            if data:
                endpoint_name = url.split("/")[-1]
                self._record_endpoint("GET", url, f"Additional endpoint: {endpoint_name}", data)
                self._extract_entities_from_data(f"additional_{endpoint_name}", data, f"Additional {endpoint_name}")
    
    async def _explore_historical_data(self) -> None:
        """Explore historical data endpoints"""
        if not self._user_id:
            return
            
        logger.info("Exploring historical data endpoints...")
        
        # Explore historical data with different time ranges
        historical_endpoints = [
            f"{self.client_api_url}/users/{self._user_id}/history",
            f"{self.client_api_url}/users/{self._user_id}/sessions",
            f"{self.client_api_url}/users/{self._user_id}/sleep-data",
            f"{self.app_api_url}/v1/users/{self._user_id}/history",
            f"{self.app_api_url}/v1/users/{self._user_id}/sleep-history",
        ]
        
        for url in historical_endpoints:
            data = await self.api_request("GET", url)
            if data:
                endpoint_name = url.split("/")[-1]
                self._record_endpoint("GET", url, f"Historical data: {endpoint_name}", data)
                self._extract_entities_from_data(f"historical_{endpoint_name}", data, f"Historical {endpoint_name}")
    
    async def _explore_settings_and_preferences(self) -> None:
        """Explore settings and preferences endpoints"""
        if not self._user_id:
            return
            
        logger.info("Exploring settings and preferences...")
        
        settings_endpoints = [
            f"{self.app_api_url}/v1/users/{self._user_id}/settings",
            f"{self.app_api_url}/v1/users/{self._user_id}/preferences",
            f"{self.app_api_url}/v1/users/{self._user_id}/config",
            f"{self.app_api_url}/v1/users/{self._user_id}/options",
            f"{self.client_api_url}/users/{self._user_id}/settings",
            f"{self.client_api_url}/users/{self._user_id}/preferences",
        ]
        
        for url in settings_endpoints:
            data = await self.api_request("GET", url)
            if data:
                endpoint_name = url.split("/")[-1]
                self._record_endpoint("GET", url, f"Settings: {endpoint_name}", data)
                self._extract_entities_from_data(f"settings_{endpoint_name}", data, f"Settings {endpoint_name}")
    
    async def _explore_analytics_and_metrics(self) -> None:
        """Explore analytics and metrics endpoints"""
        if not self._user_id:
            return
            
        logger.info("Exploring analytics and metrics...")
        
        analytics_endpoints = [
            f"{self.client_api_url}/users/{self._user_id}/analytics",
            f"{self.client_api_url}/users/{self._user_id}/metrics",
            f"{self.client_api_url}/users/{self._user_id}/stats",
            f"{self.client_api_url}/users/{self._user_id}/insights",
            f"{self.app_api_url}/v1/users/{self._user_id}/analytics",
            f"{self.app_api_url}/v1/users/{self._user_id}/metrics",
        ]
        
        for url in analytics_endpoints:
            data = await self.api_request("GET", url)
            if data:
                endpoint_name = url.split("/")[-1]
                self._record_endpoint("GET", url, f"Analytics: {endpoint_name}", data)
                self._extract_entities_from_data(f"analytics_{endpoint_name}", data, f"Analytics {endpoint_name}")
    
    async def _explore_notifications_and_alerts(self) -> None:
        """Explore notifications and alerts endpoints"""
        if not self._user_id:
            return
            
        logger.info("Exploring notifications and alerts...")
        
        notification_endpoints = [
            f"{self.app_api_url}/v1/users/{self._user_id}/notifications",
            f"{self.app_api_url}/v1/users/{self._user_id}/alerts",
            f"{self.app_api_url}/v1/users/{self._user_id}/messages",
            f"{self.client_api_url}/users/{self._user_id}/notifications",
            f"{self.client_api_url}/users/{self._user_id}/alerts",
        ]
        
        for url in notification_endpoints:
            data = await self.api_request("GET", url)
            if data:
                endpoint_name = url.split("/")[-1]
                self._record_endpoint("GET", url, f"Notifications: {endpoint_name}", data)
                self._extract_entities_from_data(f"notifications_{endpoint_name}", data, f"Notifications {endpoint_name}")
    
    async def _explore_device_management(self) -> None:
        """Explore device management endpoints"""
        if not self._device_ids:
            return
            
        logger.info("Exploring device management...")
        
        device_id = self._device_ids[0]
        device_endpoints = [
            f"{self.client_api_url}/devices/{device_id}/status",
            f"{self.client_api_url}/devices/{device_id}/health",
            f"{self.client_api_url}/devices/{device_id}/info",
            f"{self.client_api_url}/devices/{device_id}/config",
            f"{self.app_api_url}/v1/devices/{device_id}/status",
            f"{self.app_api_url}/v1/devices/{device_id}/health",
        ]
        
        for url in device_endpoints:
            data = await self.api_request("GET", url)
            if data:
                endpoint_name = url.split("/")[-1]
                self._record_endpoint("GET", url, f"Device management: {endpoint_name}", data)
                self._extract_entities_from_data(f"device_management_{endpoint_name}", data, f"Device Management {endpoint_name}")
    
    async def _explore_user_management(self) -> None:
        """Explore user management endpoints"""
        if not self._user_id:
            return
            
        logger.info("Exploring user management...")
        
        user_management_endpoints = [
            f"{self.client_api_url}/users/{self._user_id}/profile",
            f"{self.client_api_url}/users/{self._user_id}/account",
            f"{self.client_api_url}/users/{self._user_id}/info",
            f"{self.app_api_url}/v1/users/{self._user_id}/profile",
            f"{self.app_api_url}/v1/users/{self._user_id}/account",
        ]
        
        for url in user_management_endpoints:
            data = await self.api_request("GET", url)
            if data:
                endpoint_name = url.split("/")[-1]
                self._record_endpoint("GET", url, f"User management: {endpoint_name}", data)
                self._extract_entities_from_data(f"user_management_{endpoint_name}", data, f"User Management {endpoint_name}")
    
    async def _explore_nested_endpoints(self) -> None:
        """Explore nested endpoints based on discovered data"""
        logger.info("Exploring nested endpoints...")
        
        # Look for additional endpoints in the data we've already discovered
        for endpoint in self.api_endpoints:
            if endpoint.response_schema:
                self._discover_nested_endpoints_from_data(endpoint.response_schema)
    
    def _discover_nested_endpoints_from_data(self, data: Any, base_url: str = "") -> None:
        """Discover nested endpoints from API response data"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and ("/users/" in value or "/devices/" in value):
                    # This might be a URL reference
                    self.discovered_urls.add(value)
                elif isinstance(value, dict):
                    self._discover_nested_endpoints_from_data(value, f"{base_url}/{key}")
                elif isinstance(value, list) and value:
                    self._discover_nested_endpoints_from_data(value[0], f"{base_url}/{key}")
    
    async def _explore_alternative_api_versions(self) -> None:
        """Explore alternative API versions"""
        logger.info("Exploring alternative API versions...")
        
        if not self._user_id:
            return
            
        # Try different API versions
        api_versions = ["v1", "v2", "v3", "beta", "alpha"]
        
        for version in api_versions:
            version_endpoints = [
                f"{self.client_api_url.replace('/v1', f'/{version}')}/users/{self._user_id}",
                f"{self.app_api_url.replace('/v1', f'/{version}')}/users/{self._user_id}",
            ]
            
            for url in version_endpoints:
                data = await self.api_request("GET", url)
                if data:
                    self._record_endpoint("GET", url, f"Alternative API version: {version}", data)
                    self._extract_entities_from_data(f"alt_version_{version}", data, f"Alternative Version {version}")
    
    async def _explore_experimental_endpoints(self) -> None:
        """Explore experimental endpoints"""
        logger.info("Exploring experimental endpoints...")
        
        if not self._user_id:
            return
            
        experimental_endpoints = [
            f"{self.client_api_url}/users/{self._user_id}/experimental",
            f"{self.app_api_url}/v1/users/{self._user_id}/experimental",
            f"{self.client_api_url}/users/{self._user_id}/beta",
            f"{self.app_api_url}/v1/users/{self._user_id}/beta",
        ]
        
        for url in experimental_endpoints:
            data = await self.api_request("GET", url)
            if data:
                endpoint_name = url.split("/")[-1]
                self._record_endpoint("GET", url, f"Experimental: {endpoint_name}", data)
                self._extract_entities_from_data(f"experimental_{endpoint_name}", data, f"Experimental {endpoint_name}")
    
    async def _cross_reference_discoveries(self) -> None:
        """Cross-reference discoveries to find additional endpoints"""
        logger.info("Cross-referencing discoveries...")
        
        # Try to discover additional endpoints based on patterns
        if self._user_id and self._device_ids:
            device_id = self._device_ids[0]
            
            # Try different combinations
            cross_reference_endpoints = [
                f"{self.client_api_url}/users/{self._user_id}/devices/{device_id}",
                f"{self.app_api_url}/v1/users/{self._user_id}/devices/{device_id}",
                f"{self.client_api_url}/devices/{device_id}/users/{self._user_id}",
                f"{self.app_api_url}/v1/devices/{device_id}/users/{self._user_id}",
            ]
            
            for url in cross_reference_endpoints:
                data = await self.api_request("GET", url)
                if data:
                    endpoint_name = url.split("/")[-2] + "_" + url.split("/")[-1]
                    self._record_endpoint("GET", url, f"Cross-reference: {endpoint_name}", data)
                    self._extract_entities_from_data(f"cross_ref_{endpoint_name}", data, f"Cross-reference {endpoint_name}")
    
    def _record_endpoint(self, method: str, url: str, description: str, data: Dict, params: Optional[Dict] = None) -> None:
        """Record an API endpoint with its metadata"""
        self.explored_urls.add(url)
        
        endpoint = APIEndpoint(
            method=method,
            url=url,
            description=description,
            parameters=params,
            response_schema=data,
            response_size=len(json.dumps(data)) if data else 0
        )
        
        self.api_endpoints.append(endpoint)
    
    def _extract_entities_from_data(self, source: str, data: Any, description: str, path: str = "") -> None:
        """Recursively extract entities from API response data"""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                self._extract_entities_from_data(source, value, description, current_path)
                
                # Create entity for this key-value pair
                entity = self._create_entity_from_value(source, key, value, description, current_path)
                if entity:
                    self.discovered_entities.append(entity)
                    
        elif isinstance(data, list) and data:
            # For lists, analyze the first item to understand the structure
            self._extract_entities_from_data(source, data[0], description, f"{path}[0]")
            
            # Also create an entity for the array itself
            entity = self._create_entity_from_value(source, path.split(".")[-1] if "." in path else "array", data, description, path)
            if entity:
                entity.is_array = True
                entity.array_length = len(data)
                self.discovered_entities.append(entity)
    
    def _create_entity_from_value(self, source: str, key: str, value: Any, description: str, path: str) -> Optional[DiscoveredEntity]:
        """Create a DiscoveredEntity from a key-value pair"""
        if value is None:
            return None
            
        # Determine data type
        if isinstance(value, bool):
            data_type = "boolean"
        elif isinstance(value, int):
            data_type = "integer"
        elif isinstance(value, float):
            data_type = "float"
        elif isinstance(value, str):
            data_type = "string"
        elif isinstance(value, dict):
            data_type = "object"
        elif isinstance(value, list):
            data_type = "array"
        else:
            data_type = "unknown"
        
        # Determine entity type based on key name and value
        entity_type = self._determine_entity_type(key, value)
        
        # Determine unit if applicable
        unit = self._determine_unit(key, value)
        
        # Determine min/max values if applicable
        min_value, max_value = self._determine_value_range(key, value)
        
        return DiscoveredEntity(
            name=key,
            type=entity_type,
            source_endpoint=source,
            description=f"{description} - {path}",
            data_type=data_type,
            example_value=value,
            unit=unit,
            min_value=min_value,
            max_value=max_value,
            path=path
        )
    
    def _determine_entity_type(self, key: str, value: Any) -> str:
        """Determine the entity type based on key name and value"""
        key_lower = key.lower()
        
        # Temperature related
        if any(temp_word in key_lower for temp_word in ["temp", "temperature", "heating", "cooling"]):
            return "temperature"
        
        # Time related
        if any(time_word in key_lower for time_word in ["time", "duration", "start", "end", "date", "timestamp"]):
            return "time"
        
        # Sleep related
        if any(sleep_word in key_lower for sleep_word in ["sleep", "bed", "presence", "stage", "session"]):
            return "sleep"
        
        # Health related
        if any(health_word in key_lower for health_word in ["heart", "respiratory", "hrv", "breath", "pulse", "bpm"]):
            return "health"
        
        # Device related
        if any(device_word in key_lower for device_word in ["device", "priming", "water", "level", "status", "health"]):
            return "device"
        
        # Alarm related
        if any(alarm_word in key_lower for alarm_word in ["alarm", "routine", "snooze", "wake"]):
            return "alarm"
        
        # Base related
        if any(base_word in key_lower for base_word in ["base", "angle", "preset", "leg", "torso", "elevation"]):
            return "base"
        
        # Score related
        if any(score_word in key_lower for score_word in ["score", "quality", "fitness", "rating"]):
            return "score"
        
        # Status related
        if any(status_word in key_lower for status_word in ["status", "state", "enabled", "active", "online"]):
            return "status"
        
        # Analytics related
        if any(analytics_word in key_lower for analytics_word in ["analytics", "metrics", "stats", "insights", "trends"]):
            return "analytics"
        
        # Notification related
        if any(notification_word in key_lower for notification_word in ["notification", "alert", "message", "reminder"]):
            return "notification"
        
        # Settings related
        if any(settings_word in key_lower for settings_word in ["settings", "preferences", "config", "options"]):
            return "settings"
        
        return "general"
    
    def _determine_unit(self, key: str, value: Any) -> Optional[str]:
        """Determine the unit for a value based on key name"""
        key_lower = key.lower()
        
        # Temperature units
        if any(temp_word in key_lower for temp_word in ["temp", "temperature"]):
            if "f" in key_lower or "fahrenheit" in key_lower:
                return "°F"
            else:
                return "°C"
        
        # Time units
        if "duration" in key_lower:
            return "seconds"
        if "time" in key_lower:
            return "timestamp"
        
        # Percentage
        if "level" in key_lower and isinstance(value, (int, float)):
            return "%"
        
        # Angle
        if "angle" in key_lower:
            return "degrees"
        
        # Heart rate
        if any(hr_word in key_lower for hr_word in ["heart", "bpm", "pulse"]):
            return "bpm"
        
        # Respiratory rate
        if any(resp_word in key_lower for resp_word in ["respiratory", "breath"]):
            return "breaths/min"
        
        return None
    
    def _determine_value_range(self, key: str, value: Any) -> tuple[Optional[float], Optional[float]]:
        """Determine min/max values for a given key"""
        if not isinstance(value, (int, float)):
            return None, None
            
        key_lower = key.lower()
        
        # Temperature ranges
        if any(temp_word in key_lower for temp_word in ["temp", "temperature"]):
            if "f" in key_lower or "fahrenheit" in key_lower:
                return 55.0, 110.0  # Fahrenheit range
            else:
                return 13.0, 44.0   # Celsius range
        
        # Heating level range
        if "level" in key_lower and "heating" in key_lower:
            return -100.0, 100.0
        
        # Angle range
        if "angle" in key_lower:
            return 0.0, 90.0
        
        # Score ranges
        if "score" in key_lower:
            return 0.0, 100.0
        
        # Heart rate range
        if any(hr_word in key_lower for hr_word in ["heart", "bpm", "pulse"]):
            return 40.0, 200.0
        
        # Respiratory rate range
        if any(resp_word in key_lower for resp_word in ["respiratory", "breath"]):
            return 8.0, 30.0
        
        return None, None
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report of discovered entities"""
        # Group entities by type
        entities_by_type = {}
        for entity in self.discovered_entities:
            if entity.type not in entities_by_type:
                entities_by_type[entity.type] = []
            entities_by_type[entity.type].append(asdict(entity))
        
        # Group entities by source
        entities_by_source = {}
        for entity in self.discovered_entities:
            if entity.source_endpoint not in entities_by_source:
                entities_by_source[entity.source_endpoint] = []
            entities_by_source[entity.source_endpoint].append(asdict(entity))
        
        report = {
            "exploration_summary": {
                "total_entities_discovered": len(self.discovered_entities),
                "total_endpoints_explored": len(self.api_endpoints),
                "unique_urls_explored": len(self.explored_urls),
                "device_type": "Pod 4" if self._is_pod else "Unknown",
                "has_base": self._has_base,
                "device_ids": self._device_ids,
                "user_id": self._user_id,
            },
            "entities_by_type": entities_by_type,
            "entities_by_source": entities_by_source,
            "api_endpoints": [asdict(endpoint) for endpoint in self.api_endpoints],
            "recommended_home_assistant_entities": self._generate_ha_entity_recommendations(),
        }
        
        return report
    
    def _generate_ha_entity_recommendations(self) -> Dict[str, Any]:
        """Generate Home Assistant entity recommendations"""
        recommendations = {
            "sensors": [],
            "binary_sensors": [],
            "switches": [],
            "numbers": [],
            "selects": [],
            "climates": [],
        }
        
        for entity in self.discovered_entities:
            ha_entity = self._convert_to_ha_entity(entity)
            if ha_entity:
                category = ha_entity["category"]
                recommendations[category].append(ha_entity)
        
        return recommendations
    
    def _convert_to_ha_entity(self, entity: DiscoveredEntity) -> Optional[Dict[str, Any]]:
        """Convert a discovered entity to a Home Assistant entity recommendation"""
        if entity.data_type in ["object", "array", "unknown"]:
            return None
            
        ha_entity = {
            "name": entity.name,
            "type": entity.type,
            "description": entity.description,
            "data_type": entity.data_type,
            "unit": entity.unit,
            "min_value": entity.min_value,
            "max_value": entity.max_value,
            "source_endpoint": entity.source_endpoint,
            "path": entity.path,
            "is_array": entity.is_array,
            "array_length": entity.array_length,
        }
        
        # Determine Home Assistant entity category
        if entity.data_type == "boolean":
            ha_entity["category"] = "binary_sensors"
        elif entity.type == "temperature":
            ha_entity["category"] = "sensors"
        elif entity.type == "device" and "level" in entity.name.lower():
            ha_entity["category"] = "numbers"
        elif entity.type == "status":
            ha_entity["category"] = "sensors"
        elif entity.type == "time":
            ha_entity["category"] = "sensors"
        elif entity.type == "score":
            ha_entity["category"] = "sensors"
        elif entity.type == "health":
            ha_entity["category"] = "sensors"
        elif entity.type == "sleep":
            ha_entity["category"] = "sensors"
        elif entity.type == "analytics":
            ha_entity["category"] = "sensors"
        elif entity.type == "notification":
            ha_entity["category"] = "binary_sensors"
        elif entity.type == "settings":
            ha_entity["category"] = "sensors"
        else:
            ha_entity["category"] = "sensors"
        
        return ha_entity
    
    async def save_report(self, filename: str = "enhanced_eight_sleep_api_report.json") -> None:
        """Save the exploration report to a file"""
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Enhanced report saved to {filename}")
        
        # Also save a summary
        summary_filename = filename.replace('.json', '_summary.txt')
        with open(summary_filename, 'w') as f:
            f.write("Enhanced Eight Sleep API Exploration Summary\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Total Entities Discovered: {len(self.discovered_entities)}\n")
            f.write(f"Total Endpoints Explored: {len(self.api_endpoints)}\n")
            f.write(f"Unique URLs Explored: {len(self.explored_urls)}\n")
            f.write(f"Device Type: {'Pod 4' if self._is_pod else 'Unknown'}\n")
            f.write(f"Has Base: {self._has_base}\n\n")
            
            f.write("Entities by Type:\n")
            for entity_type, entities in report["entities_by_type"].items():
                f.write(f"  {entity_type}: {len(entities)} entities\n")
            
            f.write("\nRecommended Home Assistant Entities:\n")
            for category, entities in report["recommended_home_assistant_entities"].items():
                if entities:
                    f.write(f"  {category}: {len(entities)} entities\n")
            
            f.write("\nExplored Endpoints:\n")
            for endpoint in self.api_endpoints:
                f.write(f"  {endpoint.method} {endpoint.url}\n")

async def main():
    """Main function to run the enhanced API exploration"""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python enhanced_api_explorer.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    explorer = EnhancedEightSleepAPIExplorer(email, password)
    
    # Authenticate
    if not await explorer.authenticate():
        print("Authentication failed. Please check your credentials.")
        sys.exit(1)
    
    # Explore all endpoints
    await explorer.explore_api_comprehensive()
    
    # Generate and save report
    await explorer.save_report()
    
    # Print summary
    report = explorer.generate_report()
    print(f"\nEnhanced exploration complete!")
    print(f"Total entities discovered: {len(explorer.discovered_entities)}")
    print(f"Total endpoints explored: {len(explorer.api_endpoints)}")
    print(f"Unique URLs explored: {len(explorer.explored_urls)}")
    print(f"Device type: {'Pod 4' if explorer._is_pod else 'Unknown'}")
    print(f"Has base: {explorer._has_base}")
    
    print("\nEntities by type:")
    for entity_type, entities in report["entities_by_type"].items():
        print(f"  {entity_type}: {len(entities)} entities")
    
    print("\nRecommended Home Assistant entities:")
    for category, entities in report["recommended_home_assistant_entities"].items():
        if entities:
            print(f"  {category}: {len(entities)} entities")

if __name__ == "__main__":
    asyncio.run(main()) 