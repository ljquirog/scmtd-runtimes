import http.client
import csv
import json
import math
import api_request
import json_to_file
import sys 
from datetime import datetime, timedelta

def runtime_per_trip(route_stats):
    percentile_runtimes = {}
    scheduled_runtimes = {}

    for trip in route_stats['pathStats']:
        # skip if observed runtime is None (missing data)
        if trip['aggregates'][1]['value'] is None:
            continue

        # initialize vars
        scheduled_mins, percentile_mins, trip_start_time, stop_name = trip['scheduledRuntimeMinutes'], math.ceil(trip['aggregates'][1]['value']/60), trip['scheduledTripStartTime'], trip['fromStop']['name']  
        
        # scheduled runtimes
        if trip_start_time not in scheduled_runtimes:
            scheduled_runtimes[trip_start_time] = {}
        scheduled_runtimes[trip_start_time][stop_name] = scheduled_mins

        # observed runtimes
        if trip_start_time not in percentile_runtimes:
            percentile_runtimes[trip_start_time] = {}
        percentile_runtimes[trip_start_time][stop_name] = percentile_mins

    # total the runtimes for scheduled runtimes
    for trip_time, stops in scheduled_runtimes.items():
        total = 0

        # skip any key that's 'total' to avoid adding to itself
        total = sum(runtime for key, runtime in stops.items() if key != total)
        # for key, runtime in stops.items():
        #     if key == "total":
        #         continue
        #     total += runtime
        
        # rebuild dict so 'total' always comes last
        scheduled_runtimes[trip_time] = {
            # make a new key value pair for each key value in the dict, only if its not total
            **{k: v for k, v in stops.items() if k != "total"},
            "total": total, # assign total to total only once you've rebuilt dictionary
        }
        
    # total the runtimes for percentile runtimes
    for trip_time, stops in percentile_runtimes.items():
        total = 0

        # skip any key that's 'total' to avoid adding to itself
        total = sum(runtime for key, runtime in stops.items() if key != total)
        
        # rebuild dict so 'total' always comes last
        percentile_runtimes[trip_time] = {
            # make a new key value pair for each key value in the dict, only if its not total
            **{k: v for k, v in stops.items() if k != "total"},
            "total": total, # assign total to total only once you've rebuilt dictionary
        }      

    return percentile_runtimes, scheduled_runtimes

"""
    Groups trips into timebands based on runtime stability.
    Args:
        percentile_runtimes (dict): Dict where keys are trip times (string), and values are dicts with 'total' runtime (int).
        threshold (int): Maximum allowed difference (minutes) within a group's runtimes.
    Returns:
        list: A list of groups, where each group is a list of (time, runtime) tuples.
"""
def group_timebands(percentile_runtimes, threshold=5):
    grouped = [] # final list of groups
    current_group = []
    current_min = current_max = None # track max and min runtime in current group
    
    for time, stops in percentile_runtimes.items():
        current_time = time
        current_runtime = percentile_runtimes[time]['total']

        # if starting a new group, initialize it w/ the first trip
        if not current_group:
            current_group = [(current_time, current_runtime)]
            current_min = current_max = current_runtime
            continue
        
        # calculate what the new max and min would be if this trip was added to the new group
        new_min = min(current_min, current_runtime)
        new_max = max(current_max, current_runtime)

        #check if adding this trip still keeps the group's runtime spread within the threshold
        # if yes, keep it in the group 
        if new_max - new_min <= threshold:
            current_group.append((current_time, current_runtime))
            current_min, current_max = new_min, new_max
        # otherwise, close out the current group and start a new one
        else:
            grouped.append(current_group)
            current_group = [(current_time, current_runtime)]
            current_min = current_max = current_runtime
    # append the last group after looping
    if current_group:
        grouped.append(current_group)

    return grouped
   
def make_timebands(grouped_runtimes):
    timebands = []
    time_format = "%H:%M:%S"

    for i, group in enumerate(grouped_runtimes):
        # Start time = first trip time - 5 min

        # skip if trip is at or after midnight
        if group[0][0].startswith("24"):
            continue
        start_time = datetime.strptime(group[0][0], time_format) - timedelta(minutes=5)
        # End time = next group's first trip - 6 min, unless it's the last group
        if i < len(grouped_runtimes) - 1:
            if grouped_runtimes[i+1][0][0].startswith("24"):
                continue
            end_time = datetime.strptime(grouped_runtimes[i+1][0][0], time_format) - timedelta(minutes=6)
        else:
            if group[-1][0].startswith("24"):
                continue
            # If last group, just take last trip time + ~30 min buffer (adjust as needed)
            end_time = datetime.strptime(group[-1][0], time_format) + timedelta(minutes=30)

        # Runtime = avg of group runtimes, rounded UP
        if len(group) == 1:
            runtime = group[0][1]
        else:
            # what is _ ???
            avg = sum(rt for _, rt in group) / len(group)
            runtime = math.ceil(avg)

        # Append result
        timebands.append([(start_time.strftime(time_format), end_time.strftime(time_format)), runtime])
    
    return timebands
   
if __name__ == "__main__":
    route, percentile, start, end, dow, dir = 34, 60, "09-11-2025", "10-12-2025", "1,2,3,4,5", 1
    # if len(sys.argv) > 1:
    #     route = sys.argv[1]
    #     percentile = sys.argv[2]
    
    route_stats_json = api_request.call(route, percentile, start, end, dow, dir)
    route_stats_to_txt = json_to_file.txt_convert('routeStats.json', route_stats_json)  

    with open('routeStats.json', "r") as file:
        route_stats = json.load(file)    
    # === Sort the list by scheduledTripStartTime ===
    route_stats["pathStats"].sort(key=lambda x: x["scheduledTripStartTime"])

    # === Write the sorted JSON back ===
    with open("routeStats.json", "w", encoding="utf-8") as file:
        json.dump(route_stats, file, indent=2, ensure_ascii=False)
    
    percentile_runtimes, schedule_runtimes = runtime_per_trip(route_stats) 
    grouped_timebands = group_timebands(percentile_runtimes)
    print(grouped_timebands)

    new_timebands = make_timebands(grouped_timebands) # print(grouped_timebands, "\n", new_timebands)
    print(new_timebands)
