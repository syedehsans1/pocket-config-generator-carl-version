import os
import sys
import pandas as pd
import yaml
import requests
import time

def load_service_mapping():
	"""Load the Morse to Shannon service ID mapping."""
	try:
		mapping_df = pd.read_csv('morse_to_shannon_service_mapping.csv')
		# Create a dictionary mapping Morse Chain IDs to Shannon Service IDs
		return dict(zip(mapping_df['Morse_Chain_Id'], mapping_df['Shannon_Service_id']))
	except Exception as e:
		print(f"Error loading service mapping: {e}")
		return {}

def fetch_supplier_info(operator_address):
	network = os.getenv('NETWORK')
	"""Fetch supplier information from the API using operator address."""
	base_url = f"https://shannon-testnet-grove-api.{network}.poktroll.com/pokt-network/poktroll/supplier/supplier"
	url = f"{base_url}/{operator_address}"
	
	try:
		response = requests.get(url, timeout=30)
		response.raise_for_status()
		data = response.json()
		
		if 'supplier' not in data:
			print(f"Error: No supplier data found for operator {operator_address}")
			return None
		
		supplier = data['supplier']
		
		# Extract revshare addresses from services
		revshare_addresses = set()
		for service in supplier.get('services', []):
			for rev_share in service.get('rev_share', []):
				revshare_addresses.add(rev_share['address'])
		
		# Remove owner_address from revshare_addresses if present
		revshare_addresses.discard(supplier['owner_address'])
		revshare_addresses.discard(supplier['operator_address'])
		
		# Get the first revshare address (or use a default if none found)
		revshare_address = list(revshare_addresses)[0] if revshare_addresses else supplier['owner_address']
		
		# Extract existing services data
		existing_services = []
		for service in supplier.get('services', []):
			service_data = {
				'service_id': service['service_id'],
				'endpoints': []
			}
			
			# Add endpoints
			for endpoint in service.get('endpoints', []):
				endpoint_data = {
					'publicly_exposed_url': endpoint.get('url', 'https://relayminer.example.com'),
					'rpc_type': endpoint.get('rpc_type', 'JSON_RPC')
				}
				if endpoint.get('configs'):
					endpoint_data['configs'] = endpoint['configs']
				service_data['endpoints'].append(endpoint_data)
			
			# Add revenue sharing if present
			if service.get('rev_share'):
				rev_share_percent = {}
				for rev_share in service['rev_share']:
					rev_share_percent[rev_share['address']] = int(rev_share['rev_share_percentage'])
				service_data['rev_share_percent'] = rev_share_percent
			
			existing_services.append(service_data)
		
		return {
			'operator_address': supplier['operator_address'],
			'owner_address': supplier['owner_address'],
			'stake_amount': int(supplier['stake']['amount']) // 1000000,  # Convert from upokt to pokt
			'revshare_address': revshare_address,
			'publicly_exposed_url': 'https://relayminer.example.com',  # Default URL
			'existing_services': existing_services
		}
		
	except requests.exceptions.RequestException as e:
		print(f"Error fetching supplier info for {operator_address}: {e}")
		return None
	except Exception as e:
		print(f"Error processing supplier data for {operator_address}: {e}")
		return None

def load_operator_addresses():
	"""Load operator addresses from CSV file."""
	try:
		filename = input("Enter the CSV filename with operator_address column (Case-sensitive): ")
		df = pd.read_csv(filename)
		
		if 'operator_address' not in df.columns:
			print("Error: CSV file must contain 'operator_address' column")
			return {}
		
		wallet_data = {}
		for index, row in df.iterrows():
			operator_address = row['operator_address']
			print(f"Fetching supplier info for operator: {operator_address}")
			
			supplier_info = fetch_supplier_info(operator_address)
			if supplier_info:
				# Use operator address as customer_id for consistency
				customer_id = f"customer_{index + 1}"
				wallet_data[customer_id] = supplier_info
				print(f"Successfully fetched info for {operator_address}")
			else:
				print(f"Failed to fetch info for {operator_address}, skipping...")
			
			# Add a small delay to avoid overwhelming the API
			time.sleep(0.5)
		
		return wallet_data
		
	except Exception as e:
		print(f"Error loading operator addresses: {e}")
		return {}

def extract_morse_chain_id(service_id):
	"""Extract Morse Chain ID from service ID string (e.g., 'Avalanche (F003)' -> 'F003')."""
	import re
	match = re.search(r'\(([A-F0-9]{4})\)', service_id)
	return match.group(1) if match else None

def main():
	# Create output directory if it doesn't exist
	os.makedirs('output', exist_ok=True)
	
	# Load service ID mapping and operator addresses
	service_mapping = load_service_mapping()
	wallet_data = load_operator_addresses()
	
	if not service_mapping:
		print("Warning: Could not load service mapping. Using original service IDs.")
	if not wallet_data:
		print("Error: Could not load wallet data. Exiting.")
		sys.exit(1)
	
	# Read NodeAllocation.csv
	filename = input("Enter the csv received from PNF with the F-Chains node allocations (Case-sensitive): ")
	revshare_pct = int(input("Enter revshare percentage for the REVSHARE ADDRESS:"))
	
	df = pd.read_csv(filename)
 
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
			'stake_amount': f"{int(wallet_info['stake_amount']) * 1000000}upokt",
			'default_rev_share_percent': {
				wallet_info['owner_address']: 0 if revshare_pct == 100 else (99 - revshare_pct),
				wallet_info['revshare_address']: revshare_pct,
				wallet_info['operator_address']: 0 if revshare_pct == 100 else 1
			},
			'services': []
		}
		
		# Add existing services from API response
		if 'existing_services' in wallet_info:
			yaml_data['services'].extend(wallet_info['existing_services'])
		
		# Add new services for this customer from node allocation
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
				
				# Check if this service already exists in the services list
				service_exists = any(service['service_id'] == service_id for service in yaml_data['services'])
				
				if not service_exists:
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