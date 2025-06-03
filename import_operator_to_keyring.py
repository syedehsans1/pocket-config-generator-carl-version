#!/usr/bin/env python3

import csv
import subprocess
import sys
from pathlib import Path

def import_accounts_to_keyring(csv_file):
    """
    Read the CSV file and import each account to the keyring using pocketd
    """
    if not Path(csv_file).exists():
        print(f"Error: {csv_file} not found!")
        sys.exit(1)

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            customer_id = row['customer_id']
            mnemonic = row['mnemonic']
            
            # Construct the command
            cmd = [
                'pocketd', 'keys', 'add',
                customer_id,
                '--recover',
                '--keyring-backend=test',
                # '--yes'  # Automatically answer yes to prompts
            ]
            
            print(f"\nImporting account {customer_id}...")
            try:
                # Run the command and provide the mnemonic through stdin
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Send the mnemonic to the process
                stdout, stderr = process.communicate(input=mnemonic)
                
                if process.returncode == 0:
                    print(f"Successfully imported {customer_id}")
                else:
                    print(f"Error importing {customer_id}:")
                    print(stderr)
                    
            except Exception as e:
                print(f"Error running command for {customer_id}: {str(e)}")

if __name__ == "__main__":
    csv_file = "pocket_accounts.csv"
    print("Starting account import process...")
    import_accounts_to_keyring(csv_file)
    print("\nAccount import process completed!")
