#!/usr/bin/env python3
"""
Enhanced Eight Sleep API Exploration Runner
Comprehensive exploration of the Eight Sleep API to discover ALL available entities
"""

import asyncio
import sys
import os
from enhanced_api_explorer import EnhancedEightSleepAPIExplorer

async def run_enhanced_exploration(email: str, password: str):
    """Run the enhanced API exploration with provided credentials"""
    print("Starting Enhanced Eight Sleep API exploration...")
    print(f"Email: {email}")
    print("=" * 60)
    
    # Create explorer instance
    explorer = EnhancedEightSleepAPIExplorer(email, password)
    
    # Authenticate
    print("Authenticating with Eight Sleep API...")
    if not await explorer.authenticate():
        print("❌ Authentication failed. Please check your credentials.")
        return False
    
    print("✅ Authentication successful!")
    
    # Explore all endpoints comprehensively
    print("\n🔍 Exploring API endpoints comprehensively...")
    await explorer.explore_api_comprehensive()
    
    # Generate and save report
    print("\n📊 Generating comprehensive report...")
    await explorer.save_report()
    
    # Print summary
    report = explorer.generate_report()
    print("\n" + "=" * 60)
    print("ENHANCED EXPLORATION COMPLETE!")
    print("=" * 60)
    print(f"Total entities discovered: {len(explorer.discovered_entities)}")
    print(f"Total endpoints explored: {len(explorer.api_endpoints)}")
    print(f"Unique URLs explored: {len(explorer.explored_urls)}")
    print(f"Device type: {'Pod 4' if explorer._is_pod else 'Unknown'}")
    print(f"Has base: {explorer._has_base}")
    print(f"Device IDs: {explorer._device_ids}")
    
    print("\nEntities by type:")
    for entity_type, entities in report["entities_by_type"].items():
        print(f"  {entity_type}: {len(entities)} entities")
    
    print("\nRecommended Home Assistant entities:")
    for category, entities in report["recommended_home_assistant_entities"].items():
        if entities:  # Only show categories with entities
            print(f"  {category}: {len(entities)} entities")
    
    print(f"\n📄 Enhanced report saved to: enhanced_eight_sleep_api_report.json")
    print(f"📄 Summary saved to: enhanced_eight_sleep_api_report_summary.txt")
    
    return True

def main():
    """Main function"""
    print("Enhanced Eight Sleep API Explorer")
    print("=" * 40)
    print("This script will comprehensively explore the Eight Sleep API")
    print("to discover ALL available entities for your Pod 4.")
    print()
    
    # Get credentials
    if len(sys.argv) == 3:
        email = sys.argv[1]
        password = sys.argv[2]
    else:
        print("Please provide your Eight Sleep credentials:")
        email = input("Email: ").strip()
        password = input("Password: ").strip()
    
    if not email or not password:
        print("❌ Email and password are required.")
        sys.exit(1)
    
    # Run exploration
    try:
        success = asyncio.run(run_enhanced_exploration(email, password))
        if success:
            print("\n✅ Enhanced API exploration completed successfully!")
        else:
            print("\n❌ Enhanced API exploration failed.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Exploration interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during exploration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 