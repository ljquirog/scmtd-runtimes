import csv
import json
import math
import api_request
import sys
import percentiles_test

def raw_path_stats_csv_convert(filename, json_str):
    # open CSV for writing
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        
        # header row
        writer.writerow([
            "routeShortName", "tripPatternId", "scheduledRuntimeMinutes", 
            "percentile", "observedRuntimeSeconds", "fromStop", "toStop"
        ])
        
        # loop through pathStats
        for path in json_str["pathStats"]:
            # get scheduled runtime
            scheduled_seconds = float(path["aggregates"][0]["value"][0])
            scheduled_minutes = math.ceil(scheduled_seconds / 60)
            
            # get observed runtime (20th percentile in this case)
            observed = path["aggregates"][1]["value"]
            percentile_val = path["aggregates"][1]["percentile"]
            
            writer.writerow([
                path["routeShortName"],
                path["tripPatternId"],
                scheduled_minutes,
                percentile_val,
                observed,
                path["fromStop"]["name"],
                path["toStop"]["name"]
            ])
    file.close()

def timebands_to_csv(filename, timebands_list):
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)

        # first row = "fromStop - toStop"
        row1 = []
        # second row = value
        row2 = []

        for time in timebands_list:
            from_stop, to_stop = time[0]
            value = time[1]

            row1.append(f"{from_stop} - {to_stop}")
            row2.append(value)

        # write both rows
        writer.writerow(row1)
        writer.writerow(row2)
    print(filename)

if __name__ == "__main__":
    module = 'path-stats'
    filename = 'routeStats2.csv'
    route = 11
    percentile = 60
    if len(sys.argv) > 1:
        module = sys.argv[1]
        filename = sys.argv[2]
        route = sys.argv[3]
        percentile = sys.argv[4]

    
    if module == 'path-stats':
        route_stats = api_request.call(module, route)
        raw_path_stats_csv_convert(filename, route_stats)
    
    if module == 'timebands':
        route_stats_json = api_request.call('path-stats', route, percentile)
        
        with open('routeStats.json', "r") as file:
            route_stats = json.load(file)
    
            percentile_runtimes, sched = percentiles_test.runtime_per_trip(route_stats)
            
            grouped_timebands = percentiles_test.group_timebands(percentile_runtimes)
            print(grouped_timebands)
    
            new_timebands = percentiles_test.make_timebands(grouped_timebands)

            timebands_to_csv(filename, new_timebands)
            print("done")
    