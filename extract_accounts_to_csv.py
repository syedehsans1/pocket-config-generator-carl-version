import json
import csv
from typing import List, Dict

def read_json_file(file_path: str) -> Dict:
    """Read and parse the JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def extract_account_data(data: Dict) -> List[Dict]:
    """Extract required fields from the JSON data."""
    extracted_data = []
    
    for mapping in data.get('mappings', []):
        if 'shannon' in mapping and 'migration_msg' in mapping:
            account_data = {
                'shannon_address': mapping['shannon']['address'],
                'shannon_private_key': mapping['shannon']['private_key'],
                'morse_node_address': mapping['migration_msg']['morse_node_address']
            }
            extracted_data.append(account_data)
    
    return extracted_data

def write_to_csv(data: List[Dict], output_file: str):
    """Write the extracted data to a CSV file."""
    if not data:
        print("No data to write to CSV")
        return

    fieldnames = ['shannon_address', 'shannon_private_key', 'morse_node_address']
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    input_file = input("Enter JSON File name of migration exported customer accounts: ")
    output_file = 'extracted_accounts.csv'
    
    try:
        # Read JSON data
        json_data = read_json_file(input_file)
        
        # Extract required fields
        account_data = extract_account_data(json_data)
        
        # Write to CSV
        write_to_csv(account_data, output_file)
        print(f"Successfully wrote data to {output_file}")
        
    except FileNotFoundError:
        print(f"Error: Could not find input file {input_file}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {input_file}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 