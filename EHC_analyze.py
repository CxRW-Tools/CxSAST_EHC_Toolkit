import ijson
import sys
from datetime import datetime

def process_scans(file_path):
    with open(file_path, 'rb') as f:
        scans = ijson.items(f, 'value.item')
        
        size_bins = {
            '0 to 20k': 0,
            '20k-50k': 0,
            '50k-100k': 0,
            '100k-250k': 0,
            '250k-500k': 0,
            '500k-1M': 0,
            '1M-2M': 0,
            '2M-3M': 0,
            '3M-5M': 0,
            '5M-7M': 0,
            '7M-10M': 0,
            '10M+': 0
        }
        preset_names = {}
        scan_types = {
            'Full': 0,
            'Incremental': 0
        }
        scanned_languages = {}
        origins = {}
        first_date = datetime.max.date()
        last_date = datetime.min.date()

        for scan in scans:
            loc = scan.get('LOC', None)
            preset_name = scan.get('PresetName', None)
            incremental = scan.get('IsIncremental', None)
            
            # Extract the scanned languages
            for language in scan.get('ScannedLanguages', []):
                lang_name = language.get('LanguageName')
                if lang_name and lang_name != "Common":
                    scanned_languages[lang_name] = scanned_languages.get(lang_name, 0) + 1

            # Extract and compare the scan date
            scan_date_str = scan.get('ScanRequestedOn', '').split('T')[0]
            scan_date = datetime.strptime(scan_date_str, "%Y-%m-%d").date()
            first_date = min(first_date, scan_date)
            last_date = max(last_date, scan_date)

            # Increment count for PresetName
            if preset_name:
                preset_names[preset_name] = preset_names.get(preset_name, 0) + 1

            # Increment count for scan type
            if incremental is not None:
                scan_types['Incremental' if incremental else 'Full'] += 1

            # Process origin
            origin = scan.get('Origin', 'Unknown')
            origins[origin] = origins.get(origin, 0) + 1

            # LOC count
            if not isinstance(loc, int):
                continue

            if loc <= 20000:
                size_bins['0 to 20k'] += 1
            elif loc <= 50000:
                size_bins['20k-50k'] += 1
            elif loc <= 100000:
                size_bins['50k-100k'] += 1
            elif loc <= 250000:
                size_bins['100k-250k'] += 1
            elif loc <= 500000:
                size_bins['250k-500k'] += 1
            elif loc <= 1000000:
                size_bins['500k-1M'] += 1
            elif loc <= 2000000:
                size_bins['1M-2M'] += 1
            elif loc <= 3000000:
                size_bins['2M-3M'] += 1
            elif loc <= 5000000:
                size_bins['3M-5M'] += 1
            elif loc <= 7000000:
                size_bins['5M-7M'] += 1
            elif loc <= 10000000:
                size_bins['7M-10M'] += 1
            else:
                size_bins['10M+'] += 1

        return size_bins, preset_names, scan_types, scanned_languages, origins, first_date, last_date

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python EHC_analyze.py json_input_file")
        sys.exit(1)
    
    file_path = sys.argv[1]
    size_summary, preset_summary, scan_type_summary, language_summary, origins_summary, first_date, last_date = process_scans(file_path)
    
    total_count = scan_type_summary['Full'] + scan_type_summary['Incremental']
    
    print(f"Summary of Scans ({first_date} to {last_date})")
    print("-" * 20)
    print(f"Total number of scans: {format(total_count, ',')}")
    
    print("\nScan Type")
    for scan_name, scan_count in scan_type_summary.items():
        percentage = (scan_count / total_count) * 100
        print(f"- {scan_name}: {format(scan_count, ',')} ({percentage:.1f}%)")
    
    print("\nOrigin Analysis")
    for origin, count in origins_summary.items():
        percentage = (count / total_count) * 100
        print(f"- {origin}: {format(count, ',')} ({percentage:.1f}%)")

    print("\nLOC Analysis")
    for bin_name, bin_count in size_summary.items():
        percentage = (bin_count / total_count) * 100
        print(f"- {bin_name}: {format(bin_count, ',')} ({percentage:.1f}%)")

    print("\nPreset Analysis")
    for preset_name, preset_count in preset_summary.items():
        percentage = (preset_count / total_count) * 100
        print(f"- {preset_name}: {format(preset_count, ',')} ({percentage:.1f}%)")


    print("\nLanguage Analysis")
    for language_name, language_count in sorted(language_summary.items(), key=lambda x: x[1], reverse=True):
        percentage = (language_count / total_count) * 100
        print(f"- {language_name}: {format(language_count, ',')} ({percentage:.1f}%)")
