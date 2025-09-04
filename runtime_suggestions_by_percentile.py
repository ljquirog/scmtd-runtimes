import sys
import json
import api_request
import percentiles_test
import timebands_by_percentile
import json_to_file

def grouped_and_new_timebands(route, percentile, start_date, end_date, days_of_week):
    route_stats_json = api_request.call(route, percentile, start_date, end_date, days_of_week)
    
    route_stats_to_txt = json_to_file.txt_convert('routeStats.json', route_stats_json)  
    with open('routeStats.json', "r") as file:
        route_stats = json.load(file)    

    # print(route_stats)

    # gets the runtimes for a route based on percentile (observed) and schedule, respectively.
    # stop, runtime pair for each timepoint, with the total runtime at the end of list
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(route_stats) 
    grouped_timebands = percentiles_test.group_timebands(percentile_runtimes)    
    new_timebands = percentiles_test.make_timebands(grouped_timebands) 
    
    return grouped_timebands, new_timebands

def hi(grouped_runtimes, new_runtimes):
    if len(new_runtimes) != len(grouped_runtimes):
        raise "Error"
    
    # new runtimes is the suggested new timebands and the runtime associated with it
    # grouped runtimes is the same new timebands, but grouped by 
    for i, v in enumerate(new_runtimes):
        # print("new: ", new_runtimes[i], "group: ", grouped_runtimes[i])
        for a, n in enumerate(grouped_runtimes[i]):
            trip_time = n[0]
            # runtime = n[1]

            '''
            oops! need to revisit this once i've built all the components.
            
            here's what the loop/process should look like:

                for every trip in the timeband group:
                - get # of timepoints for specified route
                - get a user specified percentile for each given timepoint
                - iterate through each timepoint:
                    - pull runtimes using a percentile (speciifed by the user or default)
                    - 
                - get runtimes for that timepoint using a percentile
                - average the percentile runtimes for that timepoint for all trips within a runtime group
                - return the averaged runtimes per timepoint as a total, "suggested" runtime.
                
                later:
                - compare suggestions to current (use schedule runtimes in grouped_timebands(), replicate above process, then compare)
                - compare suggestions' total runtime to the total runtime for that timeband group in new_timebands 
                - compare to swiftly's suggestions???
            '''


if __name__ == "__main__":
    grouped_timebands, new_timebands = grouped_and_new_timebands(11, 60, '03-15-2025', '06-18-2025', '1,2,3,4,5')
    hi(grouped_timebands, new_timebands)