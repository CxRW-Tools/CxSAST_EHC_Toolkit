import json
import argparse
import datetime
import os

def parse_date(date_string):
    formats = [
        '%Y-%m-%dT%H:%M:%S.%fZ',           # Format with 'Z' at the end with milliseconds
        '%Y-%m-%dT%H:%M:%S.%f%z',          # Format with timezone offset with milliseconds
        '%Y-%m-%dT%H:%M:%SZ',              # Format with 'Z' at the end without milliseconds
        '%Y-%m-%dT%H:%M:%S%z'              # Format with timezone offset without milliseconds
    ]

    for date_format in formats:
        try:
            return datetime.datetime.strptime(date_string, date_format).date()
        except ValueError:
            continue

    raise ValueError(f"Unknown date format for string {date_string}")

def split_scans(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        all_scans = data["value"]
        
        start_date = parse_date(all_scans[0]['ScanRequestedOn'])
        end_date_1 = start_date + datetime.timedelta(days=30)
        end_date_2 = end_date_1 + datetime.timedelta(days=30)

        part1 = []
        part2 = []
        part3 = []

        for scan in all_scans:
            current_date = parse_date(scan['ScanRequestedOn'])
            if current_date < end_date_1:
                part1.append(scan)
            elif current_date < end_date_2:
                part2.append(scan)
            else:
                part3.append(scan)

    return part1, part2, part3

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Split scans into three parts based on dates.')
    parser.add_argument('input_file', type=str, help='Input JSON file with scan data.')
    args = parser.parse_args()

    # Split the scans into three parts based on date
    part1, part2, part3 = split_scans(args.input_file)

    # Generate filenames
    base_path, filename = os.path.split(args.input_file)
    base_filename, _ = os.path.splitext(filename)
    output_filename1 = os.path.join(base_path, f"{base_filename}-part1.json")
    output_filename2 = os.path.join(base_path, f"{base_filename}-part2.json")
    output_filename3 = os.path.join(base_path, f"{base_filename}-part3.json")

    # Output the split data to files
    with open(output_filename1, 'w') as file:
        json.dump({"value": part1}, file)
    with open(output_filename2, 'w') as file:
        json.dump({"value": part2}, file)
    with open(output_filename3, 'w') as file:
        json.dump({"value": part3}, file)

    print(f"Output written to:\n{output_filename1}\n{output_filename2}\n{output_filename3}")
