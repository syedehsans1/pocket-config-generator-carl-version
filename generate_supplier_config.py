import os
import sys
import pandas as pd
import yaml

def load_service_mapping():
	"""Load the Morse to Shannon service ID mapping."""
	try:
		mapping_df = pd.read_csv('morse_to_shannon_service_mapping.csv')
		# Create a dictionary mapping Morse Chain IDs to Shannon Service IDs
		return dict(zip(mapping_df['Morse_Chain_Id'], mapping_df['Shannon_Service_id']))
	except Exception as e:
		print(f"Error loading service mapping: {e}")
		return {}

def load_wallet_data():
	"""Load wallet information from pocket_accounts.csv."""
	try:
		wallets_df = pd.read_csv('pocket_accounts.csv')
		# Create a dictionary mapping customer_id to wallet details
		return {row['customer_id']: {
			'operator_address': row['operator_address'],
			'owner_address': row['owner_address'],
			'revshare_address': row['revshare_address'],
			'publicly_exposed_url': row['publicly_exposed_url'] if pd.notna(row['publicly_exposed_url']) else 'https://relayminer.example.com'
		} for _, row in wallets_df.iterrows()}
	except Exception as e:
		print(f"Error loading wallet data: {e}")
		return {}

def extract_morse_chain_id(service_id):
	"""Extract Morse Chain ID from service ID string (e.g., 'Avalanche (F003)' -> 'F003')."""
	import re
	match = re.search(r'\(([A-F0-9]{4})\)', service_id)
	return match.group(1) if match else None

def main():
	# Create output directory if it doesn't exist
	os.makedirs('output', exist_ok=True)
	
	# Load service ID mapping and wallet data
	service_mapping = load_service_mapping()
	wallet_data = load_wallet_data()
	
	if not service_mapping:
		print("Warning: Could not load service mapping. Using original service IDs.")
	if not wallet_data:
		print("Error: Could not load wallet data. Exiting.")
		sys.exit(1)
	
	# Read NodeAllocation.csv
	df = pd.read_csv('NodeAllocation.csv')
 
	# drop last column from df
	df = df.iloc[:, :-1]
	# drop last row from df
	df = df.iloc[:-1, :]
	# replace all NaN with 0
	df = df.fillna(0)
	
	# Get the numeric columns (excluding 'Chains', 'Node Type', 'StakeNodes')
	numeric_columns = [col for col in df.columns[3:] if col.isdigit()]
	
	# Check if we have more columns than wallet entries
	if len(numeric_columns) > len(wallet_data):
		print(f"Warning: Found {len(numeric_columns)} columns in NodeAllocation.csv but only {len(wallet_data)} wallet entries.")
		print("Extra columns will be skipped.")
	
	# Create mapping between column numbers and row indices
	# Each column number maps to its corresponding row index in wallet_data
	column_to_row = {}
	wallet_entries = list(wallet_data.items())  # Convert wallet_data to list of (customer_id, data) tuples
	
	for i, col in enumerate(numeric_columns):
		if i < len(wallet_entries):
			customer_id, wallet_info = wallet_entries[i]
			column_to_row[col] = customer_id
		else:
			print(f"Warning: No wallet data found for column {col}. Skipping this column.")
	
	if not column_to_row:
		print("Error: No valid column to row mappings found. Exiting.")
		sys.exit(1)
	
	# Iterate over each mapped column and create YAML for corresponding customer
	for col_num, customer_id in column_to_row.items():
		wallet_info = wallet_data[customer_id]
		
		# Create base YAML structure for this customer
		yaml_data = {
			'owner_address': wallet_info['owner_address'],
			'operator_address': wallet_info['operator_address'],
			'stake_amount': '1000000upokt',
			'default_rev_share_percent': {
				wallet_info['owner_address']: 50,
				wallet_info['operator_address']: 50
			},
			'services': []
		}
		
		# Add services for this customer
		for index, row in df.iterrows():
			if row[col_num] != 0:
				original_service_id = row['Chains']
				morse_chain_id = extract_morse_chain_id(original_service_id)
				
				node_type = row['Node Type']
				
				# Use Shannon service ID if mapping exists, otherwise use original
				service_id = service_mapping.get(morse_chain_id, None)
				
				if service_id is None:
					print(f"Morse to Shannon service mapping is missing for {morse_chain_id}: Linked Operator Address: {wallet_info['operator_address']}")
					continue
				service = {
					'service_id': service_id,
					'endpoints': [{
						'publicly_exposed_url': wallet_info['publicly_exposed_url'],
						'rpc_type': 'JSON_RPC'  # Default
					}]
				}
				
				# Set revenue share based on node type
				if node_type == 'HTC':
					pass
				else:  # LTailC
					service['rev_share_percent'] = {
						wallet_info['revshare_address']: 100
					}
				
				yaml_data['services'].append(service)
		
		# Write YAML file for this customer
		output_file = os.path.join('output', f'{customer_id}.yml')
		with open(output_file, 'w') as f:
			yaml.dump(yaml_data, f, sort_keys=False, default_flow_style=False)
		print(f"Generated {output_file}")

if __name__ == "__main__":
	main()