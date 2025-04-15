# CxSAST_EHC_Toolkit
<p>This toolkit includes a set of scripts that augment the Excel EHC tool. In particular, these tools can be helpful when processing extremely large EHC data files or looking for particular scan metrics.</p>

## EHC_analyze.py
<p>Analyzes and summarizes EHC data, including total scans, scan types, LOC ranges, and presets<br>
<br>Usage:<br>
python EHC_analyze.py input_file</p>

## EHC_project_filter.py
<p>Filters an EHC data file to only a single project (i.e., removes all other project data) and exports the result to a new JSON file<br>
<br>Usage:<br>
python EHC_project_filter.py --filter-project PROJECT_NAME input_file</p>

## EHC_scantime_deviation.py
<p>Identifies deviations in scan times for each project and provides the projects that have deviations beyond a certain minimum threshold<br>
<br>Usage:<br>
python EHC_scantime_deviation.py [--min-deviation-percentage MIN_DEVIATION_PERCENTAGE] [--min-deviation-time MIN_DEVIATION_TIME] [--csv-export] [--incremental] input_file<br>
Options:<br>
--min-deviation-percentage: The percentage of deviation in scan time to consider significant<br>
--min-deviation-time: Minimum deviation time in the format 1h47m40s<br>
--csv-export: Exports the result to a CSV file
--incremental: Option to include incremental scans</p>

## EHC_split.py
<p>Splits a 90-day EHC file into 30-day parts; useful for processing extremely large EHC data sets<br>
<br>Usage:<br>
python EHC_split.py input_file</p>


## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
