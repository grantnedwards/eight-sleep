#!/usr/bin/env python3
"""
Script to fix common linting issues in the Eight Sleep integration.
"""

import os
import re
from pathlib import Path

def fix_trailing_whitespace(file_path: str) -> int:
    """Remove trailing whitespace from a file."""
    fixed_count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                original_line = line
                line = line.rstrip() + '\n'
                if original_line != line:
                    fixed_count += 1
                f.write(line)
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
    
    return fixed_count

def fix_blank_lines_with_whitespace(file_path: str) -> int:
    """Remove whitespace from blank lines."""
    fixed_count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace lines that contain only whitespace with empty lines
        original_content = content
        content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_count = 1
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
    
    return fixed_count

def fix_missing_newline_at_end(file_path: str) -> int:
    """Ensure file ends with a newline."""
    fixed_count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content and not content.endswith('\n'):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content + '\n')
            fixed_count = 1
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
    
    return fixed_count

def fix_line_length(file_path: str, max_length: int = 120) -> int:
    """Fix lines that are too long by breaking them appropriately."""
    fixed_count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            if len(line.rstrip()) > max_length and not line.strip().startswith('#'):
                # Try to break long lines at appropriate points
                if '(' in line and ')' in line:
                    # Break function calls
                    parts = line.split('(')
                    if len(parts) > 1:
                        func_name = parts[0]
                        args = '(' + parts[1]
                        if len(func_name) + len(args) > max_length:
                            # Break at commas in arguments
                            args_parts = args.split(',')
                            if len(args_parts) > 1:
                                new_line = func_name + args_parts[0] + ','
                                new_lines.append(new_line)
                                for part in args_parts[1:-1]:
                                    new_lines.append('    ' + part.strip() + ',')
                                new_lines.append('    ' + args_parts[-1])
                                fixed_count += 1
                                continue
            
            new_lines.append(line)
        
        if fixed_count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
    
    return fixed_count

def fix_unused_imports(file_path: str) -> int:
    """Remove unused imports (basic implementation)."""
    fixed_count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # This is a basic implementation - in practice, you'd want a more sophisticated approach
        # For now, we'll just fix some common patterns
        
        # Remove empty import lines
        original_content = content
        content = re.sub(r'from \. import\s*\n', '', content)
        content = re.sub(r'import \.diagnostics\s*\n', '', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_count = 1
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
    
    return fixed_count

def process_file(file_path: str) -> dict:
    """Process a single file and fix common issues."""
    results = {
        'file': file_path,
        'trailing_whitespace': 0,
        'blank_lines': 0,
        'missing_newline': 0,
        'line_length': 0,
        'unused_imports': 0
    }
    
    if file_path.endswith('.py'):
        results['trailing_whitespace'] = fix_trailing_whitespace(file_path)
        results['blank_lines'] = fix_blank_lines_with_whitespace(file_path)
        results['missing_newline'] = fix_missing_newline_at_end(file_path)
        results['line_length'] = fix_line_length(file_path)
        results['unused_imports'] = fix_unused_imports(file_path)
    
    return results

def main():
    """Main function to process all Python files in the integration."""
    print("🔧 Fixing linting issues in Eight Sleep integration...")
    print("=" * 60)
    
    total_fixes = {
        'trailing_whitespace': 0,
        'blank_lines': 0,
        'missing_newline': 0,
        'line_length': 0,
        'unused_imports': 0,
        'files_processed': 0
    }
    
    # Process all Python files in the custom_components directory
    integration_dir = Path("custom_components/eight_sleep")
    
    if not integration_dir.exists():
        print("❌ Integration directory not found!")
        return
    
    for py_file in integration_dir.rglob("*.py"):
        print(f"📝 Processing {py_file}...")
        results = process_file(str(py_file))
        total_fixes['files_processed'] += 1
        
        # Sum up fixes
        for key in total_fixes:
            if key in results:
                total_fixes[key] += results[key]
        
        # Report fixes for this file
        file_fixes = sum(v for k, v in results.items() if k != 'file')
        if file_fixes > 0:
            print(f"   ✅ Fixed {file_fixes} issues")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary of fixes:")
    print(f"   Files processed: {total_fixes['files_processed']}")
    print(f"   Trailing whitespace removed: {total_fixes['trailing_whitespace']}")
    print(f"   Blank lines with whitespace fixed: {total_fixes['blank_lines']}")
    print(f"   Missing newlines added: {total_fixes['missing_newline']}")
    print(f"   Long lines fixed: {total_fixes['line_length']}")
    print(f"   Unused imports removed: {total_fixes['unused_imports']}")
    
    total_issues = sum(total_fixes.values()) - total_fixes['files_processed']
    print(f"\n🎉 Total issues fixed: {total_issues}")

if __name__ == "__main__":
    main() 