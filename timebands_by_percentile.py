import http.client
import csv
import json
import math
import api_request
import json_to_file
import sys 
import percentiles_test
from datetime import datetime, timedelta

if __name__ == "__main__":
    # ask user for input
    
    route = input("what route(s) would you like to run this for? ")
    percentile = input ("at what percentile? ")

    # api call
    route_stats_json = api_request.call("path-stats", route, percentile)
    
    # convert to json file, add "scheduledRuntimeMinutes" variable
    route_stats_to_txt = json_to_file.txt_convert('routeStats.json', route_stats_json)  
    with open('routeStats.json', "r") as file:
        route_stats = json.load(file)    

    # gets the runtimes for a route based on percentile (observed) and schedule, respectively.
    # stop, runtime pair for each timepoint, with the total runtime at the end of list
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(route_stats) 
    grouped_timebands = percentiles_test.group_timebands(percentile_runtimes)    
    new_timebands = percentiles_test.make_timebands(grouped_timebands) 
    print(new_timebands)

    if route == "all":
        print("hi")
    elif route == type(list):
        print("yo")
    else:
        print("route")
