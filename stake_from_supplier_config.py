#!/usr/bin/env python3

import csv
import os
import yaml
import subprocess
from google.protobuf.message import Message
import json
from dotenv import load_dotenv
import time


def stake_wallet(config_file, network, is_owner):
    """Execute the stake supplier command using the CLI."""
    # Read the config file to get the addresses
    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Get the addresses from default_rev_share_percent
    rev_share_addresses = list(config_data['default_rev_share_percent'].keys())
    if len(rev_share_addresses) != 2:
        print(f"Error: Expected exactly 2 addresses in default_rev_share_percent for {config_file}")
        return False
    
    # First address is owner, second address is revshare
    owner_address = rev_share_addresses[0]
    revshare_address = rev_share_addresses[1]
    
    # Use owner address if user is owner, otherwise use revshare address
    from_address = owner_address if is_owner else revshare_address
    
    cmd = [
        "pocketd", "tx", "supplier", "stake-supplier",
        f"--config={config_file}",
        f"--from={from_address}",
        "--gas=auto",
        "--gas-prices=1upokt",
        "--gas-adjustment=1.5",
        "--yes",
        f"--network={network}",
        "--keyring-backend=test", "--unordered", "--timeout-duration=1m"
    ]
    
    try:
        print(f"Executing stake command for {config_file} using address: {from_address}")
        print("Command:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Successfully staked using {from_address}")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing stake command: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get network from env
    network = os.getenv('NETWORK')
    
    if not network:
        print("Error: NETWORK environment variable must be set in .env file")
        return
    
    # Ask user if they are the owner
    while True:
        user_input = input("Are you the owner? (yes/no): ").lower().strip()
        if user_input in ['yes', 'no']:
            is_owner = user_input == 'yes'
            break
        print("Please answer 'yes' or 'no'")
    
    # Get list of YAML files in the output directory
    foldername = input("Enter foldername to read supplier config yaml files from: ")
    output_dir = foldername
    if not os.path.exists(output_dir):
        print(f"Error: {output_dir} directory not found")
        return
    
    yaml_files = [f for f in os.listdir(output_dir) if f.endswith('.yml') or f.endswith('.yaml')]
    
    if not yaml_files:
        print(f"No YAML files found in {output_dir} directory")
        return
    
    print(f"\nFound {len(yaml_files)} configuration files to process")
    
    # Process each YAML file
    for yaml_file in yaml_files:
        config_path = os.path.join(output_dir, yaml_file)
        print(f"\nProcessing {yaml_file}...")
        
        try:
            success = stake_wallet(config_path, network, is_owner)
            if not success:
                print(f"Failed to stake using {yaml_file}")
            # Add a small delay between stakes to avoid rate limiting
            time.sleep(2)
        except Exception as e:
            print(f"Error processing {yaml_file}: {e}")
            continue

if __name__ == "__main__":
    main()
