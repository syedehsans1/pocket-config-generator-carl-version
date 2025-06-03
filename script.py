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

def get_service_details(owner_address):
	"""Get service details from owner-specific CSV file if it exists."""
	details_file = f"{owner_address}.csv"
	if os.path.exists(details_file):
		try:
			details_df = pd.read_csv(details_file)
			# Create a dictionary mapping service_id to its details
			return {row['service_id']: {
				'publicly_exposed_url': row['publicly_exposed_url'],
				'rpc_type': row['rpc_type'],
				'operator_address': row['operator_address']
			} for _, row in details_df.iterrows()}
		except Exception as e:
			print(f"Warning: Error reading {details_file}: {e}")
	return {}

def extract_morse_chain_id(service_id):
	"""Extract Morse Chain ID from service ID string (e.g., 'Avalanche (F003)' -> 'F003')."""
	import re
	match = re.search(r'\(([A-F0-9]{4})\)', service_id)
	return match.group(1) if match else None

def main():
	# Create output directory if it doesn't exist
	os.makedirs('output', exist_ok=True)
	
	# Load service ID mapping
	service_mapping = load_service_mapping()
	if not service_mapping:
		print("Warning: Could not load service mapping. Using original service IDs.")
	
	df = pd.read_csv('NodeAllocation.csv')
 
	# drop last column from df
	df = df.iloc[:, :-1]
	# drop last row from df
	df = df.iloc[:-1, :]
	# replace all NaN with 0
	df = df.fillna(0)
	
	# Iterate over each owner address (columns 4 onwards)
	for owner_address in df.columns[3:]:
		# Get service details from owner-specific CSV if available
		service_details = get_service_details(owner_address)
		
		# Create base YAML structure for this owner
		yaml_data = {
			'owner_address': owner_address,
			'operator_address': f"{owner_address}_operator",  # Default, will be overridden if in details
			'stake_amount': '1000000upokt',
			'default_rev_share_percent': {
				owner_address: 50,
				f"{owner_address}_operator": 50
			},
			'services': []
		}
		
		# Add services for this owner
		for index, row in df.iterrows():
			if row[owner_address] != 0:
				original_service_id = row[0]
				morse_chain_id = extract_morse_chain_id(original_service_id)
				
				# Use Shannon service ID if mapping exists, otherwise use original
				service_id = service_mapping.get(morse_chain_id, original_service_id)
				
				service = {
					'service_id': service_id,
					'endpoints': [{
						'publicly_exposed_url': 'https://relayminer.example.com',  # Default
						'rpc_type': 'JSON_RPC'  # Default
					}]
				}
				
				# Update service details if available from CSV
				if original_service_id in service_details:
					details = service_details[original_service_id]
					service['endpoints'][0].update({
						'publicly_exposed_url': details['publicly_exposed_url'],
						'rpc_type': details['rpc_type']
					})
					# Update operator address if available
					if 'operator_address' in details:
						yaml_data['operator_address'] = details['operator_address']
    
				if row[1] != 'HTC':
					service['rev_share_percent'] = {
						owner_address: 0,
						f"{owner_address}_operator": 100
					}
				
				yaml_data['services'].append(service)
		
		# Write YAML file for this owner
		output_file = os.path.join('output', f'{owner_address}.yml')
		with open(output_file, 'w') as f:
			yaml.dump(yaml_data, f, sort_keys=False, default_flow_style=False)
		print(f"Generated {output_file}")

if __name__ == "__main__":
	main()