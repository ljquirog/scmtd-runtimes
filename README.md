# scmtd-runtimes

## Project Description
Use Swiftly's Runtimes API to streamline runtime analysis. Directory includes 3 main functions:
- End-to-end runtimes at the percentile level
- Creates new timeband groups based on percentile level
- Creates new suggestions for runtimes using a varying percentile level for each timepoint

## File descriptions
api_request.py -> calls the api
json_to_file.py -> turns api call into json

percentiles_test.py -> calculates the runtime per trip, groups trips into timebands
timebands_by_percentile.py > makes timeband groups, puts them into csv

runtime_suggestions_by_percentile.py > makes runtime suggestions per new timebands
runtimes_to_csv.py