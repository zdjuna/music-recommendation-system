#!/usr/bin/env python3
"""
Syntax check script for all Python files in the repository
"""
import py_compile
import os
import sys

def check_syntax():
    """Check syntax of all Python files"""
    errors = []
    checked = 0
    
    for root, dirs, files in os.walk('.'):
        if any(skip in root for skip in ['node_modules', '.git', '__pycache__', '.pytest_cache']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    py_compile.compile(filepath, doraise=True)
                    checked += 1
                except py_compile.PyCompileError as e:
                    errors.append(f"Syntax error in {filepath}: {e}")
                except Exception as e:
                    errors.append(f"Error checking {filepath}: {e}")
    
    print(f"Checked {checked} Python files")
    if errors:
        print(f"Found {len(errors)} syntax errors:")
        for error in errors:
            print(f"  ❌ {error}")
        return False
    else:
        print("✅ All Python files have valid syntax")
        return True

if __name__ == "__main__":
    success = check_syntax()
    sys.exit(0 if success else 1)
