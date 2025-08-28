import http.client
import csv
import json

def call(endpoint="path-stats", route=11, percentile=60):
    conn = http.client.HTTPSConnection("api.goswift.ly")

    headers = {
        'Accept': "application/json, text/csv; charset=utf-8, */*",
        'Authorization': "52d1916b5d1221ed54267b01e6a47de5"
    }

    if endpoint == "path-stats":
        conn.request("GET", f"/run-times/santa-cruz/{endpoint}?routes={route}&additionalGroupBy=SCHEDULED_TRIP_START_TIME,SCHEDULED_RUN_TIME&aggregationTypes=PERCENTILE&aggregationFields=RUN_TIME&listAggregations=SCHEDULED_RUN_TIME&percentiles={percentile}&groupByTimepoint=true&startDate=03-13-2025&endDate=06-18-2025&daysOfWeek=1,2,3,4,5", headers=headers)

    res = conn.getresponse()
    data = res.read()
    
    # parse string
    percentiles = json.loads(data)
    
    return percentiles

if __name__ == "__main__":
    print(call('path-stats', 11))

