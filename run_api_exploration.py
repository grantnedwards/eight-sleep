#!/usr/bin/env python3
"""
Eight Sleep API Exploration Runner
Safely explores the Eight Sleep API to discover all available entities
"""

import asyncio
import sys
import os
from safe_api_explorer import EightSleepAPIExplorer

async def run_exploration(email: str, password: str):
    """Run the API exploration with provided credentials"""
    print("Starting Eight Sleep API exploration...")
    print(f"Email: {email}")
    print("=" * 50)
    
    # Create explorer instance
    explorer = EightSleepAPIExplorer(email, password)
    
    # Authenticate
    print("Authenticating with Eight Sleep API...")
    if not await explorer.authenticate():
        print("❌ Authentication failed. Please check your credentials.")
        return False
    
    print("✅ Authentication successful!")
    
    # Explore all endpoints
    print("\nExploring API endpoints...")
    await explorer.explore_api()
    
    # Generate and save report
    print("\nGenerating report...")
    await explorer.save_report()
    
    # Print summary
    report = explorer.generate_report()
    print("\n" + "=" * 50)
    print("EXPLORATION COMPLETE!")
    print("=" * 50)
    print(f"Total entities discovered: {len(explorer.discovered_entities)}")
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
    
    print(f"\n📄 Detailed report saved to: eight_sleep_api_report.json")
    print(f"📄 Summary saved to: eight_sleep_api_report_summary.txt")
    
    return True

def main():
    """Main function"""
    print("Eight Sleep API Explorer")
    print("=" * 30)
    print("This script will safely explore the Eight Sleep API")
    print("to discover all available entities for your Pod 4.")
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
        success = asyncio.run(run_exploration(email, password))
        if success:
            print("\n✅ API exploration completed successfully!")
        else:
            print("\n❌ API exploration failed.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Exploration interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during exploration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 