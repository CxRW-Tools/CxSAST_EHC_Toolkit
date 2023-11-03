import ijson
import sys
import json
import argparse

def filter_scans(input_file, project_name):
    """
    Reads the JSON file and filters scans based on the given project name.
    """
    filtered_scans = []

    with open(input_file, 'rb') as f:
        scans = ijson.items(f, 'value.item')

        for scan in scans:
            if scan.get('ProjectName') == project_name:
                filtered_scans.append(scan)

    return filtered_scans

if __name__ == "__main__":
    # Command line argument parsing
    parser = argparse.ArgumentParser(description="Filter scans by project name.")
    parser.add_argument("input_file", help="Path to the input JSON file containing scan data.")
    parser.add_argument("--filter-project", required=True, help="Project name to filter the scans by.")
    
    args = parser.parse_args()

    # Filter scans
    filtered_data = filter_scans(args.input_file, args.filter_project)

    output_file = f"filtered-{args.filter_project}-{args.input_file}"
    with open(args.input_file, 'r') as in_f, open(output_file, 'w') as out_f:
        # Read the original file content
        json_content = json.load(in_f)
        
        # Replace the 'value' key with the filtered data
        json_content["value"] = filtered_data

        # Dump the updated structure to the output file
        json.dump(json_content, out_f, indent=4)

    print(f"Filtered data written to: {output_file}")
