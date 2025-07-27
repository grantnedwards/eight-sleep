#!/usr/bin/env python3
"""
Test script for Eight Sleep Home Assistant Integration
This script validates the integration structure and identifies potential issues.
"""

import os
import sys
import ast
import json
from pathlib import Path
from typing import List, Dict, Any

def check_file_structure() -> Dict[str, Any]:
    """Check if the integration has the correct file structure."""
    results = {
        "valid": True,
        "missing_files": [],
        "required_files": [
            "custom_components/eight_sleep/__init__.py",
            "custom_components/eight_sleep/manifest.json",
            "custom_components/eight_sleep/config_flow.py",
            "custom_components/eight_sleep/const.py",
            "custom_components/eight_sleep/strings.json",
            "custom_components/eight_sleep/translations/en.json",
            "hacs.json"
        ]
    }
    
    for file_path in results["required_files"]:
        if not os.path.exists(file_path):
            results["missing_files"].append(file_path)
            results["valid"] = False
    
    return results

def validate_manifest() -> Dict[str, Any]:
    """Validate the manifest.json file."""
    results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    try:
        with open("custom_components/eight_sleep/manifest.json", "r") as f:
            manifest = json.load(f)
        
        required_fields = ["domain", "name", "codeowners", "config_flow", "documentation", "integration_type", "iot_class", "requirements", "version"]
        
        for field in required_fields:
            if field not in manifest:
                results["errors"].append(f"Missing required field: {field}")
                results["valid"] = False
        
        # Check specific values
        if manifest.get("domain") != "eight_sleep":
            results["errors"].append("Domain should be 'eight_sleep'")
            results["valid"] = False
            
        if manifest.get("integration_type") != "hub":
            results["warnings"].append("Integration type should be 'hub' for this type of integration")
            
        if "frontend" in manifest:
            if "js_type" not in manifest["frontend"] or "js_url" not in manifest["frontend"]:
                results["errors"].append("Frontend configuration incomplete")
                results["valid"] = False
                
    except Exception as e:
        results["errors"].append(f"Failed to parse manifest.json: {str(e)}")
        results["valid"] = False
    
    return results

def validate_hacs_json() -> Dict[str, Any]:
    """Validate the hacs.json file."""
    results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    try:
        with open("hacs.json", "r") as f:
            hacs_config = json.load(f)
        
        required_fields = ["name", "homeassistant"]
        
        for field in required_fields:
            if field not in hacs_config:
                results["errors"].append(f"Missing required field: {field}")
                results["valid"] = False
        
        # Check Home Assistant version compatibility
        ha_version = hacs_config.get("homeassistant", "")
        if ha_version < "2023.9.1":
            results["warnings"].append(f"Home Assistant version {ha_version} might be too old")
            
    except Exception as e:
        results["errors"].append(f"Failed to parse hacs.json: {str(e)}")
        results["valid"] = False
    
    return results

def check_syntax_errors() -> Dict[str, Any]:
    """Check for Python syntax errors in all .py files."""
    results = {
        "valid": True,
        "errors": [],
        "files_checked": 0
    }
    
    python_files = []
    for root, dirs, files in os.walk("custom_components/eight_sleep"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    for file_path in python_files:
        results["files_checked"] += 1
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Try to parse the file
            ast.parse(content)
            
        except SyntaxError as e:
            results["errors"].append(f"Syntax error in {file_path}: {str(e)}")
            results["valid"] = False
        except Exception as e:
            results["errors"].append(f"Error reading {file_path}: {str(e)}")
            results["valid"] = False
    
    return results

def check_imports() -> Dict[str, Any]:
    """Check for import issues in the main integration files."""
    results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    critical_files = [
        "custom_components/eight_sleep/__init__.py",
        "custom_components/eight_sleep/config_flow.py",
        "custom_components/eight_sleep/const.py"
    ]
    
    for file_path in critical_files:
        if not os.path.exists(file_path):
            results["errors"].append(f"Critical file missing: {file_path}")
            results["valid"] = False
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for common import issues
            if "from __future__ import annotations" not in content:
                results["warnings"].append(f"Missing future annotations import in {file_path}")
            
            # Check for proper Home Assistant imports
            if "homeassistant" not in content:
                results["warnings"].append(f"No Home Assistant imports found in {file_path}")
                
        except Exception as e:
            results["errors"].append(f"Error checking imports in {file_path}: {str(e)}")
            results["valid"] = False
    
    return results

def check_translations() -> Dict[str, Any]:
    """Check translation files."""
    results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    translation_files = [
        "custom_components/eight_sleep/strings.json",
        "custom_components/eight_sleep/translations/en.json"
    ]
    
    for file_path in translation_files:
        if not os.path.exists(file_path):
            results["errors"].append(f"Translation file missing: {file_path}")
            results["valid"] = False
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json.load(f)  # Validate JSON
        except Exception as e:
            results["errors"].append(f"Invalid JSON in {file_path}: {str(e)}")
            results["valid"] = False
    
    return results

def check_frontend() -> Dict[str, Any]:
    """Check frontend components."""
    results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    frontend_files = [
        "custom_components/eight_sleep/frontend/panel.js",
        "custom_components/eight_sleep/frontend/dist/eight-sleep-bed-card.js"
    ]
    
    for file_path in frontend_files:
        if not os.path.exists(file_path):
            results["warnings"].append(f"Frontend file missing: {file_path}")
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if len(content.strip()) == 0:
                    results["warnings"].append(f"Frontend file is empty: {file_path}")
            except Exception as e:
                results["errors"].append(f"Error reading frontend file {file_path}: {str(e)}")
                results["valid"] = False
    
    return results

def run_all_tests() -> Dict[str, Any]:
    """Run all validation tests."""
    print("🔍 Running Eight Sleep Integration Tests...")
    print("=" * 50)
    
    all_results = {
        "overall_valid": True,
        "tests": {}
    }
    
    # Run all tests
    tests = [
        ("File Structure", check_file_structure),
        ("Manifest Validation", validate_manifest),
        ("HACS Configuration", validate_hacs_json),
        ("Syntax Check", check_syntax_errors),
        ("Import Check", check_imports),
        ("Translations", check_translations),
        ("Frontend", check_frontend)
    ]
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        result = test_func()
        all_results["tests"][test_name] = result
        
        if result["valid"]:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
            all_results["overall_valid"] = False
        
        # Print details
        if result.get("errors"):
            for error in result["errors"]:
                print(f"   ❌ Error: {error}")
        
        if result.get("warnings"):
            for warning in result["warnings"]:
                print(f"   ⚠️  Warning: {warning}")
        
        if result.get("missing_files"):
            for file in result["missing_files"]:
                print(f"   📁 Missing: {file}")
    
    # Summary
    print("\n" + "=" * 50)
    if all_results["overall_valid"]:
        print("🎉 All tests passed! Integration appears to be valid.")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    return all_results

if __name__ == "__main__":
    results = run_all_tests()
    
    # Exit with appropriate code
    if results["overall_valid"]:
        sys.exit(0)
    else:
        sys.exit(1) 