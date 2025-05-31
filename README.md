# POKT Node Allocation YAML Generator

This script generates YAML configuration files for POKT node allocations based on CSV input files. It processes a main allocation CSV file and optional service detail CSV files to create properly formatted YAML configurations for each node owner.

## File Structure

### 1. Main Allocation CSV (`NodeAllocation.csv`)

The main CSV file should have the following structure:
- First 3 columns: Service ID, Node Type, Stake Nodes
- Remaining columns: Owner addresses (column headers should be the owner addresses)
- Values in the matrix: Number of nodes allocated (0 means no allocation)

Example:
```csv
service_id,node_type,stake_nodes,1,2,3
Avalanche (F003),HTC,1,1,0,1
Avalanche-DFK (F004),HTC,1,0,1,1
```

### 2. Service Detail CSV Files (Optional)

For each owner address, you can provide a CSV file named `{owner_address}.csv` (e.g., `1.csv`) with specific service details:

Required columns:
- `service_id`: Must match the service_id from the main allocation CSV
- `publicly_exposed_url`: The public URL for the service
- `rpc_type`: The RPC type (e.g., "JSON_RPC")
- `operator_address`: The operator address for this service

Example (`1.csv`):
```csv
service_id,publicly_exposed_url,rpc_type,operator_address
Avalanche (F003),https://relayminer1.example.com,JSON_RPC,1_operator_test
Avalanche-DFK (F004),https://relayminer2.example.com,JSON_RPC,1_operator_test
```

## Output

The script generates YAML files in the `output` directory, one for each owner address. Each YAML file follows this structure:

```yaml
owner_address: "1"
operator_address: "1_operator_test"  # From CSV if available, otherwise default
stake_amount: "1000000upokt"
default_rev_share_percent:
  "1": 50
  "1_operator": 50
services:
  - service_id: "Avalanche (F003)"
    endpoints:
      - publicly_exposed_url: "https://relayminer1.example.com"  # From CSV if available
        rpc_type: "JSON_RPC"  # From CSV if available
    # rev_share_percent will be added for non-HTC nodes
```

## Requirements

- Python 3.x
- Required packages:
  - pandas
  - pyyaml

Install dependencies:
```bash
pip install pandas pyyaml
```

## Usage

1. Prepare your CSV files:
   - Create `NodeAllocation.csv` with the main allocation matrix
   - Optionally create service detail CSV files for each owner (e.g., `1.csv`, `2.csv`, etc.)

2. Run the script:
```bash
python script.py
```

3. Check the `output` directory for generated YAML files

## Notes

- If a service detail CSV file is not provided for an owner, default values will be used
- For non-HTC node types, a custom rev_share_percent will be set (0% owner, 100% operator)
- The script will create an `output` directory if it doesn't exist
- Any errors reading service detail CSV files will be reported but won't stop the script 