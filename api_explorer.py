#!/usr/bin/env python3
"""
Eight Sleep API Explorer
Safely reverse engineers the Eight Sleep API to discover all available entities
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import httpx
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIEndpoint:
    """Represents an API endpoint with its metadata"""
    method: str
    url: str
    description: str
    parameters: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    discovered_entities: Optional[List[str]] = None

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

class EightSleepAPIExplorer:
    """Safely explores the Eight Sleep API to discover all available entities"""
    
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
                "user-agent": "EightSleepAPIExplorer/1.0",
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
            "user-agent": "EightSleepAPIExplorer/1.0",
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
    
    async def discover_user_info(self) -> None:
        """Discover user information and device details"""
        logger.info("Discovering user information...")
        
        # Get user profile
        url = f"{self.client_api_url}/users/me"
        data = await self.api_request("GET", url)
        
        if data:
            self.api_endpoints.append(APIEndpoint(
                method="GET",
                url=url,
                description="Get current user profile and device information",
                response_schema=data
            ))
            
            user_data = data.get("user", {})
            self._device_ids = user_data.get("devices", [])
            self._is_pod = "cooling" in user_data.get("features", [])
            self._has_base = "elevation" in user_data.get("features", [])
            
            logger.info(f"Discovered devices: {self._device_ids}")
            logger.info(f"Is Pod: {self._is_pod}")
            logger.info(f"Has Base: {self._has_base}")
            
            # Extract entities from user data
            self._extract_entities_from_data("user_profile", data, "User Profile")
    
    async def discover_device_data(self) -> None:
        """Discover device-specific data"""
        if not self._device_ids:
            logger.warning("No device IDs available")
            return
            
        device_id = self._device_ids[0]
        logger.info(f"Discovering device data for device {device_id}...")
        
        # Get device details
        url = f"{self.client_api_url}/devices/{device_id}"
        data = await self.api_request("GET", url)
        
        if data:
            self.api_endpoints.append(APIEndpoint(
                method="GET",
                url=url,
                description="Get device details and status",
                response_schema=data
            ))
            
            # Extract entities from device data
            self._extract_entities_from_data("device_status", data.get("result", {}), "Device Status")
            
            # Get device with specific filters
            url_with_filter = f"{self.client_api_url}/devices/{device_id}?filter=leftUserId,rightUserId,awaySides"
            data_with_filter = await self.api_request("GET", url_with_filter)
            
            if data_with_filter:
                self.api_endpoints.append(APIEndpoint(
                    method="GET",
                    url=url_with_filter,
                    description="Get device user assignments and away status",
                    response_schema=data_with_filter
                ))
    
    async def discover_user_data(self) -> None:
        """Discover user-specific data for each user"""
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
        
        # Discover data for each user
        for user_id in filter(None, user_ids):
            await self._discover_single_user_data(user_id)
    
    async def _discover_single_user_data(self, user_id: str) -> None:
        """Discover data for a single user"""
        logger.info(f"Discovering data for user {user_id}...")
        
        # Get user profile
        url = f"{self.client_api_url}/users/{user_id}"
        data = await self.api_request("GET", url)
        
        if data:
            self.api_endpoints.append(APIEndpoint(
                method="GET",
                url=url,
                description=f"Get user profile for user {user_id}",
                response_schema=data
            ))
            
            # Extract entities from user profile
            self._extract_entities_from_data(f"user_{user_id}_profile", data, f"User {user_id} Profile")
        
        # Get user trends (sleep data)
        await self._discover_user_trends(user_id)
        
        # Get user routines (alarms)
        await self._discover_user_routines(user_id)
        
        # Get temperature settings
        await self._discover_user_temperature(user_id)
        
        # Get base data if available
        if self._has_base:
            await self._discover_user_base(user_id)
    
    async def _discover_user_trends(self, user_id: str) -> None:
        """Discover user trends (sleep data)"""
        url = f"{self.client_api_url}/users/{user_id}/trends"
        
        # Get trends for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
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
            self.api_endpoints.append(APIEndpoint(
                method="GET",
                url=url,
                description=f"Get sleep trends for user {user_id}",
                parameters=params,
                response_schema=data
            ))
            
            # Extract entities from trends data
            self._extract_entities_from_data(f"user_{user_id}_trends", data, f"User {user_id} Sleep Trends")
    
    async def _discover_user_routines(self, user_id: str) -> None:
        """Discover user routines (alarms)"""
        url = f"{self.app_api_url}/v2/users/{user_id}/routines"
        data = await self.api_request("GET", url)
        
        if data:
            self.api_endpoints.append(APIEndpoint(
                method="GET",
                url=url,
                description=f"Get routines and alarms for user {user_id}",
                response_schema=data
            ))
            
            # Extract entities from routines data
            self._extract_entities_from_data(f"user_{user_id}_routines", data, f"User {user_id} Routines")
    
    async def _discover_user_temperature(self, user_id: str) -> None:
        """Discover user temperature settings"""
        url = f"{self.app_api_url}/v1/users/{user_id}/temperature"
        data = await self.api_request("GET", url)
        
        if data:
            self.api_endpoints.append(APIEndpoint(
                method="GET",
                url=url,
                description=f"Get temperature settings for user {user_id}",
                response_schema=data
            ))
            
            # Extract entities from temperature data
            self._extract_entities_from_data(f"user_{user_id}_temperature", data, f"User {user_id} Temperature")
    
    async def _discover_user_base(self, user_id: str) -> None:
        """Discover user base data (if available)"""
        url = f"{self.app_api_url}/v1/users/{user_id}/base"
        data = await self.api_request("GET", url)
        
        if data:
            self.api_endpoints.append(APIEndpoint(
                method="GET",
                url=url,
                description=f"Get base settings for user {user_id}",
                response_schema=data
            ))
            
            # Extract entities from base data
            self._extract_entities_from_data(f"user_{user_id}_base", data, f"User {user_id} Base")
    
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
            max_value=max_value
        )
    
    def _determine_entity_type(self, key: str, value: Any) -> str:
        """Determine the entity type based on key name and value"""
        key_lower = key.lower()
        
        # Temperature related
        if any(temp_word in key_lower for temp_word in ["temp", "temperature", "heating", "cooling"]):
            return "temperature"
        
        # Time related
        if any(time_word in key_lower for time_word in ["time", "duration", "start", "end", "date"]):
            return "time"
        
        # Sleep related
        if any(sleep_word in key_lower for sleep_word in ["sleep", "bed", "presence", "stage"]):
            return "sleep"
        
        # Health related
        if any(health_word in key_lower for health_word in ["heart", "respiratory", "hrv", "breath"]):
            return "health"
        
        # Device related
        if any(device_word in key_lower for device_word in ["device", "priming", "water", "level"]):
            return "device"
        
        # Alarm related
        if any(alarm_word in key_lower for alarm_word in ["alarm", "routine", "snooze"]):
            return "alarm"
        
        # Base related
        if any(base_word in key_lower for base_word in ["base", "angle", "preset", "leg", "torso"]):
            return "base"
        
        # Score related
        if any(score_word in key_lower for score_word in ["score", "quality", "fitness"]):
            return "score"
        
        # Status related
        if any(status_word in key_lower for status_word in ["status", "state", "enabled", "active"]):
            return "status"
        
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
        
        return None, None
    
    async def explore_all_endpoints(self) -> None:
        """Explore all known API endpoints"""
        logger.info("Starting comprehensive API exploration...")
        
        # Discover basic information
        await self.discover_user_info()
        await self.discover_device_data()
        await self.discover_user_data()
        
        # Additional endpoint exploration
        await self._explore_additional_endpoints()
    
    async def _explore_additional_endpoints(self) -> None:
        """Explore additional endpoints that might exist"""
        if not self._user_id:
            return
            
        # Explore potential additional endpoints
        additional_endpoints = [
            f"{self.client_api_url}/users/{self._user_id}/sessions",
            f"{self.client_api_url}/users/{self._user_id}/metrics",
            f"{self.client_api_url}/users/{self._user_id}/stats",
            f"{self.app_api_url}/v1/users/{self._user_id}/settings",
            f"{self.app_api_url}/v1/users/{self._user_id}/preferences",
            f"{self.app_api_url}/v1/users/{self._user_id}/notifications",
        ]
        
        for url in additional_endpoints:
            data = await self.api_request("GET", url)
            if data:
                self.api_endpoints.append(APIEndpoint(
                    method="GET",
                    url=url,
                    description=f"Additional endpoint discovered: {url}",
                    response_schema=data
                ))
                
                # Extract entities
                endpoint_name = url.split("/")[-1]
                self._extract_entities_from_data(f"additional_{endpoint_name}", data, f"Additional {endpoint_name}")
    
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
        else:
            ha_entity["category"] = "sensors"
        
        return ha_entity
    
    async def save_report(self, filename: str = "eight_sleep_api_report.json") -> None:
        """Save the exploration report to a file"""
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Report saved to {filename}")
        
        # Also save a summary
        summary_filename = filename.replace('.json', '_summary.txt')
        with open(summary_filename, 'w') as f:
            f.write("Eight Sleep API Exploration Summary\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total Entities Discovered: {len(self.discovered_entities)}\n")
            f.write(f"Total Endpoints Explored: {len(self.api_endpoints)}\n")
            f.write(f"Device Type: {'Pod 4' if self._is_pod else 'Unknown'}\n")
            f.write(f"Has Base: {self._has_base}\n\n")
            
            f.write("Entities by Type:\n")
            for entity_type, entities in report["entities_by_type"].items():
                f.write(f"  {entity_type}: {len(entities)} entities\n")
            
            f.write("\nRecommended Home Assistant Entities:\n")
            for category, entities in report["recommended_home_assistant_entities"].items():
                f.write(f"  {category}: {len(entities)} entities\n")

async def main():
    """Main function to run the API exploration"""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python api_explorer.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    explorer = EightSleepAPIExplorer(email, password)
    
    # Authenticate
    if not await explorer.authenticate():
        print("Authentication failed. Please check your credentials.")
        sys.exit(1)
    
    # Explore all endpoints
    await explorer.explore_all_endpoints()
    
    # Generate and save report
    await explorer.save_report()
    
    # Print summary
    report = explorer.generate_report()
    print(f"\nExploration complete!")
    print(f"Total entities discovered: {len(explorer.discovered_entities)}")
    print(f"Total endpoints explored: {len(explorer.api_endpoints)}")
    print(f"Device type: {'Pod 4' if explorer._is_pod else 'Unknown'}")
    print(f"Has base: {explorer._has_base}")
    
    print("\nEntities by type:")
    for entity_type, entities in report["entities_by_type"].items():
        print(f"  {entity_type}: {len(entities)} entities")
    
    print("\nRecommended Home Assistant entities:")
    for category, entities in report["recommended_home_assistant_entities"].items():
        print(f"  {category}: {len(entities)} entities")

if __name__ == "__main__":
    asyncio.run(main()) 