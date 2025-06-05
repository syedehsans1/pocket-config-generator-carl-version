#!/usr/bin/env python3

import csv
import os
import yaml
import subprocess
from google.protobuf.message import Message
import json
from dotenv import load_dotenv
import time

def read_wallets(csv_file):
    wallets = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            wallets.append(row)
    return wallets

def generate_stake_config(wallet_data, template_file, stake_amount):
    # Read the template
    with open(template_file, 'r') as f:
        template = f.read()
    
    # Replace placeholders
    config = template.replace('<owner_address>', wallet_data['owner_address'])
    config = config.replace('<operator_address>', wallet_data['operator_address'])
    config = config.replace('<stake_amount>', stake_amount)
    
    # Parse as YAML to handle the rev share percentages
    config_dict = yaml.safe_load(config)
    config_dict['default_rev_share_percent'] = {
        wallet_data['owner_address']: 50,
        wallet_data['revshare_address']: 50
    }
    
    # Create directory if it doesn't exist
    output_dir = "initial-stake-files"
    os.makedirs(output_dir, exist_ok=True)
    
    # Write to file
    output_path = f"{output_dir}/supplier-stake-{wallet_data['customer_id']}.yaml"
    with open(output_path, 'w') as f:
        yaml.dump(config_dict, f)
    
    return output_path

def stake_wallet(wallet_data, config_file, network):
    """Execute the stake supplier command using the CLI."""
    cmd = [
        "pocketd", "tx", "supplier", "stake-supplier",
        f"--config={config_file}",
        f"--from={wallet_data['owner_address']}",
        "--gas=auto",
        "--gas-prices=1upokt",
        "--gas-adjustment=1.5",
        "--yes",
        f"--network={network}",
        "--keyring-backend=test", "--unordered", "--timeout-duration=1m"
    ]
    
    try:
        print(cmd)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Successfully staked for {wallet_data['operator_address']}")
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
    
    # Get network and RPC endpoint from env
    network = os.getenv('NETWORK')
    
    if not network:
        print("Error: NETWORK environment variable must be set in .env file")
        return
    
    # Read wallets
    filename = input("Enter filename to read wallets from (Case-Sensitive): ")
    stake_amount = input("Enter stake amount in upokt (1POKT=1000000upokt): ")
	
    wallets = read_wallets(filename)
    
    # Process each wallet
    for wallet in wallets:
        config_file = generate_stake_config(wallet, 'sample.yml', stake_amount)
        print(f"Generated config file: {config_file}")
        
        try:
            # stake the wallet
            success = stake_wallet(wallet, config_file, network)
            # wait for 30 seconds
            # time.sleep(15)
            # os.remove(config_file)
            if not success:
                print(f"Failed to stake for {wallet['operator_address']}")
        except Exception as e:
            print(f"Error staking for {wallet['operator_address']}: {e}")
            pass


if __name__ == "__main__":
    main()
