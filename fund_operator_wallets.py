#!/usr/bin/env python3

import csv
import sys
import time
import os
import subprocess
from typing import List, Tuple
from dotenv import load_dotenv

def read_addresses(csv_filename: str) -> List[Tuple[str, str]]:
    """Read owner and operator addresses from CSV file."""
    addresses = []
    try:
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                owner_address = row['owner_address']
                operator_address = row['operator_address']
                addresses.append((owner_address, operator_address))
    except FileNotFoundError:
        print(f"Error: File '{csv_filename}' not found.")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Required column {e} not found in CSV file.")
        sys.exit(1)
    return addresses

def send_funds(owner_address: str, operator_address: str, amount: str) -> None:
    """Execute the pocketd send command."""
    load_dotenv()
    network = os.getenv('NETWORK')
    cmd = [
        'pocketd', 'tx', 'bank', 'send',
        owner_address,
        operator_address,
        f"{amount}upokt",
        f"--from={owner_address}",
        '--gas=auto',
        '--gas-prices=1upokt',
        '--gas-adjustment=1.5',
        '--yes',
        f"--network={network}",
        '--keyring-backend=test',
        "--unordered",
        "--timeout-duration=1m"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        
        if result.returncode == 0:
            print(f"Successfully sent {amount} upokt from {owner_address} to {operator_address}")
        else:
            print(f"Error sending funds from {owner_address} to {operator_address}:")
            print(result.stderr)
        # time.sleep(30)
    except Exception as e:
        print(f"Error executing command: {e}")

def main():
    csv_filename = input("Enter filename to read wallets from (Case-Sensitive): ")
    # csv_filename = sys.argv[1]
    addresses = read_addresses(csv_filename)
    
    if not addresses:
        print("No addresses found in the CSV file.")
        sys.exit(1)

    # Get funding amount from user
    while True:
        try:
            amount = input("Enter the amount of upokt to send to each operator (1POKT=1000000UPOKT): ")
            # Validate that amount is a positive number
            amount_float = int(amount)
            if amount_float <= 0:
                print("Amount must be greater than 0")
                continue
            break
        except ValueError:
            print("Please enter a valid number")

    print(f"\nSending {amount} upokt to {len(addresses)} operators...")
    
    for owner_address, operator_address in addresses:
        print(f"\nProcessing transfer from {owner_address} to {operator_address}")
        send_funds(owner_address, operator_address, amount)

if __name__ == "__main__":
    main()
