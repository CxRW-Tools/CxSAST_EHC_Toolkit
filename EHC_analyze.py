import argparse
import os
import ijson
import sys
from datetime import datetime
from dateutil.parser import parse as parse_date
import time
import math
import pprint

try:
    from tqdm import tqdm
    tqdm_available = True
except ImportError:
    tqdm_available = False
    print("Consider installing tqdm for progress bar: 'pip install tqdm'")



def ingest_file(file_path):
    print("Reading data file...", end="", flush=True)
    scans = []
    with open(file_path, 'rb') as file:
        for scan in ijson.items(file, 'value.item'):
            scans.append(scan)
    print("completed!")
    return scans



def calculate_time_difference(t1, t2):
    dt1 = parse_date(t1)
    dt2 = parse_date(t2)
    time_diff = (dt2 - dt1).total_seconds()
    
    return time_diff



# One single function will be more efficient but start to get messy. Brace youreself.
def process_scans(scans):

    # define (most) variables and data structures

    # date range of data
    first_date = datetime.max.date()
    last_date = datetime.min.date()

    # general scan stats
    sum_scan_count = yes_scan_count = no_scan_count = 0
    scan_stats_by_date = {}
    scanned_projects = {}

    # results info
    results = {
        "total_vulns__sum": 0, "high__sum": 0, "medium__sum": 0, "low__sum": 0, "info__sum": 0, 
        "total_vulns__max": 0, "high__max": 0, "medium__max": 0, "low__max": 0, "info__max": 0, 
        "total_vulns__avg": 0, "high__avg": 0, "medium__avg": 0, "low__avg": 0, "info__avg": 0,
        "high_results__scan_count": 0, "medium_results__scan_count": 0, "low_results__scan_count": 0, "info_results__scan_count": 0, "zero_results__scan_count": 0}

    # presets
    preset_names = {}
    
    # languages
    scanned_languages = {}

    # scan origins
    origins = {}
    printable_origins = {
        "ADO": "ADO",
        "Bamboo": "Bamboo",
        "CLI": "CLI",
        "cx-CLI": "cx-CLI",
        "CxFlow": "CxFlow",
        "Eclipse": "Eclipse",
        "cx-intellij": "IntelliJ",
        "Jenkins": "Jenkins",
        "Manual": "Manual",
        "Maven": "Maven",
        "Other": "Other",
        "System": "Scheduled",
        "TeamCity": "TeamCity",
        "TFS": "TFS",
        "Visual Studio": "Visual Studio",
        "Visual-Studio-Code": "Visual Studio Code",
        "VSTS": "VSTS",
        "Web Portal": "Web Portal",
        "MISSING ORIGIN TYPE": "Missing Origin Type"
    }
    grouped_origins = {value: 0 for value in printable_origins.values()}

    # bins to track scan info based on LOC range (count and various time data)
    size_bins = {
        '0 to 20k': {"yes_scan_count": 0, "no_scan_count": 0, "total_scan_time__sum": 0, "source_pulling_time__sum": 0, "queue_time__sum": 0,
        "engine_scan_time__sum": 0, "total_scan_time__max": 0, "source_pulling_time__max": 0, "queue_time__max": 0, "engine_scan_time__max": 0,
        "total_scan_time__avg": 0, "source_pulling_time__avg": 0, "queue_time__avg": 0, "engine_scan_time__avg": 0},
        '20k-50k': {"yes_scan_count": 0, "no_scan_count": 0, "total_scan_time__sum": 0, "source_pulling_time__sum": 0, "queue_time__sum": 0,
        "engine_scan_time__sum": 0, "total_scan_time__max": 0, "source_pulling_time__max": 0, "queue_time__max": 0, "engine_scan_time__max": 0,
        "total_scan_time__avg": 0, "source_pulling_time__avg": 0, "queue_time__avg": 0, "engine_scan_time__avg": 0},
        '50k-100k': {"yes_scan_count": 0, "no_scan_count": 0, "total_scan_time__sum": 0, "source_pulling_time__sum": 0, "queue_time__sum": 0,
        "engine_scan_time__sum": 0, "total_scan_time__max": 0, "source_pulling_time__max": 0, "queue_time__max": 0, "engine_scan_time__max": 0,
        "total_scan_time__avg": 0, "source_pulling_time__avg": 0, "queue_time__avg": 0, "engine_scan_time__avg": 0},
        '100k-250k': {"yes_scan_count": 0, "no_scan_count": 0, "total_scan_time__sum": 0, "source_pulling_time__sum": 0, "queue_time__sum": 0,
        "engine_scan_time__sum": 0, "total_scan_time__max": 0, "source_pulling_time__max": 0, "queue_time__max": 0, "engine_scan_time__max": 0,
        "total_scan_time__avg": 0, "source_pulling_time__avg": 0, "queue_time__avg": 0, "engine_scan_time__avg": 0},
        '250k-500k': {"yes_scan_count": 0, "no_scan_count": 0, "total_scan_time__sum": 0, "source_pulling_time__sum": 0, "queue_time__sum": 0,
        "engine_scan_time__sum": 0, "total_scan_time__max": 0, "source_pulling_time__max": 0, "queue_time__max": 0, "engine_scan_time__max": 0,
        "total_scan_time__avg": 0, "source_pulling_time__avg": 0, "queue_time__avg": 0, "engine_scan_time__avg": 0},
        '500k-1M': {"yes_scan_count": 0, "no_scan_count": 0, "total_scan_time__sum": 0, "source_pulling_time__sum": 0, "queue_time__sum": 0,
        "engine_scan_time__sum": 0, "total_scan_time__max": 0, "source_pulling_time__max": 0, "queue_time__max": 0, "engine_scan_time__max": 0,
        "total_scan_time__avg": 0, "source_pulling_time__avg": 0, "queue_time__avg": 0, "engine_scan_time__avg": 0},
        '1M-2M': {"yes_scan_count": 0, "no_scan_count": 0, "total_scan_time__sum": 0, "source_pulling_time__sum": 0, "queue_time__sum": 0,
        "engine_scan_time__sum": 0, "total_scan_time__max": 0, "source_pulling_time__max": 0, "queue_time__max": 0, "engine_scan_time__max": 0,
        "total_scan_time__avg": 0, "source_pulling_time__avg": 0, "queue_time__avg": 0, "engine_scan_time__avg": 0},
        '2M-3M': {"yes_scan_count": 0, "no_scan_count": 0, "total_scan_time__sum": 0, "source_pulling_time__sum": 0, "queue_time__sum": 0,
        "engine_scan_time__sum": 0, "total_scan_time__max": 0, "source_pulling_time__max": 0, "queue_time__max": 0, "engine_scan_time__max": 0,
        "total_scan_time__avg": 0, "source_pulling_time__avg": 0, "queue_time__avg": 0, "engine_scan_time__avg": 0},
        '3M-5M': {"yes_scan_count": 0, "no_scan_count": 0, "total_scan_time__sum": 0, "source_pulling_time__sum": 0, "queue_time__sum": 0,
        "engine_scan_time__sum": 0, "total_scan_time__max": 0, "source_pulling_time__max": 0, "queue_time__max": 0, "engine_scan_time__max": 0,
        "total_scan_time__avg": 0, "source_pulling_time__avg": 0, "queue_time__avg": 0, "engine_scan_time__avg": 0},
        '5M-7M': {"yes_scan_count": 0, "no_scan_count": 0, "total_scan_time__sum": 0, "source_pulling_time__sum": 0, "queue_time__sum": 0,
        "engine_scan_time__sum": 0, "total_scan_time__max": 0, "source_pulling_time__max": 0, "queue_time__max": 0, "engine_scan_time__max": 0,
        "total_scan_time__avg": 0, "source_pulling_time__avg": 0, "queue_time__avg": 0, "engine_scan_time__avg": 0},
        '7M-10M': {"yes_scan_count": 0, "no_scan_count": 0, "total_scan_time__sum": 0, "source_pulling_time__sum": 0, "queue_time__sum": 0,
        "engine_scan_time__sum": 0, "total_scan_time__max": 0, "source_pulling_time__max": 0, "queue_time__max": 0, "engine_scan_time__max": 0,
        "total_scan_time__avg": 0, "source_pulling_time__avg": 0, "queue_time__avg": 0, "engine_scan_time__avg": 0},
        '10M+':  {"yes_scan_count": 0, "no_scan_count": 0, "total_scan_time__sum": 0, "source_pulling_time__sum": 0, "queue_time__sum": 0,
        "engine_scan_time__sum": 0, "total_scan_time__max": 0, "source_pulling_time__max": 0, "queue_time__max": 0, "engine_scan_time__max": 0,
        "total_scan_time__avg": 0, "source_pulling_time__avg": 0, "queue_time__avg": 0, "engine_scan_time__avg": 0}
    }

    # Initialize tqdm object
    if tqdm_available:
        pbar = tqdm(total=len(scans), desc="Processing scans")
    else:
        print("Processing scans...", end="", flush=True)

    # process all the things
    for scan in scans:
        if tqdm_available:
            pbar.update(1)
        
        # if there is no LOC value, we might as well just completely skip the scan
        loc = scan.get('LOC', None)
        if loc is None:
            continue

        # update the date range
        scan_date_str = scan.get('ScanRequestedOn', '').split('T')[0]
        scan_date = datetime.strptime(scan_date_str, "%Y-%m-%d").date()
        first_date = min(first_date, scan_date)
        last_date = max(last_date, scan_date)

        # determine the correct bin key
        if loc <= 20000:
            bin_key = '0 to 20k'
        elif loc <= 50000:
            bin_key = '20k-50k'
        elif loc <= 100000:
            bin_key = '50k-100k'
        elif loc <= 250000:
            bin_key = '100k-250k'
        elif loc <= 500000:
            bin_key = '250k-500k'
        elif loc <= 1000000:
            bin_key = '500k-1M'
        elif loc <= 2000000:
            bin_key = '1M-2M'
        elif loc <= 3000000:
            bin_key = '2M-3M'
        elif loc <= 5000000:
            bin_key = '3M-5M'
        elif loc <= 7000000:
            bin_key = '5M-7M'
        elif loc <= 10000000:
            bin_key = '7M-10M'
        else:
            bin_key = '10M+'

        # general stats + bin metrics; only update engine time if there was actually a scan
        if scan_date not in scan_stats_by_date:
            scan_stats_by_date[scan_date] = {
                'total_scan_count': 0,
                'yes_scan_count': 0,
                'no_scan_count': 0,
                'full_scan_count': 0,
                'incremental_scan_count': 0,
                'loc__sum': 0,
                'loc__max': 0,
                'failed_loc__sum': 0,
                'failed_loc__max': 0
            }

        scan_stats_by_date[scan_date]['total_scan_count'] += 1
        scan_stats_by_date[scan_date]['loc__sum'] += loc
        scan_stats_by_date[scan_date]['loc__max'] = max(loc, scan_stats_by_date[scan_date]['loc__max'])
        scan_stats_by_date[scan_date]['failed_loc__sum'] += scan.get('FailedLOC', 0)
        scan_stats_by_date[scan_date]['failed_loc__max'] = max(scan.get('FailedLOC', 0), scan_stats_by_date[scan_date]['failed_loc__max'])
        
        if scan.get('IsIncremental', None):
            scan_stats_by_date[scan_date]['incremental_scan_count'] += 1
        else:
            scan_stats_by_date[scan_date]['full_scan_count'] += 1
        
        project_id = scan.get('ProjectId', 0)
        if project_id not in scanned_projects:
            scanned_projects[project_id] = {
                'project_name': scan.get('ProjectName', ""),
                'project_scan_count': 0,
                'total_vulns_count': 0,
                'high_count': 0,
                'medium_count': 0,
                'low_count': 0,
                'info_count': 0,
            }
        
        scanned_projects[project_id]['project_scan_count'] += 1
        scanned_projects[project_id]['total_vulns_count'] = scan.get('TotalVulnerabilities', 0)
        scanned_projects[project_id]['high_count'] = scan.get('High', 0)
        scanned_projects[project_id]['medium_count'] = scan.get('Medium', 0)
        scanned_projects[project_id]['low_count'] = scan.get('Low', 0)
        scanned_projects[project_id]['info_count'] = scan.get('Info', 0)

        source_pulling_time = math.ceil(calculate_time_difference(scan.get('ScanRequestedOn'),scan.get('QueuedOn')))
        queue_time = math.ceil(calculate_time_difference(scan.get('QueuedOn'),scan.get('EngineStartedOn')))
        total_scan_time = math.ceil(calculate_time_difference(scan.get('ScanRequestedOn'),scan.get('ScanCompletedOn')))

        bin = size_bins[bin_key]

        bin['source_pulling_time__sum'] += source_pulling_time
        bin['queue_time__sum'] += queue_time
        bin['total_scan_time__sum'] += total_scan_time
        bin['source_pulling_time__max'] = max(source_pulling_time, bin['source_pulling_time__max'])
        bin['queue_time__max'] = max(queue_time, bin['queue_time__max'])
        bin['total_scan_time__max'] = max(total_scan_time, bin['total_scan_time__max'])

        if scan.get('EngineFinishedOn', None) is not None:
            engine_scan_time = math.ceil(calculate_time_difference(scan.get('EngineStartedOn'),scan.get('EngineFinishedOn')))
            yes_scan_count += 1
            scan_stats_by_date[scan_date]['yes_scan_count'] += 1
            bin['yes_scan_count'] += 1
            bin['engine_scan_time__sum'] += engine_scan_time
            bin['engine_scan_time__max'] = max(engine_scan_time, bin['engine_scan_time__max'])
        else:
            no_scan_count +=1
            scan_stats_by_date[scan_date]['no_scan_count'] += 1
            bin['no_scan_count'] += 1

        # results info
        results['total_vulns__sum'] += scan.get('TotalVulnerabilities', 0)
        results['high__sum'] += scan.get('High', 0)
        results['medium__sum'] += scan.get('Medium', 0)
        results['low__sum'] += scan.get('Low', 0)
        results['info__sum'] += scan.get('Info', 0)
        results['total_vulns__max'] = max(results['total_vulns__max'], scan.get('TotalVulnerabilities', 0))
        results['high__max'] = max(results['high__max'], scan.get('High', 0))
        results['medium__max'] = max(results['medium__max'], scan.get('Medium', 0))
        results['low__max'] = max(results['low__max'], scan.get('Low', 0))
        results['info__max'] = max(results['info__max'], scan.get('Info', 0))
        if scan.get('High', 0) > 0:
            results['high_results__scan_count'] += 1
        if scan.get('Medium', 0) > 0:
            results['medium_results__scan_count'] += 1
        if scan.get('Low', 0) > 0:
            results['low_results__scan_count'] += 1
        if scan.get('Info', 0) > 0:
            results['info_results__scan_count'] += 1
        if scan.get('TotalVulnerabilities', 0) == 0:
            results['zero_results__scan_count'] += 1
        
        # presets
        preset_name = scan.get('PresetName')
        preset_names[preset_name] = preset_names.get(preset_name, 0) + 1
        
        # languages
        for language in scan.get('ScannedLanguages', []):
            lang_name = language.get('LanguageName')
            if lang_name and lang_name != "Common":
                scanned_languages[lang_name] = scanned_languages.get(lang_name, 0) + 1

        # scan origins
        origin = scan.get('Origin', 'Unknown')
        origins[origin] = origins.get(origin, 0) + 1

    # calculate totals and averages
    total_scan_count = yes_scan_count + no_scan_count
    for bin_key, bin in size_bins.items():
        if (bin['yes_scan_count'] + bin['no_scan_count']) > 0:
            bin['source_pulling_time__avg'] = math.ceil(bin['source_pulling_time__sum'] / (bin['yes_scan_count'] + bin['no_scan_count']))
            bin['queue_time__avg'] = math.ceil(bin['queue_time__sum'] / (bin['yes_scan_count'] + bin['no_scan_count']))
            bin['total_scan_time__avg'] = math.ceil(bin['total_scan_time__sum'] / (bin['yes_scan_count'] + bin['no_scan_count']))
        if bin['yes_scan_count'] > 0:
            bin['engine_scan_time__avg'] = math.ceil(bin['engine_scan_time__sum'] / bin['yes_scan_count'])
            bin['total_scan_time__avg'] = math.ceil(bin['total_scan_time__sum'] / bin['yes_scan_count'])
    results['total_vulns__avg'] = math.ceil(results['total_vulns__sum'] / total_scan_count)
    results['high__avg'] = round(results['high__sum'] / total_scan_count)
    results['medium__avg'] = round(results['medium__sum'] / total_scan_count)
    results['low__avg'] = round(results['low__sum'] / total_scan_count)
    results['info__avg']= round(results['info__sum'] / total_scan_count)

    # group origins
    for origin, count in origins.items():
        # Determine the group for each origin
        group = next((printable_origins[key] for key in printable_origins if origin.startswith(key)), 'Other')
        # Update the grouped origins count
        grouped_origins[group] += count
    grouped_origins_2 = {origin: count for origin, count in grouped_origins.items() if count > 0}

    if tqdm_available:
        pbar.close()
    else:
            print("completed!")
    
    return {
        'first_date': first_date,
        'last_date': last_date,
        'scan_stats_by_date': scan_stats_by_date,
        'scanned_projects': scanned_projects,
        'size_bins': size_bins,
        'results': results,
        'preset_names': preset_names,
        'scanned_languages': scanned_languages,
        'origins': grouped_origins_2
    }



def format_seconds_to_hms(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"



def print_summary(data):

    total_scan_count = yes_scan_count = no_scan_count = full_scan_count = incremental_scan_count = date_max_scan_count = 0
    scan_loc__sum = scan_loc__max = scan_failed_loc__sum = scan_failed_loc__max = date_loc__max = 0
    total_scan_time__sum = source_pulling_time__sum = queue_time__sum = engine_scan_time__sum = 0
    total_scan_time__max = source_pulling_time__max = queue_time__max = engine_scan_time__max = 0
    total_scan_time__avg = source_pulling_time__avg = queue_time__avg = engine_scan_time__avg = 0
    
    weekly_scan_totals = {
        'Monday': 0,
        'Tuesday': 0,
        'Wednesday': 0,
        'Thursday': 0,
        'Friday': 0,
        'Saturday': 0,
        'Sunday': 0,
        'Weekday': 0,
        'Weekend': 0
    }

    # unpack scan stats and crunch numbers
    for scan_date, stats in data['scan_stats_by_date'].items():
        full_scan_count += stats['full_scan_count']
        incremental_scan_count += stats['incremental_scan_count']
        yes_scan_count += stats['yes_scan_count']
        no_scan_count += stats['no_scan_count']
        scan_loc__sum += stats['loc__sum']
        scan_loc__max = max(scan_loc__max, stats['loc__max'])
        scan_failed_loc__sum += stats['failed_loc__sum']
        scan_failed_loc__max = max(scan_failed_loc__max, stats['failed_loc__max'])
        date_loc__max = max(date_loc__max, stats['loc__sum'])
        if(stats['total_scan_count'] > date_max_scan_count):
            date_max_scan_count = stats['total_scan_count']
            date_max_scan_date = scan_date
        day_name = scan_date.strftime('%A')
        day_index = scan_date.weekday()
        weekly_scan_totals[day_name] += stats['total_scan_count']
        if day_index >= 5:  # Saturday or Sunday
            weekly_scan_totals['Weekend'] += stats['total_scan_count']
        else:
            weekly_scan_totals['Weekday'] += stats['total_scan_count']
    total_scan_count = yes_scan_count + no_scan_count
    high_results__scan_count = data['results']['high_results__scan_count']
    medium_results__scan_count = data['results']['medium_results__scan_count']
    low_results__scan_count = data['results']['low_results__scan_count']
    info_results__scan_count = data['results']['info_results__scan_count']
    zero_results__scan_count = data['results']['zero_results__scan_count']
    total_days = (data['last_date'] - data['first_date']).days
    total_weeks = math.ceil(total_days / 7)
    total_scan_days = len(data['scan_stats_by_date'])

    print(f"\nSummary of Scans ({data['first_date']} to {data['last_date']})")
    print("-" * 50)
    print(f"Total number of scans: {format(total_scan_count, ',')}")
    print(f"- Full Scans: {format(full_scan_count, ',')} ({(full_scan_count / total_scan_count) * 100:.1f}%)")
    print(f"- Incremental Scans: {format(incremental_scan_count, ',')} ({(incremental_scan_count / total_scan_count) * 100:.1f}%)")
    print(f"- No Code Change Scans: {format(no_scan_count, ',')} ({(no_scan_count / total_scan_count) * 100:.1f}%)")
    print(f"- Scans with High Results: {format(high_results__scan_count, ',')} ({(high_results__scan_count / total_scan_count) * 100:.1f}%)")
    print(f"- Scans with Medium Results: {format(medium_results__scan_count, ',')} ({(medium_results__scan_count / total_scan_count) * 100:.1f}%)")
    print(f"- Scans with Low Results: {format(low_results__scan_count, ',')} ({(low_results__scan_count / total_scan_count) * 100:.1f}%)")
    print(f"- Scans with Informational Results: {format(info_results__scan_count, ',')} ({(info_results__scan_count / total_scan_count) * 100:.1f}%)")
    print(f"- Scans with Zero Results: {format(zero_results__scan_count, ',')} ({(zero_results__scan_count / total_scan_count) * 100:.1f}%)")
    print(f"- Unique Projects Scanned: {format(len(data['scanned_projects']), ',')}")
    
    print("\nScan Metrics")
    print(f"- Avg LOC per Scan: {format(round(scan_loc__sum / total_scan_count), ',')}")
    print(f"- Max LOC per Scan:  {format(round(scan_loc__max), ',')}")
    print(f"- Avg Failed LOC per Scan: {format(round(scan_failed_loc__sum / yes_scan_count), ',')}")
    print(f"- Max Failed LOC per Scan:  {format(round(scan_failed_loc__max), ',')}")
    print(f"- Avg Daily LOC: {format(round(scan_loc__sum / total_scan_days), ',')}")
    print(f"- Max Daily LOC: {format(round(date_loc__max), ',')}")

    # Iterate through the size_bins dictionary to calculate avg and max durations (overall)
    for bin_key, bin_values in data['size_bins'].items():
        total_scan_time__sum += bin_values['total_scan_time__sum']
        total_scan_time__max = max(total_scan_time__max, bin_values['total_scan_time__max'])
        source_pulling_time__sum += bin_values['source_pulling_time__sum']
        source_pulling_time__max = max(source_pulling_time__max, bin_values['source_pulling_time__max'])
        queue_time__sum += bin_values['queue_time__sum']
        queue_time__max = max(queue_time__max, bin_values['queue_time__max'])
        engine_scan_time__sum += bin_values['engine_scan_time__sum']
        engine_scan_time__max = max(engine_scan_time__max, bin_values['engine_scan_time__max'])
    total_scan_time__avg = total_scan_time__sum / yes_scan_count
    source_pulling_time__avg = source_pulling_time__sum / yes_scan_count
    queue_time__avg = queue_time__sum / yes_scan_count
    engine_scan_time__avg = engine_scan_time__sum / yes_scan_count

    print("\nScan Duration")
    print(f"- Avg Total Scan Duration: {format_seconds_to_hms(total_scan_time__avg)}")
    print(f"- Max Total Scan Duration: {format_seconds_to_hms(total_scan_time__max)}")
    print(f"- Avg Engine Scan Duration: {format_seconds_to_hms(engine_scan_time__avg)}")
    print(f"- Max Engine Scan Duration: {format_seconds_to_hms(engine_scan_time__max)}")
    print(f"- Avg Queued Duration: {format_seconds_to_hms(queue_time__avg)}")
    print(f"- Max Queued Scan Duration: {format_seconds_to_hms(queue_time__max)}")
    print(f"- Avg Source Pulling Duration: {format_seconds_to_hms(source_pulling_time__avg)}")
    print(f"- Max Source Pulling Duration: {format_seconds_to_hms(source_pulling_time__max)}")
    
    print("\nScan Results / Severity")
    print(f"- Average Total Results: {data['results']['total_vulns__avg']}")
    print(f"- Max Total Results: {data['results']['total_vulns__max']}")
    print(f"- Average High Results: {data['results']['high__avg']}")
    print(f"- Max High Results: {data['results']['high__max']}")
    print(f"- Average Medium Results: {data['results']['medium__avg']}")
    print(f"- Max Medium Results: {data['results']['medium__max']}")
    print(f"- Average Low Results: {data['results']['low__avg']}")
    print(f"- Max Low Results: {data['results']['low__max']}")
    print(f"- Average Informational Results: {data['results']['info__avg']}")
    print(f"- Max Informational Results: {data['results']['info__max']}")

    print("\nLanguages")
    for language_name, language_count in sorted(data['scanned_languages'].items(), key=lambda x: x[1], reverse=True):
        percentage = (language_count / total_scan_count) * 100
        print(f"- {language_name}: {format(language_count, ',')} ({percentage:.1f}%)")

    print("\nScan Submission Summary")
    print(f"- Average Scans Submitted per Week: {format(round(total_scan_count / total_weeks), ',')}")
    print(f"- Average Scans Submitted per Day: {format(round(total_scan_count / total_days), ',')}")
    print(f"- nAverage Scans Submitted per Week Day: {format(round(weekly_scan_totals['Weekday'] / (total_weeks * 5)), ',')}")
    print(f"- Average Scans Submitted per Weekend Day: {format(round(weekly_scan_totals['Weekend'] / (total_weeks * 2)), ',')}")
    print(f"- Max Daily Scans Submitted: {format(date_max_scan_count, ',')}")
    print(f"- Date of Max Scans: {date_max_scan_date}")

    print("\nDay of Week Scan Average")
    for day_name, total_day_count in weekly_scan_totals.items():
        if day_name == "Weekday" or day_name == "Weekend":
            continue
        percentage = (total_day_count / total_scan_count) * 100
        print(f"- {day_name}: {format(round(total_day_count / total_weeks), ',')} ({percentage:.1f}%)")

    print("\nOrigin")
    for origin, count in sorted(data['origins'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_scan_count) * 100
        print(f"- {origin}: {format(count, ',')} ({percentage:.1f}%)")

    print("\nPresets")
    for preset_name, preset_count in sorted(data['preset_names'].items(), key=lambda x: x[1], reverse=True):
        percentage = (preset_count / total_scan_count) * 100
        print(f"- {preset_name}: {format(preset_count, ',')} ({percentage:.1f}%)")

    print("\nScan Time Analysis")

    # Print the header of the table
    print(f"{'LOC Range':<12} {'Scans':<12} {'% Scans':<10} {'Avg Total Time':<18} {'Avg Source Pull':<18} {'Avg Queue':<18} "
    f"{'Avg Engine':<18}")
    
    # Iterate through the size_bins dictionary to print the per-bin data
    for bin_key, bin_values in data['size_bins'].items():
        # Format times from seconds to HH:MM:SS
        source_pulling_time__avg = format_seconds_to_hms(bin_values['source_pulling_time__avg'])
        queue_time__avg = format_seconds_to_hms(bin_values['queue_time__avg'])
        engine_scan_time__avg = format_seconds_to_hms(bin_values['engine_scan_time__avg'])
        total_scan_time__avg = format_seconds_to_hms(bin_values['total_scan_time__avg'])
        
        # Print the formatted row for each bin
        print(f"{bin_key:<12} {bin_values['yes_scan_count'] + bin_values['no_scan_count']:<12,} "
        f"{(math.ceil((10000 * (bin_values['yes_scan_count'] + bin_values['no_scan_count']) / total_scan_count)) / 100):<11.2f}"
        f"{total_scan_time__avg:<18} {source_pulling_time__avg:<18} {queue_time__avg:<18} {engine_scan_time__avg:<18}")


def generate_csvs(data, basename):
    print("")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process scans and output CSV files if requested.")
    parser.add_argument("input_file", help="The JSON file containing scan data.")
    parser.add_argument("--csv", action="store_true", help="Generate CSV output files.")
    
    args = parser.parse_args()
    input_file = args.input_file

    scans = ingest_file(input_file)

    data = process_scans(scans)

    print_summary(data)

    print("")

    if args.csv:
        generate_csvs(data, os.path.splitext(os.path.basename(input_file))[0])
