import http.client
import json


def run_all_routes(endpoint="all-routes"):

    conn = http.client.HTTPSConnection("api.goswift.ly")

    headers = {
        'Accept': "application/json, */*",
        'Authorization': "52d1916b5d1221ed54267b01e6a47de5"
    }

    conn.request("GET", "/run-times/santa-cruz/all-routes/by-trip?startDate=03-13-2025&endDate=06-18-2025&daysOfWeek=1%2C2%2C3%2C4%2C5", headers=headers)

    res = conn.getresponse()
    data = res.read()
    
    # parse string
    all_routes_sum = json.loads(data)
    
    return all_routes_sum

def get_all_routes(all_routes_sum):
    all_routes = []
    
    # for a in all_routes_sum['data']:
    #     for e in a.keys():
    #         if e == 'routeShortName':
    #             all_routes.append(a[e])
    
    # comprehension
    # extract all of our agency's routes from the "all-routes" endpoint
    all_routes += [a[e] for a in all_routes_sum['data'] for e in a.keys() if e == 'routeShortName']


if __name__ == "__main__":
    all_routes_sum = run_all_routes()
    get_all_routes(all_routes_sum)