#!/usr/bin/env python3
"""
Script to override services in customer config YAML files.

This script prompts the user for a folder containing customer config YAML files and an override YAML file,
then updates all config files by replacing their services section with the services from the override file.

Usage:
    python override_customer_services_config_files.py
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file '{file_path}': {e}")
        sys.exit(1)


def save_yaml_file(file_path: str, data: Dict[str, Any]) -> None:
    """Save data to a YAML file with proper formatting."""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(data, file, default_flow_style=False, sort_keys=False, indent=2)
    except Exception as e:
        print(f"Error saving file '{file_path}': {e}")
        sys.exit(1)


def update_config_with_override(config_data: Dict[str, Any], override_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update config data with override services."""
    # Create a copy of the config data
    updated_config = config_data.copy()
    
    # Replace the services section with the override services
    if 'services' in override_data:
        updated_config['services'] = override_data['services']
        print(f"  - Updated services section with {len(override_data['services'])} services")
    else:
        print(f"  - Warning: No 'services' section found in override file")
    
    return updated_config


def get_user_input(prompt: str, default: str = "") -> str:
    """Get user input with optional default value."""
    if default:
        user_input = input(f"{prompt} (default: {default}): ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()


def confirm_action(message: str) -> bool:
    """Ask user to confirm an action."""
    while True:
        response = input(f"{message} (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")


def process_config_files(config_folder: str, override_file: str) -> None:
    """Process all YAML files in the config folder and apply override."""
    
    # Validate inputs
    config_path = Path(config_folder)
    override_path = Path(override_file)
    
    if not config_path.exists():
        print(f"Error: Config folder '{config_folder}' does not exist.")
        sys.exit(1)
    
    if not config_path.is_dir():
        print(f"Error: '{config_folder}' is not a directory.")
        sys.exit(1)
    
    if not override_path.exists():
        print(f"Error: Override file '{override_file}' does not exist.")
        sys.exit(1)
    
    # Load override data
    print(f"Loading override file: {override_file}")
    override_data = load_yaml_file(override_file)
    
    # Find all YAML files in the config folder
    yaml_files = list(config_path.glob("*.yml")) + list(config_path.glob("*.yaml"))
    
    if not yaml_files:
        print(f"No YAML files found in '{config_folder}'")
        return
    
    print(f"Found {len(yaml_files)} YAML files to process")
    
    # Show preview of files that will be processed
    print("\nFiles that will be processed:")
    for yaml_file in yaml_files:
        print(f"  - {yaml_file.name}")
    
    # Ask for confirmation
    if not confirm_action(f"\nDo you want to proceed with updating {len(yaml_files)} files?"):
        print("Operation cancelled.")
        return
    
    # Process each YAML file
    for yaml_file in yaml_files:
        print(f"\nProcessing: {yaml_file.name}")
        
        # Load config file
        config_data = load_yaml_file(str(yaml_file))
        
        # Check if config has services section
        if 'services' not in config_data:
            print(f"  - Warning: No 'services' section found in {yaml_file.name}")
            continue
        
        # Update config with override
        updated_config = update_config_with_override(config_data, override_data)
        
        # Save updated config
        save_yaml_file(str(yaml_file), updated_config)
        print(f"  - Successfully updated {yaml_file.name}")
    
    print(f"\nCOMPLETED: {len(yaml_files)} files updated successfully")


def main():
    """Main function to handle user input and execute the script."""
    print("Customer Services Config Override Tool")
    print("=" * 50)
    print()
    
    # Get config folder from user
    config_folder = get_user_input("Enter the folder path containing customer config YAML files")
    
    # Get override file from user
    override_file = get_user_input("Enter the path to the override YAML file")
    
    print()
    print("Configuration:")
    print(f"  Config folder: {config_folder}")
    print(f"  Override file: {override_file}")
    print()
    
    process_config_files(config_folder, override_file)


if __name__ == "__main__":
    main()
