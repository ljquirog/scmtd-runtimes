import http.client
import csv
import json
import math
import api_request
import json_to_file
import sys 
import percentiles_test
import all_routes_test
from datetime import datetime, timedelta

'''
yayyy comment block!!!
ok ok
'''
def route_new_timebands(route, percentile, start_date, end_date, days_of_week):
    route_stats_json = api_request.call(route, percentile, start_date, end_date, days_of_week)
    
    route_stats_to_txt = json_to_file.txt_convert('routeStats.json', route_stats_json)  
    with open('routeStats.json', "r") as file:
        route_stats = json.load(file)    

    # gets the runtimes for a route based on percentile (observed) and schedule, respectively.
    # stop, runtime pair for each timepoint, with the total runtime at the end of list
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(route_stats) 
    grouped_timebands = percentiles_test.group_timebands(percentile_runtimes)    
    new_timebands = percentiles_test.make_timebands(grouped_timebands) 
    return new_timebands

if __name__ == "__main__":
    # e.g. [11,19] 60 03-13-2025 06-18-2025 '1,2,3,4,5'
    route, percentile, start_date, end_date, days_of_week = input(
    "provide the following information, each variable separated by a space:\n" \
        "route - format: string \n\t" \
            "ex) for all routes: 'all', a subset of routes: '[str1, str2])" \
        "\npercentile - format: int\n" \
        "start date - format: string\n\t" \
            "ex) 'MM-DD-YYYY'\n" \
        "end date - format: string.\n\t" \
            "ex) 'MM-DD-YYYY'\n" \
        "day of the week - format: string\n\t" \
            "days in a comma separated list, no spaces\n\t" \
            "ex) 1,2,3,4,5,6,7\n"
        ).split()
    print(type(route))
    if route == 'all':
        all_routes_sum = all_routes_test.run_all_routes(start_date, end_date, days_of_week)
        all_routes = all_routes_test.get_all_routes(all_routes_sum)
        print(all_routes)
        for r in all_routes:
            if r == '18': continue
            timebands = route_new_timebands(r, percentile, start_date, end_date, days_of_week)
            print(r, "\n", timebands)
    elif type(eval(route)) == list:
        route_list = eval(route)
        for r in route_list:
            print(f"{r}: ")
            timebands = route_new_timebands(r, percentile, start_date, end_date, days_of_week)
            print(timebands)
            print(f"count of timebands: {len(timebands)}")
    else:
        timebands = route_new_timebands(route, percentile, start_date, end_date, days_of_week)
        print(timebands)
        