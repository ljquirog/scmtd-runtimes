import os
import json
import math
import api_request
import json_to_file
import percentiles_test
import runtimes_to_csv
import numpy as np
from datetime import datetime, timedelta
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from collections import defaultdict

def diff_runtimes(scheduled, suggested):
    """
    Returns a diff matrix with the same structure as input:
    [ ((timeband_start, timeband_end), {stop: diff, ...}), ... ]
    where diff = scheduled - suggested
    """
    diff_data = []
    for (tb_sched, vals_sched), (tb_sugg, vals_sugg) in zip(scheduled, suggested):
        diff_dict = {}
        for stop in vals_sched.keys():
            val_sched = vals_sched.get(stop, 0)
            val_sugg = vals_sugg.get(stop, 0)
            # handle missing or None
            try:
                diff = val_sched - val_sugg
            except TypeError:
                diff = ""
            diff_dict[stop] = diff
        diff_data.append((tb_sched, diff_dict))
    return diff_data


def daterange(start_date, end_date):
    """Yield each date in the range [start_date, end_date]."""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def get_route_stats(route, percentile, start_date, end_date, days_of_week, direction):
    """
    Fetch route stats JSON for a given percentile and write to file.
    Returns the parsed JSON as a dict.
    """
    route_stats_json = api_request.call(route, percentile, start_date, end_date, days_of_week, direction)
    json_to_file.txt_convert('routeStats.json', route_stats_json)  
    
    with open('routeStats.json', "r") as file:
        route_stats = json.load(file)    
    
    # === Sort the list by scheduledTripStartTime ===
    route_stats["pathStats"].sort(key=lambda x: x["scheduledTripStartTime"])

    # === Write the sorted JSON back ===
    with open("routeStats.json", "w", encoding="utf-8") as file:
        json.dump(route_stats, file, indent=2, ensure_ascii=False)
    
    return route_stats
    
def get_num_timepoints(route, start, end, dow, direction):
    length, timepoints = 0, []
    fixed_route_stats = get_route_stats(route, 60, start, end, dow, direction)
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(fixed_route_stats)
    for trip_time, stops in percentile_runtimes.items():
        # Make sure user provided the right number of percentiles
        length = len(stops)-1
        # Grab all stop names except 'total'
        timepoints = [tp for tp in stops if tp != "total"]
        break  # only need to do this once
    # timepoint_length = dict()
    # # check to see if route has multiple variants (based on when # timepoints differs)
    # for trip_time, stops in percentile_runtimes.items():
    #     # Make sure user provided the right number of percentiles
    #     length = len(stops)-1
    #     timepoint_length[length] = stops
    
    # max_timepoint = max(timepoint_length.keys())
    # timepoints = timepoint_length[max_timepoint]
    # timepoints = [stops for stops in timepoints.keys() if stops != "total"]
    # length = len(timepoints)

    return length, timepoints

def end_to_end_runtimes(route, start, end, dow, direction,variant_trips=0):
    print("** END TO END RUNTIMES **")
    # === STEP 1: Build "skeleton" timebands using default (60th percentile) ===
    print("\n=== STEP 1: Build skeleton timebands with default (60th) percentile ===")
    base_route_stats = get_route_stats(route, 60, start, end, dow, direction)
    if variant_trips:
        filter_diff_variants(base_route_stats, variant_trips, "routeStats.json")
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(base_route_stats)

    grouped_timebands = percentiles_test.group_timebands(percentile_runtimes,3) # groups trips if runtimes are within threshold
    new_timebands = percentiles_test.make_timebands(grouped_timebands) # consolidate grouped trips into new timebands

    base_route_stats = get_route_stats(route, 85, start, end, dow, direction)
    if variant_trips:
        filter_diff_variants(base_route_stats, variant_trips, "routeStats.json")
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(base_route_stats)
    
    # === STEP 2: Run end-to-end percentile runtimes per trip ===
    print("\n=== STEP 2: Run end-to-end percentile runtimes per trip ===")
    runtimes_85 = {"total": {}}
    for trip_time, stops in percentile_runtimes.items():
        runtimes_85["total"][trip_time] = stops["total"]
    

    # === STEP 3: Aggregate runtimes per timeband ===
    print("\n=== STEP 3: Aggregate runtimes per timeband ===")

    suggested = []
    for j, (timeband_range, _) in enumerate(new_timebands):
        tb_start, tb_end = timeband_range
        agg = {}
        print(f"\nTimeband {tb_start} - {tb_end}")

        # For each timepoint, look at all trips inside this timeband group
        for total in runtimes_85:
            new_runtimes = []

            for trip_time, _ in grouped_timebands[j]:
                if trip_time in runtimes_85[total]:
                    new_runtimes.append(runtimes_85[total][trip_time])  # append all days

            if new_runtimes:
                avg_val = math.ceil(sum(new_runtimes) / len(new_runtimes))
                agg[total] = avg_val
                print(f"  → Avg across {len(new_runtimes)} values for {total}: {avg_val}")

        agg["total"] = sum(agg.values())
        print(f"  → Total runtime for timeband: {agg['total']}")
        suggested.append(((tb_start, tb_end), agg))       
    return suggested

def sched_end_to_end_runtimes(route, start, end, dow, direction,variant_trips=0):
    print("END TO END RUNTIMES")
    # === STEP 1: Build "skeleton" timebands using default (60th percentile) ===
    print("\n=== STEP 1: Build skeleton timebands with default (60th) percentile ===")
    base_route_stats = get_route_stats(route, 60, start, end, dow, direction)
    if variant_trips:
        filter_diff_variants(base_route_stats, variant_trips, "routeStats.json")
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(base_route_stats)

    grouped_timebands = percentiles_test.group_timebands(schedule_runtimes, 1) # groups trips if runtimes are within threshold
    new_timebands = percentiles_test.make_timebands(grouped_timebands) # consolidate grouped trips into new timebands

    base_route_stats = get_route_stats(route, 90, start, end, dow, direction)
    if variant_trips:
        filter_diff_variants(base_route_stats, variant_trips, "routeStats.json")
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(base_route_stats)

    # === STEP 2: Run end-to-end percentile runtimes per trip ===
    print("\n=== STEP 2: Run end-to-end percentile runtimes per trip ===")
    runtimes_85 = {"total": {}}
    for trip_time, stops in schedule_runtimes.items():
        runtimes_85["total"][trip_time] = stops["total"]

    # === STEP 3: Aggregate runtimes per timeband ===
    print("\n=== STEP 3: Aggregate runtimes per timeband ===")

    suggested = []
    for j, (timeband_range, _) in enumerate(new_timebands):
        tb_start, tb_end = timeband_range
        agg = {}
        print(f"\nTimeband {tb_start} - {tb_end}")

        # For each timepoint, look at all trips inside this timeband group
        for total in runtimes_85:
            new_runtimes = []

            for trip_time, _ in grouped_timebands[j]:
                if trip_time in runtimes_85[total]:
                    new_runtimes.append(runtimes_85[total][trip_time])  # append all days

            if new_runtimes:
                avg_val = math.ceil(sum(new_runtimes) / len(new_runtimes))
                agg[total] = avg_val
                print(f"  → Avg across {len(new_runtimes)} values for {total}: {avg_val}")

        agg["total"] = sum(agg.values())
        print(f"  → Total runtime for timeband: {agg['total']}")
        suggested.append(((tb_start, tb_end), agg))   
    
    return suggested
 
"""
    Build suggested runtimes for each timeband, using custom percentiles per timepoint.

    Args:
        route (int): The route ID
        percentiles (list[int]): List of percentiles, one per timepoint
        start, end (str): Date range
        dow (list): Days of week to filter
        timepoints (list): Timepoints for runtimes to be ran at
        t (int): Type of runtime; t=0 for percentile, 1 for scheduled

    Returns:
        list: Suggested runtimes per new timeband in the form:
              [((start_time, end_time), {timepoint: avg_runtime, ..., "total": total})]
    """   
def suggested_runtimes(route, percentiles, start, end, dow, direction, timepoints, t=0, variant_trips=0):
    # Parse input dates (MM-DD-YYYY)
    start_dt = datetime.strptime(start, "%m-%d-%Y")
    end_dt = datetime.strptime(end, "%m-%d-%Y")

    # === STEP 1: Build "skeleton" timebands using default (60th percentile) ===
    print("\n=== STEP 1: Build skeleton timebands with default (60th) percentile ===")
    base_route_stats = get_route_stats(route, 60, start, end, dow, direction)
    if variant_trips:
        filter_diff_variants(base_route_stats, variant_trips, "routeStats.json")
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(base_route_stats)
    grouped_timebands = percentiles_test.group_timebands(percentile_runtimes,3) # groups trips if runtimes are within threshold
    new_timebands = percentiles_test.make_timebands(grouped_timebands) # consolidate grouped trips into new timebands

    # checking what it would look like if you ran this w/ scheduled runtimes
    # percentile_runtimes = schedule_runtimes # be careful
    runtimes = percentile_runtimes if t==0 else schedule_runtimes
    
    '''
    I NEED TO FIX THIS TO TAKE IN THE VARIANT NEEDED TO RUN!!!! Pass in timepoints object? MAKES THINGS SM EASIER
    '''
    # === STEP 2: Extract timepoint names from the first trip ===
    print("\n=== STEP 2: Extract timepoint names ===")
    print("Timepoints:", timepoints)
    print("Percentiles:", percentiles)
    
    # === STEP 3: Re-run stats for each timepoint at its assigned percentile ===
    print("\n=== STEP 3: Re-run stats for each timepoint at its assigned percentile ===")
    # Nested dict: {tp: {trip_time: [list of runtimes across days]}}
    per_timepoint_runtimes = {tp: {} for tp in timepoints}

    for i, p in enumerate(percentiles):
        tp = timepoints[i]
        print(f"\n-- Collecting runtimes for timepoint '{tp}' at percentile {p} --")

        route_stats = get_route_stats(route, p, start, end, dow, direction) 
        if variant_trips:
            filter_diff_variants(base_route_stats, variant_trips, "routeStats.json")
        if t==0:
            runtimes, _ = percentiles_test.runtime_per_trip(route_stats)
        else: 
            _, runtimes = percentiles_test.runtime_per_trip(route_stats)

        # Fill per_timepoint_runtimes with runtimes for this stop at this percentile
        for trip_time, stops in runtimes.items():
            # try matching by stop name first
            value = stops.get(tp)
            # # If name-based lookup fails, fall back to position-based
            if value is None:
                continue
            per_timepoint_runtimes[tp][trip_time] = value

    # === STEP 4: Aggregate runtimes per timeband ===
    print("\n=== STEP 4: Aggregate runtimes per timeband ===")
    suggested = []
    for j, (timeband_range, _) in enumerate(new_timebands):
        tb_start, tb_end = timeband_range
        agg = {}
        print(f"\nTimeband {tb_start} - {tb_end}")
        # For each timepoint, look at all trips inside this timeband group
        for tp in timepoints:
            new_runtimes = []
            print(f"  Timepoint {tp}:")
            for trip_time, _ in grouped_timebands[j]:
                if trip_time in per_timepoint_runtimes[tp]:
                    new_runtimes.append(per_timepoint_runtimes[tp][trip_time])  # append all days

            if new_runtimes:
                avg_val = math.ceil(sum(new_runtimes) / len(new_runtimes))
                agg[tp] = avg_val
                print(f"  → Avg across {len(new_runtimes)} values for {tp}: {avg_val}")

        agg["total"] = sum(agg.values())
        print(f"  → Total runtime for timeband: {agg['total']}")
        suggested.append(((tb_start, tb_end), agg))   
    
    # === FINAL OUTPUT ===
    print("\n=== FINAL SUGGESTED RUNTIMES ===")
    for tb in suggested:
        print(tb)

    return suggested

def get_end_to_end_diff(end_to_end, suggested):
    differences = []
    for ((start_s, end_s), sugg_data), ((start_e, end_e), end_data) in zip(suggested, end_to_end):
        sugg_total = sugg_data.get("total", 0)
        end_total = end_data.get("total", 0)
        diff = end_total - sugg_total
        differences.append(((start_s, end_s), {"total": diff}))
    return differences

def filter_diff_variants(route_stats, variant_trips, file_path="routeStats.json"):
    """
    Filters a routeStats JSON object to only include trips whose
    scheduledTripStartTime is in variant_trips.

    Args:
        route_stats (dict): The routeStats JSON object (from get_route_stats()).
        variant_trips (list): List of scheduledTripStartTime strings to keep.
        file_path (str): Path to overwrite the JSON file (default: 'routeStats.json').

    Returns:
        dict: Filtered routeStats object.
    """
    if not variant_trips:
        raise ValueError("You must provide a list of variant_trips to keep.")
    if not isinstance(route_stats, dict):
        raise TypeError("route_stats must be a dictionary (parsed JSON object).")

    # Filter the pathStats list
    filtered_pathStats = [
        path for path in route_stats.get("pathStats", [])
        if path.get("scheduledTripStartTime") in variant_trips
    ]
    route_stats["pathStats"] = filtered_pathStats

    # Overwrite file if the file exists
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(route_stats, f, indent=2, ensure_ascii=False)
        print(f"✅ {file_path} updated: kept {len(filtered_pathStats)} trips.")

    return route_stats

    
if __name__ == "__main__":
    def_start, def_end = "09-11-2025", "10-20-2025"
    wd, we = "1,2,3,4,5", "6,7"

    date_presets = {
        "ds": def_start,
        "de": def_end,
    }

    dow_presets = {
        "default_wd": wd,
        "default_we": we,
    }

    # Ask for start & end date
    raw_dates = input(
        f"* Start date and end date\n"
        f"** Format: MM-DD-YYYY MM-DD-YYYY\n"
        f"Press Enter for default ({def_start} to {def_end}), "
        f"or use 'ds' / 'de': "
    ).strip()

    # Ask for start and end date to compare it to
    compare_dates = input(
        f"* Comparing: Start date and end date\n"
        f"** Format: MM-DD-YYYY MM-DD-YYYY\n"
        f"Press Enter for default ({def_start} to {def_end}), "
        f"or use 'ds' / 'de': "
    ).strip()

    if compare_dates:
        comp_start, comp_end = compare_dates.split()
        # Replace presets if typed
        comp_start = date_presets.get(comp_start, comp_start)
        comp_end   = date_presets.get(comp_end, comp_end)
    else:
        comp_start, comp_end = def_start, def_end

    if raw_dates:
        start_date, end_date = raw_dates.split()
        # Replace presets if typed
        start_date = date_presets.get(start_date, start_date)
        end_date   = date_presets.get(end_date, end_date)
    else:
        # Blank input → full defaults
        start_date, end_date = def_start, def_end

    # Ask for days of week
    days_of_week = input(
        f"* Day of week\n"
        f"** Format: '1,2,3,4,5,6,7'\n"
        f"Press Enter for default (weekday={wd}), "
        f"or type 'wd' / 'we': "
    ).strip()

    if days_of_week:
        days_of_week = dow_presets.get(days_of_week, days_of_week)
    else:
        # Blank input → default weekdays
        days_of_week = wd

    route = input("* Route: ")
    direction = input("* Direction (0=outbound, 1=inbound): ")

    fixed_route_stats = get_route_stats(route, 60, start_date, end_date, days_of_week, direction)
    runtimes, _ = percentiles_test.runtime_per_trip(fixed_route_stats) # groups into arrows

    # identify all unique variants in a list, based on diff timepoints (even if # timepoints is the same)
    timepoint_sets = []
    for trip_time, stops in runtimes.items():
        stop_list = [s for s in stops if s != "total"]
        if stop_list not in timepoint_sets:
            timepoint_sets.append(stop_list)
    
    timepoint_groups = defaultdict(list)
    for trip_time, stops in runtimes.items():
        stop_list = tuple([s for s in stops if s != "total"])  # tuples can be dict keys
        timepoint_groups[stop_list].append(trip_time)
    timepoint_groups = list(timepoint_groups.items())
    
    variant_trips=0
    variant_name = "Base Variant"
    # if multiple variants
    if len(timepoint_sets) > 1:
        print("Route has multiple variants.")
        for i, stops in enumerate(timepoint_sets, start=1):
            print(f"\nOption {i}:")
            for stop in list(stops):
                print(stop)
        variant = int(input("\nWhich variant would you like to run? ")) - 1
        timepoints = timepoint_sets[variant]
        length = len(timepoints)
        print(f"tp sets:\n{timepoints}\ntp groups:\n{timepoint_groups[variant]}")
        variant_tps, variant_trips = timepoint_groups[variant]
        print(variant_trips)
        variant_name = f"Variant {variant+1}:"
    else:
        length, timepoints = get_num_timepoints(route, start_date, end_date, days_of_week, direction)
    

    print(f"\n> Route {route} has {length} timepoints for dates {start_date} to {end_date}:")
    for tp in timepoints:
        print(">> ", tp)
    if length == 0:
        raise ValueError("Timepoint calculation failed; route has 0 timepoints")
    df_pct = np.ceil(np.linspace(30, 60, length)).astype(int).tolist()
    percentiles = input(f"\n* List the percentiles you'd like each timepoint to be ran at.\n** Format: 30,40,50 or press enter for default {df_pct}: ")
    if percentiles:
        percentiles = [int(x.strip()) for x in percentiles.split(",")]
    else:
        # Blank input → default weekdays
        percentiles = df_pct
    
    dow = "wd"
    if days_of_week == we:
        dow = "we"        
    elif days_of_week == "2,4":
        dow="TTH"
    elif days_of_week == "1,3,5":
        dow = 'MWF'
    
    filename = f"route_{route}_{dow}_suggested_runtimes.xlsx"
    # Check if workbook exists; otherwise create new
    if os.path.exists(filename):
        wb = load_workbook(filename)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
    
    ws.append([f"Dates ran for: {start_date} to {end_date}"])

    if direction == "0":
        ws.append(["Outbound"])
    else:
        ws.append(["Inbound"])
    ws.append([variant_name])
    wb.save(filename)
    print(variant_trips)
    suggested = suggested_runtimes(route, percentiles, start_date, end_date, days_of_week, direction, timepoints,0,variant_trips)
    scheduled = suggested_runtimes(route, percentiles, start_date, end_date, days_of_week, direction, timepoints, 1,variant_trips)
    # print(suggested)
    diff_data = diff_runtimes(suggested, scheduled)
    end_to_end = end_to_end_runtimes(route, start_date, end_date, days_of_week, direction,variant_trips)
    diff_e2e_sugg = get_end_to_end_diff(end_to_end, suggested)
    base_timebands = sched_end_to_end_runtimes(route, comp_start, comp_end, days_of_week, direction, variant_trips)

    # print("suggested:\n", suggested, "\nend_to_end:\n", end_to_end, "\ne2e diff:\n", diff_e2e_sugg)

    runtimes_to_csv.runtimes_to_excel(suggested, route, filename,label="Suggested Runtimes",percentiles=percentiles,write_header=True)
    runtimes_to_csv.runtimes_to_excel(scheduled, route, filename,label="Scheduled Runtimes", write_header=False,add_blank_row=True)
    runtimes_to_csv.runtimes_to_excel(diff_data, route, filename,label="Diff: Suggested - Scheduled",write_header=False,add_blank_row=True)
    runtimes_to_csv.runtimes_to_excel(end_to_end, route, filename,label="End to End 85th percentile runtime",write_header=False,add_blank_row=True)
    runtimes_to_csv.runtimes_to_excel(diff_e2e_sugg, route, filename,label="Diff 85th - Suggested (Minimum layover)",write_header=False,add_blank_row=True)
    runtimes_to_csv.runtimes_to_excel(base_timebands, route, filename,label="Fall End to End Runtimes (HASTUS)",write_header=False,add_blank_row=True)
