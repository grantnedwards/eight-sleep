# Eight Sleep API Exploration

This directory contains tools to safely reverse engineer the Eight Sleep API and discover all available entities for your Pod 4.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements_explorer.txt
   ```

2. **Run the exploration:**
   ```bash
   python run_api_exploration.py
   ```
   
   Or with credentials as arguments:
   ```bash
   python run_api_exploration.py your_email@example.com your_password
   ```

## 📋 What This Does

The API exploration script will:

1. **Authenticate** with your Eight Sleep account
2. **Discover** your device information (Pod 4, base, etc.)
3. **Explore** all available API endpoints
4. **Extract** all possible entities and data points
5. **Generate** a comprehensive report with:
   - All discovered entities organized by type
   - Home Assistant entity recommendations
   - Detailed API endpoint information
   - Data types, units, and value ranges

## 🔍 What Will Be Discovered

The script will explore and discover entities in these categories:

### Device Status
- Device online/offline status
- Water level and priming status
- Device health metrics
- Connection status

### Temperature Control
- Current heating/cooling levels
- Target temperatures
- Temperature presets
- Heating/cooling duration

### Sleep Data
- Sleep stages (light, deep, REM, awake)
- Sleep scores and quality metrics
- Sleep duration and efficiency
- Bed presence detection

### Health Metrics
- Heart rate (current and average)
- Respiratory rate
- Heart rate variability (HRV)
- Toss and turn count

### Environmental Data
- Room temperature
- Bed temperature
- Environmental conditions

### Base Control (if available)
- Leg angle
- Torso angle
- Base presets
- Snore mitigation status

### Alarm Management
- Alarm settings and schedules
- Snooze functionality
- Alarm states and status

### User Profiles
- User preferences
- Side assignments
- Away mode status

## 📊 Output Files

After running the exploration, you'll get:

1. **`eight_sleep_api_report.json`** - Complete detailed report
2. **`eight_sleep_api_report_summary.txt`** - Human-readable summary

## 🔒 Security & Safety

- **Read-only operations**: The script only performs GET requests
- **No data modification**: No settings or configurations are changed
- **Secure authentication**: Uses official Eight Sleep API endpoints
- **Local processing**: All data is processed locally, not sent elsewhere
- **Error handling**: Graceful handling of API errors and timeouts

## 🛠️ Technical Details

### API Endpoints Explored

The script explores these Eight Sleep API endpoints:

- `GET /users/me` - User profile and device information
- `GET /devices/{device_id}` - Device status and details
- `GET /users/{user_id}` - Individual user profiles
- `GET /users/{user_id}/trends` - Sleep data and trends
- `GET /users/{user_id}/routines` - Alarm and routine settings
- `GET /users/{user_id}/temperature` - Temperature settings
- `GET /users/{user_id}/base` - Base control settings (if available)

### Entity Discovery Process

1. **Authentication**: Secure login to Eight Sleep API
2. **Device Discovery**: Identify your Pod 4 and its capabilities
3. **User Discovery**: Find all users associated with your device
4. **Data Extraction**: Recursively extract all data points from API responses
5. **Entity Classification**: Categorize entities by type and purpose
6. **Home Assistant Mapping**: Map discovered entities to HA entity types

### Entity Types Discovered

- **temperature**: Temperature-related data (bed temp, room temp, etc.)
- **time**: Time-related data (durations, timestamps, etc.)
- **sleep**: Sleep-related data (stages, scores, etc.)
- **health**: Health metrics (heart rate, respiratory rate, etc.)
- **device**: Device status and health data
- **alarm**: Alarm and routine data
- **base**: Base control data (if available)
- **score**: Scoring and quality metrics
- **status**: Status and state information
- **general**: Other miscellaneous data

## 📈 Expected Results

For a typical Pod 4 setup, you can expect to discover:

- **50-100+ entities** across all categories
- **20-30 temperature-related** entities
- **15-25 sleep-related** entities  
- **10-20 health-related** entities
- **10-15 device status** entities
- **5-10 alarm/routine** entities
- **5-10 base control** entities (if base is present)

## 🎯 Home Assistant Integration

The discovered entities will be mapped to appropriate Home Assistant entity types:

- **sensors**: Temperature, health metrics, sleep data, scores
- **binary_sensors**: Device status, presence detection, alarm states
- **numbers**: Temperature levels, angles, durations
- **selects**: Presets, modes, states
- **climates**: Temperature control (if applicable)

## 🔧 Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify your email and password
   - Check if your account has API access
   - Try logging into the Eight Sleep app first

2. **No Devices Found**
   - Ensure your Pod 4 is properly connected
   - Check the Eight Sleep app for device status
   - Verify your account has access to the device

3. **API Errors**
   - The script includes retry logic and error handling
   - Check the console output for specific error messages
   - Some endpoints may not be available for all devices

### Debug Mode

To see more detailed information, modify the logging level in `safe_api_explorer.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Example Output

```
Eight Sleep API Explorer
==============================
This script will safely explore the Eight Sleep API
to discover all available entities for your Pod 4.

Starting Eight Sleep API exploration...
Email: your_email@example.com
==================================================
Authenticating with Eight Sleep API...
✅ Authentication successful!

Exploring API endpoints...
Generating report...

==================================================
EXPLORATION COMPLETE!
==================================================
Total entities discovered: 87
Device type: Pod 4
Has base: True
Device IDs: ['device_12345']

Entities by type:
  temperature: 23 entities
  sleep: 18 entities
  health: 15 entities
  device: 12 entities
  status: 8 entities
  alarm: 6 entities
  base: 5 entities

Recommended Home Assistant entities:
  sensors: 45 entities
  binary_sensors: 12 entities
  numbers: 8 entities
  selects: 5 entities

📄 Detailed report saved to: eight_sleep_api_report.json
📄 Summary saved to: eight_sleep_api_report_summary.txt

✅ API exploration completed successfully!
```

## 🚀 Next Steps

After running the exploration:

1. **Review the reports** to understand all available data
2. **Identify priority entities** for your Home Assistant integration
3. **Plan entity implementation** based on the discovered data
4. **Implement new sensors** using the discovered entity information

The detailed JSON report will contain all the information needed to implement new Home Assistant entities for your Eight Sleep Pod 4. 