# Eight Sleep Integration for Home Assistant

A comprehensive Home Assistant integration for Eight Sleep smart mattresses and mattress covers, featuring a beautiful custom Lovelace card, device actions, enhanced error handling, and real-time sleep stage tracking.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintainer](https://img.shields.io/badge/maintainer-%40grantnedwards-blue.svg)](https://github.com/grantnedwards)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

## 📋 Description

This integration provides comprehensive control and monitoring for Eight Sleep smart mattresses and mattress covers. It includes real-time temperature control, sleep stage tracking, biometric monitoring, and a beautiful custom Lovelace card for easy bed management.

**Key Features:**
- 🎛️ Real-time temperature control with custom Lovelace card
- 📊 Comprehensive sleep stage and biometric monitoring  
- 🔧 Device actions for automation integration
- 🛡️ Enhanced error handling with offline support
- 📱 Responsive design for mobile and desktop

## ✨ Features

### 🎛️ Custom Lovelace Card
- **Real-time Temperature Control**: Adjust bed temperature with intuitive sliders
- **Visual Bed Presence Indicators**: See when someone is on each side of the bed
- **Sleep Metrics Display**: View heart rate, HRV, breath rate, and sleep quality
- **Responsive Design**: Works perfectly on mobile and desktop devices
- **Theme Support**: Automatically adapts to light/dark themes
- **Side-by-Side Controls**: Independent control for left and right sides

### 🔧 Device Actions
- **Temperature Control**: Set temperature, increment/decrement, and preset modes
- **Side Control**: Turn individual sides on/off
- **Away Mode**: Start/stop away mode with one-touch actions
- **Pod Management**: Prime pod and configure bed sides
- **Modern Integration**: Uses Home Assistant's device action framework

### 🛡️ Enhanced Error Handling
- **Exponential Backoff**: Intelligent retry logic with exponential delays
- **Connection Recovery**: Automatic token refresh and connection recovery
- **Graceful Degradation**: Continues working when API is temporarily unavailable
- **Detailed Logging**: Comprehensive error reporting and debugging information

### 📊 Enhanced Sensors
- **Real-time Sleep Stage Tracking**: Monitor sleep stages with detailed attributes
- **Sleep Stage Breakdown**: Detailed breakdown of sleep stage percentages
- **Biometric Monitoring**: Heart rate, HRV, and respiratory rate tracking
- **Environmental Sensors**: Room temperature and bed temperature monitoring
- **Device Health**: Water level, priming status, and device health monitoring

## 🚀 Installation

### Via HACS (Recommended)

1. Add this repository to HACS
2. Install the integration
3. Add your Eight Sleep credentials in Home Assistant
4. Add the custom card to your Lovelace dashboard

### Manual Installation

1. Copy the `custom_components/eight_sleep` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add your Eight Sleep credentials in the integrations page

## 📋 Configuration

### Basic Integration Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Eight Sleep**
4. Enter your Eight Sleep credentials
5. The integration will automatically discover your devices

### Custom Card Configuration

Add this to your Lovelace dashboard:

```yaml
type: custom:eight-sleep-bed-card
title: "Eight Sleep Bed"
left_side: "left"
right_side: "right"
```

### Advanced Card Configuration

```yaml
type: custom:eight-sleep-bed-card
title: "Master Bedroom"
left_side: "left"
right_side: "right"
show_metrics: true
show_presence: true
temperature_range:
  min: 16
  max: 32
  step: 0.5
```

## 🎯 Device Actions

The integration provides device actions that can be used in automations:

### Temperature Actions
- **Set Temperature**: Set specific temperature for bed sides
- **Increment Temperature**: Adjust temperature by increment
- **Set Preset**: Apply Cool/Warm/Neutral presets

### Control Actions
- **Turn On Side**: Activate heating/cooling for specific side
- **Turn Off Side**: Deactivate heating/cooling for specific side
- **Start Away Mode**: Enable away mode
- **Stop Away Mode**: Disable away mode

### Device Actions
- **Prime Pod**: Prime the Eight Sleep pod
- **Set Bed Side**: Configure bed side settings

## 📊 Sensors

### Sleep Stage Sensors
- **Sleep Stage**: Real-time sleep stage tracking with duration and history
- **Sleep Stage Breakdown**: Detailed breakdown of sleep stage percentages
- **Sleep Efficiency**: Calculated sleep efficiency percentage

### Biometric Sensors
- **Heart Rate**: Real-time heart rate monitoring
- **HRV**: Heart rate variability tracking
- **Breath Rate**: Respiratory rate monitoring
- **Sleep Quality**: Sleep quality score

### Environmental Sensors
- **Room Temperature**: Current room temperature
- **Bed Temperature**: Current bed temperature
- **Target Temperature**: Target heating temperature

### Device Sensors
- **Water Level**: Pod water level status
- **Priming Status**: Pod priming status
- **Device Health**: Overall device health status

## 🔧 Services

The integration provides several services for advanced control:

### Temperature Services
- `eight_sleep.heat_set`: Set heating level with duration
- `eight_sleep.heat_increment`: Increment heating level

### Control Services
- `eight_sleep.side_on`: Turn on bed side
- `eight_sleep.side_off`: Turn off bed side
- `eight_sleep.away_mode_start`: Start away mode
- `eight_sleep.away_mode_stop`: Stop away mode

### Alarm Services
- `eight_sleep.alarm_snooze`: Snooze alarm
- `eight_sleep.alarm_stop`: Stop alarm
- `eight_sleep.alarm_dismiss`: Dismiss alarm

### Device Services
- `eight_sleep.prime_pod`: Prime the pod
- `eight_sleep.set_bed_side`: Configure bed side settings

## 🤖 Automation Examples

### Automatic Temperature Adjustment

```yaml
automation:
  - alias: "Cool Bed at Bedtime"
    trigger:
      platform: time
      at: "22:00:00"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.eight_sleep_left_side
        data:
          temperature: 18
```

### Sleep Stage Monitoring

```yaml
automation:
  - alias: "Notify Deep Sleep"
    trigger:
      platform: state
      entity_id: sensor.eight_sleep_sleep_stage_enhanced
      to: "Deep Sleep"
    action:
      - service: notify.mobile_app
        data:
          message: "Deep sleep detected - optimal rest phase"
```

### Away Mode Automation

```yaml
automation:
  - alias: "Start Away Mode When Gone"
    trigger:
      platform: state
      entity_id: person.your_name
      to: "not_home"
    action:
      - service: eight_sleep.away_mode_start
        target:
          entity_id: sensor.eight_sleep_sensor
```

## 🎨 Custom Card Features

### Temperature Control
- **Real-time Slider**: Adjust temperature from 16°C to 32°C
- **Preset Buttons**: Quick access to Cool, Warm, and Neutral settings
- **Side-specific Control**: Independent temperature control for each side
- **Visual Feedback**: Active sides are highlighted

### Sleep Metrics
- **Heart Rate**: Real-time heart rate monitoring
- **HRV**: Heart rate variability tracking
- **Breath Rate**: Respiratory rate monitoring
- **Sleep Quality**: Sleep quality score percentage

### Presence Detection
- **Visual Indicators**: Green dots show when someone is present
- **Side-specific**: Separate indicators for left and right sides
- **Real-time Updates**: Updates automatically when presence changes

### Responsive Design
- **Mobile Optimized**: Touch-friendly controls for mobile devices
- **Desktop Enhanced**: Full feature set for desktop use
- **Theme Support**: Automatically adapts to light/dark themes

## 🔍 Troubleshooting

### Integration Issues
1. **Authentication Failed**: Verify your Eight Sleep credentials
2. **No Devices Found**: Ensure your Eight Sleep device is online
3. **Connection Errors**: Check your internet connection and Eight Sleep service status

### Card Issues
1. **Card Not Loading**: Ensure Eight Sleep integration is properly configured
2. **Temperature Controls Not Working**: Check that climate entities are available
3. **Metrics Not Displaying**: Verify sensor entities are available and sleep session is active

### Sensor Issues
1. **No Sleep Data**: Ensure you're actively using the bed for sleep tracking
2. **Missing Sensors**: Check that all sensor entities are properly created
3. **Stale Data**: Verify the integration is updating regularly

## 📈 Performance

### Optimizations
- **Smart Polling**: Updates based on device state and activity
- **Connection Pooling**: Efficient API connection management
- **Caching**: Intelligent data caching to reduce API calls
- **Background Updates**: Non-critical data updates in background

### Error Recovery
- **Exponential Backoff**: Intelligent retry logic prevents API overload
- **Token Refresh**: Automatic token refresh when expired
- **Graceful Degradation**: Continues working during temporary API issues
- **Connection Monitoring**: Real-time connection status tracking

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Eight Sleep for providing the API
- Home Assistant community for inspiration and feedback
- Contributors who have helped improve this integration

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/lukas-clarke/eight_sleep/issues)
- **Discussions**: [Join the community discussion](https://github.com/lukas-clarke/eight_sleep/discussions)
- **Documentation**: [Full documentation](https://github.com/lukas-clarke/eight_sleep/wiki)

---

**Made with ❤️ for the Home Assistant community**