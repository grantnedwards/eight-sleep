# Eight Sleep Bed Card

A beautiful and functional custom Lovelace card for controlling Eight Sleep bed temperature and viewing sleep metrics in real-time.

## Features

- **Real-time Temperature Control**: Adjust bed temperature with sliders and preset buttons
- **Visual Bed Presence Indicators**: See when someone is on each side of the bed
- **Sleep Metrics Display**: View heart rate, HRV, breath rate, and sleep quality
- **Responsive Design**: Works on mobile and desktop devices
- **Dark/Light Theme Support**: Automatically adapts to your Home Assistant theme
- **Side-by-Side Controls**: Independent control for left and right sides

## Installation

1. Install this integration via HACS
2. Add the card to your Lovelace dashboard
3. Configure the card with your Eight Sleep entities

## Configuration

### Basic Configuration

```yaml
type: custom:eight-sleep-bed-card
title: "Eight Sleep Bed"
left_side: "left"
right_side: "right"
```

### Advanced Configuration

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

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | string | "Eight Sleep Bed" | Card title |
| `left_side` | string | "left" | Left side identifier |
| `right_side` | string | "right" | Right side identifier |
| `show_metrics` | boolean | true | Show sleep metrics section |
| `show_presence` | boolean | true | Show presence indicators |
| `temperature_range` | object | {min: 16, max: 32, step: 0.5} | Temperature slider range |

## Entity Requirements

The card automatically detects Eight Sleep entities with the following patterns:

### Climate Entities
- `climate.*` with friendly name containing "Eight Sleep"
- Used for temperature control and heating/cooling

### Sensor Entities  
- `sensor.*` with friendly name containing "Eight Sleep"
- Used for sleep metrics (heart rate, HRV, breath rate, sleep quality)

### Binary Sensor Entities
- `binary_sensor.*` with friendly name containing "Eight Sleep" and "presence"
- Used for bed presence detection

## Usage Examples

### Basic Temperature Control

```yaml
type: custom:eight-sleep-bed-card
title: "Bed Temperature"
```

### Sleep Monitoring Dashboard

```yaml
type: custom:eight-sleep-bed-card
title: "Sleep Monitoring"
show_metrics: true
show_presence: true
```

### Minimal Configuration

```yaml
type: custom:eight-sleep-bed-card
```

## Features

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

## Troubleshooting

### Card Not Loading
1. Ensure Eight Sleep integration is properly configured
2. Check that climate entities are available
3. Verify entity names contain "Eight Sleep"

### Temperature Controls Not Working
1. Check that climate entities are in the correct state
2. Verify entity permissions allow temperature changes
3. Ensure the bed is powered on

### Metrics Not Displaying
1. Verify sensor entities are available
2. Check that sleep session is active
3. Ensure entities contain the expected data

### Presence Not Detecting
1. Check binary sensor entities for presence
2. Verify sensor names contain "presence"
3. Ensure bed sensors are functioning

## Development

This card is built using:
- **Lit**: Modern web components framework
- **Home Assistant Lovelace**: Integration with Home Assistant UI
- **CSS Grid/Flexbox**: Responsive layout system
- **Material Design**: Consistent visual design

## Support

For issues and feature requests, please visit the [GitHub repository](https://github.com/lukas-clarke/eight_sleep). 