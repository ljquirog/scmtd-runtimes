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
    # route = input("what route(s) would you like to run this for? ")
    # percentile = input("at what percentile? ")
    # start_date = input("start date (format: 'MM-DD-YYYY'): ")
    # end_date = input("end date (format: 'MM-DD-YYYY'): ")
    # days_of_week = input("what days of the week? (format: '1,2,3,4,5,6,7') ")
    route, percentile, start_date, end_date, days_of_week = input("provide the following information, each variable separated by a space:\nroute - format: string \n\tall routes: 'all', a subset of routes: '[str1, str2])\npercentile - format: int\nstart date - format: string\n\tex) 'MM-DD-YYYY'\nend date - format: string.\n\tex) 'MM-DD-YYYY'\nday of the week - format: string\n\tdays in a comma separated list, no spaces\n\tex) 1,2,3,4,5,6,7\n").split()

    if route == 'all':
        all_routes_sum = all_routes_test.run_all_routes(start_date, end_date, days_of_week)
        all_routes = all_routes_test.get_all_routes(all_routes_sum)
        print(all_routes)
        for r in all_routes:
            if r == '18': continue
            timebands = route_new_timebands(r, percentile, start_date, end_date, days_of_week)
            print(r, "\n", timebands)
    elif type(route) == list:
        for r in route:
            timebands = route_new_timebands(r, percentile, start_date, end_date, days_of_week)
            print(timebands)
    else:
        timebands = route_new_timebands(route, percentile, start_date, end_date, days_of_week)
        print(timebands)
        



    # # ask user for input
    
    # route = input("what route(s) would you like to run this for? ")
    # percentile = input("at what percentile? ")
    # start_date = input("start date (format: 'MM-DD-YYYY'): ")
    # end_date = input("end date (format: 'MM-DD-YYYY'): ")
    # days_of_week = input("what days of the week? (format: '1,2,3,4,5,6,7') ")

    # '''api call - route: int = 11,
    # percentile: int = 60,
    # start_date: str = "03-13-2025",
    # end_date: str = "06-18-2025",
    # days_of_week: str = "1,2,3,4,5"
    # '''
    # route_stats_json = api_request.call(route, percentile, start_date, end_date, days_of_week)
    
    # # convert to json file, add "scheduledRuntimeMinutes" variable
    # route_stats_to_txt = json_to_file.txt_convert('routeStats.json', route_stats_json)  
    # with open('routeStats.json', "r") as file:
    #     route_stats = json.load(file)    

    # # gets the runtimes for a route based on percentile (observed) and schedule, respectively.
    # # stop, runtime pair for each timepoint, with the total runtime at the end of list
    # percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(route_stats) 
    # grouped_timebands = percentiles_test.group_timebands(percentile_runtimes)    
    # new_timebands = percentiles_test.make_timebands(grouped_timebands) 
    # print(new_timebands)

    # if route == "all":
    #     print("hi")
    # elif route == type(list):
    #     print("yo")
    # else:
    #     print("route")
