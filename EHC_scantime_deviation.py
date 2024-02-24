import argparse
import json
import csv
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil import parser # pip install python-dateutil
import re

def parse_time_to_seconds(time_str):
    # Regular expression to find hours, minutes, and seconds
    time_re = re.compile(r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?')
    match = time_re.match(time_str)
    if not match:
        return None

    hours, minutes, seconds = match.groups()
    total_seconds = 0

    if hours:
        total_seconds += int(hours) * 3600
    if minutes:
        total_seconds += int(minutes) * 60
    if seconds:
        total_seconds += int(seconds)

    return total_seconds

def parse_date(date_string):
    if date_string is None:
        return None
    try:
        return parser.parse(date_string)
    except ValueError:
        return None

def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    result = ''
    if hours:
        result += f"{hours}h"
    if minutes:
        result += f"{minutes}m"
    if seconds:
        result += f"{seconds}s"
    return result

def find_deviations(scan_data, min_deviation_time_seconds, deviation_percentage, include_incremental):
    project_scan_data = defaultdict(lambda: {'Incremental': [], 'Full': []})
    unique_project_ids = set()

    for scan in scan_data['value']:
        project_id = scan.get('ProjectId', None)
        if project_id is not None:
            unique_project_ids.add(project_id)
        start_time = parse_date(scan.get('EngineStartedOn'))
        end_time = parse_date(scan.get('EngineFinishedOn'))
        loc = scan.get('LOC', "N/A")  # Get LOC
        engine_server_id = scan.get('EngineServerId', "N/A")  # Get EngineServerId
        total_vulnerabilities = scan.get('TotalVulnerabilities', "N/A")  # Get TotalVulnerabilities

        if start_time and end_time:
            scan_duration = int((end_time - start_time).total_seconds())
        else:
            continue

        scan_type = 'Incremental' if scan['IsIncremental'] else 'Full'
        project_scan_data[scan['ProjectName']][scan_type].append((scan['Id'], scan_duration, loc, engine_server_id, total_vulnerabilities))

    deviations = []
    
    for project_name, scan_types in project_scan_data.items():        
        for scan_type, scan_list in scan_types.items():
            if not include_incremental and scan_type == 'Incremental':
                continue  # Skip incremental scans if not included

            if len(scan_list) < 2:  # Skip if there are not enough scans to compare
                continue

            min_scan = min(scan_list, key=lambda x: x[1])
            max_scan = max(scan_list, key=lambda x: x[1])

            if max_scan[1] == min_scan[1]:
                continue

            if min_scan[1] != 0:
                percentage_difference = ((max_scan[1] - min_scan[1]) / min_scan[1]) * 100
            else:
                continue

            if max_scan[1] - min_scan[1] >= min_deviation_time_seconds and \
               percentage_difference >= deviation_percentage:

                deviations.append({
                    'ProjectName': project_name,
                    'MinDuration': str(timedelta(seconds=min_scan[1])),
                    'MaxDuration': str(timedelta(seconds=max_scan[1])),
                    'MinScanLOC': min_scan[2],  # Include Min Scan LOC
                    'MaxScanLOC': max_scan[2],  # Include Max Scan LOC
                    'MinEngineServerId': min_scan[3],  # Include Min EngineServerId
                    'MaxEngineServerId': max_scan[3],  # Include Max EngineServerId
                    'MinTotalVulnerabilities': min_scan[4],  # Include Min Scan TotalVulnerabilities
                    'MaxTotalVulnerabilities': max_scan[4],  # Include Max Scan TotalVulnerabilities
                    'PercentageDifference': int(percentage_difference),
                    'MinScanID': min_scan[0],
                    'MaxScanID': max_scan[0],
                    'ScanType': scan_type
                })

    return deviations, len(unique_project_ids)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Find deviations in scan times.')
    parser.add_argument('json_file', type=str, help='JSON file containing scan data.')
    parser.add_argument('--min-deviation-percentage', type=int, default=500, help='Deviation percentage threshold.')
    parser.add_argument('--min-deviation-time', type=str, default='5m', help='Minimum deviation time.')
    parser.add_argument('--csv-export', action='store_true', help='Export to CSV.')
    parser.add_argument('--incremental', action='store_true', help='Include incremental scans.')

    args = parser.parse_args()

    min_deviation_time_seconds = parse_time_to_seconds(args.min_deviation_time)
    if min_deviation_time_seconds is None:
        print("Invalid time format for --min-deviation-time")
        return

    with open(args.json_file, 'r') as f:
        scan_data = json.load(f)

    deviations, total_projects = find_deviations(scan_data, min_deviation_time_seconds, args.min_deviation_percentage, args.incremental)

    if args.csv_export:
        original_name = args.json_file.rsplit('.', 1)[0]
        csv_file_name = f"{original_name}-scantime_deviation.csv"
        if deviations:
            with open(csv_file_name, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=deviations[0].keys())
                writer.writeheader()
                writer.writerows(deviations)
            print(f"CSV exported to {csv_file_name}")
        else:
            print("No deviations found.")
    else:
        if not deviations:
            print("No deviations found.")
            return
            
        # Sort deviations by 'PercentageDifference' from smallest to largest
        sorted_deviations = sorted(deviations, key=lambda x: x['PercentageDifference'])

        for deviation in sorted_deviations:
            print(f"• Project: {deviation['ProjectName']}\n  - Min Scan ID: {deviation['MinScanID']} [Duration: {deviation['MinDuration']}, LOC: {deviation['MinScanLOC']}, EngineServerId: {deviation['MinEngineServerId']}, Total Vulnerabilities: {deviation['MinTotalVulnerabilities']}]\n  - Max Scan ID: {deviation['MaxScanID']} [Duration: {deviation['MaxDuration']}, LOC: {deviation['MaxScanLOC']}, EngineServerId: {deviation['MaxEngineServerId']}, Total Vulnerabilities: {deviation['MaxTotalVulnerabilities']}]\n  - % Delta: {deviation['PercentageDifference']}%\n  - Scan Type: {deviation['ScanType']}\n")

    print(f"{len(deviations)} deviations in {total_projects} projects using minimum deviation time of {args.min_deviation_time} and minimum deviation percentage of {args.min_deviation_percentage}%\n")
