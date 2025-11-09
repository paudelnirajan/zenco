#!/usr/bin/env python3
"""
Build and publish script for Zenco package to PyPI.
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(e.stderr)
        return False

def main():
    """Main build and publish workflow."""
    print("🚀 Zenco Package Build & Publish Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("pyproject.toml"):
        print("❌ Error: pyproject.toml not found. Run this script from the project root.")
        sys.exit(1)
    
    # Clean previous builds
    if not run_command("rm -rf dist/ build/ *.egg-info/", "Cleaning previous builds"):
        sys.exit(1)
    
    # Install build dependencies
    if not run_command("pip install --upgrade build twine", "Installing build dependencies"):
        sys.exit(1)
    
    # Build the package
    if not run_command("python -m build", "Building package"):
        sys.exit(1)
    
    # Check the package
    if not run_command("twine check dist/*", "Checking package"):
        sys.exit(1)
    
    print("\n🎉 Package built successfully!")
    print("\nNext steps:")
    print("1. Test upload to TestPyPI:")
    print("   twine upload --repository testpypi dist/*")
    print("\n2. If test is successful, upload to PyPI:")
    print("   twine upload dist/*")
    print("\n3. Install and test:")
    print("   pip install zenco")
    print("   zenco --help")

if __name__ == "__main__":
    main()
