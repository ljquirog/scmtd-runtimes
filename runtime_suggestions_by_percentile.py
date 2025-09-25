import json
import math
import api_request
import json_to_file
import percentiles_test


def get_route_stats(route, percentile, start_date, end_date, days_of_week):
    """
    Fetch route stats JSON for a given percentile and write to file.
    Returns the parsed JSON as a dict.
    """
    route_stats_json = api_request.call(route, percentile, start_date, end_date, days_of_week)
    json_to_file.txt_convert('routeStats.json', route_stats_json)  
    
    with open('routeStats.json', "r") as file:
        return json.load(file)
    
def get_num_timepoints(route, start, end, dow):
    length, timepoints = 0, []
    fixed_route_stats = get_route_stats(route, 60, start, end, dow)
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(fixed_route_stats)
    for trip_time, stops in percentile_runtimes.items():
        # Make sure user provided the right number of percentiles
        length = len(stops)-1
        # Grab all stop names except 'total'
        timepoints = [tp for tp in stops if tp != "total"]
        print(stops)
        break  # only need to do this once
    return length, timepoints


def suggested_runtimes(route, percentiles, start, end, dow):
    """
    Build suggested runtimes for each timeband, using custom percentiles per timepoint.

    Args:
        route (int): The route ID
        percentiles (list[int]): List of percentiles, one per timepoint
        start, end (str): Date range
        dow (list): Days of week to filter

    Returns:
        list: Suggested runtimes per new timeband in the form:
              [((start_time, end_time), {timepoint: avg_runtime, ..., "total": total})]
    """

    # === STEP 1: Build "skeleton" timebands using default (60th percentile) ===
    print("\n=== STEP 1: Build skeleton timebands with default (60th) percentile ===")
    base_route_stats = get_route_stats(route, 60, start, end, dow)
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(base_route_stats)

    # grouped_timebands: keeps individual trips grouped if runtimes are within threshold
    grouped_timebands = percentiles_test.group_timebands(percentile_runtimes)

    # new_timebands: consolidates grouped trips into suggested new timebands
    new_timebands = percentiles_test.make_timebands(grouped_timebands)

    print("\nGrouped timebands (raw trips grouped):")
    for tb in grouped_timebands:
        print("   ", tb)

    print("\nNew (suggested) timebands (rolled up from groups):")
    for tb in new_timebands:
        print("   ", tb)

    # === STEP 2: Extract timepoint names from the first trip ===
    print("\n=== STEP 2: Extract timepoint names ===")
    timepoints = []
    for trip_time, stops in percentile_runtimes.items():
        # Make sure user provided the right number of percentiles
        if len(stops)-1 != len(percentiles):
            raise ValueError("Number of timepoints != number of percentiles provided")
        # Grab all stop names except 'total'
        timepoints = [tp for tp in stops if tp != "total"]
        break  # only need to do this once
    print("Timepoints:", timepoints)
    print("Percentiles:", percentiles)

    # === STEP 3: Re-run stats for each timepoint at its assigned percentile ===
    print("\n=== STEP 3: Re-run stats for each timepoint at its assigned percentile ===")
    per_timepoint_runtimes = {tp: {} for tp in timepoints}

    for i, p in enumerate(percentiles):
        tp = timepoints[i]
        print(f"\n-- Fetching runtimes for timepoint '{tp}' at percentile {p} --")
        route_stats = get_route_stats(route, p, start, end, dow)
        percentile_runtimes, _ = percentiles_test.runtime_per_trip(route_stats)

        # Fill per_timepoint_runtimes with runtimes for this stop at this percentile
        for trip_time, stops in percentile_runtimes.items():
            per_timepoint_runtimes[tp][trip_time] = stops[tp]
            print(f"Trip {trip_time}: {tp} runtime = {stops[tp]}")

    # === STEP 4: Aggregate runtimes per timeband ===
    print("\n=== STEP 4: Aggregate runtimes per timeband ===")
    suggested = []
    for j, (timeband_range, _) in enumerate(new_timebands):
        tb_start, tb_end = timeband_range
        agg = {}
        print(f"\nTimeband {tb_start} - {tb_end}")

        # For each timepoint, look at all trips inside this timeband group
        for tp in timepoints:
            runtimes = []
            print(f"  Timepoint {tp}:")
            for trip_time, _ in grouped_timebands[j]:
                # NOTE: "for trip_time, _ in grouped_timebands[j]" → 
                # grouped_timebands[j] is a list of tuples (trip_time, runtime).
                # We only care about trip_time here, not runtime, so we assign
                # the second element to "_" to ignore it.
                if trip_time in per_timepoint_runtimes[tp]:
                    runtime_val = per_timepoint_runtimes[tp][trip_time]
                    runtimes.append(runtime_val)
                    print(f"    Trip {trip_time} → {runtime_val}")

            # Average runtimes across trips (round up to whole minutes)
            if runtimes:
                avg_val = math.ceil(sum(runtimes) / len(runtimes))
                agg[tp] = avg_val
                print(f"  → Average (rounded up) for {tp}: {avg_val}")

        # Add total across timepoints
        agg["total"] = sum(agg.values())
        print(f"  → Total runtime for timeband: {agg['total']}")

        suggested.append(((tb_start, tb_end), agg))

    # === FINAL OUTPUT ===
    print("\n=== FINAL SUGGESTED RUNTIMES ===")
    for tb in suggested:
        print(tb)

    return suggested

if __name__ == "__main__":
    len, tp = get_num_timepoints("16", "09-12-2025", "09-24-2025", "1,2,3,4,5")
    '''9/25 left off here: DEBUG!!!!!!!!!!!'''
    print(len, tp)
    start_date, end_date = input("* Start date and end date\n** Format: 'MM-DD-YY' 'MM-DD-YY'\n").split()
    days_of_week = input("* Day of week\n** Format: '1,2,3,4,5,6,7'\n")
    route = input("* Route: ")
    length, timepoints = get_num_timepoints(route, start_date, end_date, days_of_week)
    print(f"\n> Route {route} has {length} timepoints:")
    for tp in timepoints:
        print(">> ", tp)
    timepoints = input(f"\n* List the percentiles you'd like each timepoint to be ran at.\n** Format: [30,40,50]\n")
    '''
    # -- Left off here --
        # TODO: Add variables to suggested_runtimes
        
        Other ideas:
        - Compare runtime suggestions total to avg timeband total
            - E.g. do the 90th and take the difference to get layover
        - Write a function to convert suggested runtimes to csv in json_to_csv and call it in main
        - Combine timebands_by_percentile and runtime_suggestions_by_percentile together??

    I DON'T WANT TO STOP UGHHHH
    '''
    # suggested_runtimes(11, [30,40,50], '03-25-2025', '04-13-2025', '1,2,3,4,5')