import json
import argparse

def combine_scans(file_paths):
    combined_scans = []
    metadata = None
    
    for i, file_path in enumerate(file_paths):
        with open(file_path, 'r') as file:
            data = json.load(file)
            if i == 0:
                # Capture the metadata from the first file
                metadata = data.get("@odata.context", None)
            combined_scans.extend(data["value"])  # Combine the "value" arrays
            
    return metadata, combined_scans

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Combine multiple JSON files into one.')
    parser.add_argument('input_files', nargs='+', type=str, help='Input JSON files with scan data.')
    parser.add_argument('output_file', type=str, help='Output JSON file to write combined data.')
    args = parser.parse_args()

    # Combine the scans from the input files
    metadata, combined_scans = combine_scans(args.input_files)

    # Output the combined data to a file
    with open(args.output_file, 'w') as output_file:
        # Write the metadata and combined scans
        json.dump({
            "@odata.context": metadata,
            "value": combined_scans
        }, output_file, indent=4)
    
    print(f"Combined output written to {args.output_file}")
