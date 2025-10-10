# puts api call response into a json file called "routeStats.json".

import http.client 
import json
import math
import api_request

def txt_convert(filename, route_stats):

    # modify JSON in place
    for path in route_stats["pathStats"]:
        # scheduled runtime is nested in aggregates[0]
        scheduled_seconds = float(path["aggregates"][0]["value"][0])
        scheduled_minutes = math.ceil(scheduled_seconds / 60)

        path["scheduledRuntimeMinutes"] = scheduled_minutes

    # write back to file as raw JSON
    with open(filename, "w") as f:
        json.dump(route_stats, f, indent=2)
    
    f.close()

if __name__ == "__main__":
    route_stats = api_request.call('path-stats', 11)
    txt_convert('routeStats.json', route_stats)
