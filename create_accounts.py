import csv
from pathlib import Path
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.aerial.client import LedgerClient, NetworkConfig
from mnemonic import Mnemonic
import json

def generate_pocket_accounts(num_accounts, customer_prefix):
    # Resolve output file path to ~/pocket_accounts.csv
    output_path = Path("pocket_accounts1.csv").expanduser()
    
    # Configure the network (using Pocket Network testnet)
    # network = NetworkConfig(
    #     chain_id="testnet",
    #     url="http://localhost:8081",  # Adjust this URL based on your Pocket node
    #     fee_minimum_gas_price=0.00001,
    #     fee_denomination="upokt",
    #     staking_denomination="upokt",
    # )
    
    # # Initialize the client
    # client = LedgerClient(network)
    
    accounts = []
    for i in range(num_accounts):
        try:
            print(f"Creating account {i + 1}/{num_accounts}...")
            
            # Generate a new mnemonic
            mnemonic = Mnemonic("english").generate(256)
            
            # Create wallet from mnemonic
            wallet = LocalWallet.from_mnemonic(mnemonic, "pokt")
            
            # Get account details
            address = wallet.address()
            
            print(f"Account created with address: {address}")
            
            # Add the account details to the list
            accounts.append({
                "customer_id": f"{customer_prefix}_{i}",
                "operator_address": address,
                "mnemonic": mnemonic
            })
            
        except Exception as e:
            print(f"Error during account creation: {e}")
            continue
    
    # Write the accounts to a CSV file
    with open(output_path, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["customer_id", "operator_address", "mnemonic", "owner_address", "revshare_address", "publicly_exposed_url", "rpc_type"])
        writer.writeheader()
        writer.writerows(accounts)
    
    print(f"Accounts successfully generated and saved to {output_path}")

# Inputs
number_of_accounts = int(input("Enter the number of accounts to create: "))
customer_prefix = input("Enter a prefix for customer_id: ")

# Run the function
generate_pocket_accounts(number_of_accounts, customer_prefix)