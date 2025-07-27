#!/usr/bin/env python3
"""
Entity Analysis Script
Analyzes the discovered entities and identifies the most important ones for Home Assistant integration
"""

import json
import sys
from collections import defaultdict
from typing import Dict, List, Any

def analyze_entities(report_file: str = "enhanced_eight_sleep_api_report.json"):
    """Analyze the discovered entities and provide insights"""
    
    print("🔍 Analyzing discovered Eight Sleep entities...")
    print("=" * 60)
    
    # Load the report
    with open(report_file, 'r') as f:
        report = json.load(f)
    
    # Extract key information
    total_entities = report["exploration_summary"]["total_entities_discovered"]
    device_type = report["exploration_summary"]["device_type"]
    has_base = report["exploration_summary"]["has_base"]
    
    print(f"📊 Analysis Summary:")
    print(f"   Total Entities: {total_entities}")
    print(f"   Device Type: {device_type}")
    print(f"   Has Base: {has_base}")
    print()
    
    # Analyze entities by type
    entities_by_type = report["entities_by_type"]
    ha_recommendations = report["recommended_home_assistant_entities"]
    
    print("📈 Entities by Type:")
    for entity_type, entities in entities_by_type.items():
        print(f"   {entity_type}: {len(entities)} entities")
    print()
    
    print("🏠 Home Assistant Recommendations:")
    for category, entities in ha_recommendations.items():
        if entities:
            print(f"   {category}: {len(entities)} entities")
    print()
    
    # Find the most important entities
    print("⭐ Most Important Entities by Category:")
    
    # Temperature entities
    if "temperature" in entities_by_type:
        temp_entities = entities_by_type["temperature"]
        print(f"\n🌡️  Temperature Entities ({len(temp_entities)}):")
        for entity in temp_entities[:5]:  # Show top 5
            print(f"   - {entity['name']}: {entity['description']}")
            if entity.get('unit'):
                print(f"     Unit: {entity['unit']}")
    
    # Sleep entities
    if "sleep" in entities_by_type:
        sleep_entities = entities_by_type["sleep"]
        print(f"\n😴 Sleep Entities ({len(sleep_entities)}):")
        for entity in sleep_entities[:5]:  # Show top 5
            print(f"   - {entity['name']}: {entity['description']}")
    
    # Health entities
    if "health" in entities_by_type:
        health_entities = entities_by_type["health"]
        print(f"\n❤️  Health Entities ({len(health_entities)}):")
        for entity in health_entities[:5]:  # Show top 5
            print(f"   - {entity['name']}: {entity['description']}")
            if entity.get('unit'):
                print(f"     Unit: {entity['unit']}")
    
    # Device entities
    if "device" in entities_by_type:
        device_entities = entities_by_type["device"]
        print(f"\n🔧 Device Entities ({len(device_entities)}):")
        for entity in device_entities[:5]:  # Show top 5
            print(f"   - {entity['name']}: {entity['description']}")
    
    # Score entities
    if "score" in entities_by_type:
        score_entities = entities_by_type["score"]
        print(f"\n📊 Score Entities ({len(score_entities)}):")
        for entity in score_entities[:5]:  # Show top 5
            print(f"   - {entity['name']}: {entity['description']}")
    
    # Alarm entities
    if "alarm" in entities_by_type:
        alarm_entities = entities_by_type["alarm"]
        print(f"\n⏰ Alarm Entities ({len(alarm_entities)}):")
        for entity in alarm_entities[:5]:  # Show top 5
            print(f"   - {entity['name']}: {entity['description']}")
    
    # Find unique entities that aren't already in the integration
    print(f"\n🆕 New Entity Opportunities:")
    
    # Look for entities that might not be in the current integration
    new_opportunities = []
    
    for entity_type, entities in entities_by_type.items():
        for entity in entities:
            name = entity['name'].lower()
            # Look for entities that might be missing from current integration
            if any(keyword in name for keyword in [
                'hrv', 'respiratory', 'breath', 'pulse', 'bpm',
                'efficiency', 'quality', 'fitness', 'consistency',
                'latency', 'duration', 'breakdown', 'stage',
                'presence', 'away', 'priming', 'water',
                'analytics', 'insights', 'metrics', 'trends'
            ]):
                new_opportunities.append(entity)
    
    print(f"   Found {len(new_opportunities)} potential new entities:")
    for entity in new_opportunities[:10]:  # Show top 10
        print(f"   - {entity['name']} ({entity['type']}): {entity['description']}")
        if entity.get('unit'):
            print(f"     Unit: {entity['unit']}")
    
    # Generate implementation suggestions
    print(f"\n💡 Implementation Suggestions:")
    print(f"   1. Focus on health metrics (HRV, respiratory rate, heart rate)")
    print(f"   2. Implement sleep quality and efficiency sensors")
    print(f"   3. Add device health monitoring (water level, priming status)")
    print(f"   4. Create analytics and trend sensors")
    print(f"   5. Implement presence detection and away mode")
    print(f"   6. Add alarm and routine management")
    
    # Save focused analysis
    analysis = {
        "summary": {
            "total_entities": total_entities,
            "device_type": device_type,
            "has_base": has_base,
            "entities_by_type": dict(entities_by_type),
            "ha_recommendations": dict(ha_recommendations)
        },
        "new_opportunities": [dict(entity) for entity in new_opportunities],
        "implementation_suggestions": [
            "Focus on health metrics (HRV, respiratory rate, heart rate)",
            "Implement sleep quality and efficiency sensors", 
            "Add device health monitoring (water level, priming status)",
            "Create analytics and trend sensors",
            "Implement presence detection and away mode",
            "Add alarm and routine management"
        ]
    }
    
    with open("entity_analysis.json", 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"\n📄 Detailed analysis saved to: entity_analysis.json")
    
    return analysis

if __name__ == "__main__":
    analyze_entities() 