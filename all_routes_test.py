import http.client
import json


def run_all_routes(start_date="03-13-2025", end_date="06-18-2025", days_of_week="1,2,3,4,5"):

    conn = http.client.HTTPSConnection("api.goswift.ly")

    headers = {
        'Accept': "application/json, */*",
        'Authorization': "52d1916b5d1221ed54267b01e6a47de5"
    }

    conn.request("GET", f"/run-times/santa-cruz/all-routes/by-trip?startDate={start_date}&endDate={end_date}&daysOfWeek=1%2C2%2C3%2C4%2C5", headers=headers)

    res = conn.getresponse()
    data = res.read()
    
    # parse string
    all_routes_sum = json.loads(data)
    
    return all_routes_sum

# extract all of our agency's routes from the "all-routes" endpoint
def get_all_routes(all_routes_sum):
    all_routes = []
    
    # comprehension - goes through list then dict i think
    all_routes += [a[e] for a in all_routes_sum['data'] for e in a.keys() if e == 'routeShortName']
    
    return all_routes


if __name__ == "__main__":
    # start date and end date!
    all_routes_sum = run_all_routes()
    get_all_routes(all_routes_sum)