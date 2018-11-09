import heapq

try:
    from .error_message import moov_errors
    from .common_helper import get_distance
except ImportError:
    from moov_backend.api.helper.error_message import moov_errors
    from moov_backend.api.helper.common_helper import get_distance

# get the nearest or furthest drivers
def get_nearest_or_furthest_drivers(driver_list, user_latitude, user_longitude,
number_of_drivers=2, operation="nearest"):
    drivers = []
    driver_distance = None
    get_driver_distances = [{"driver": driver,
                             "distance": get_distance(
                                            driver.destination_latitude,
                                            driver.destination_longitude,
                                            user_latitude,
                                            user_longitude,
                                            "k")} \
                                for driver in driver_list]
    distance_list = [driver["distance"] for driver in get_driver_distances]

    if operation.lower() == "furthest":
        driver_distance = heapq.nlargest(number_of_drivers, distance_list)
    
    if operation.lower() == "nearest":
        driver_distance = heapq.nsmallest(number_of_drivers, distance_list)

    return [driver["driver"] \
            for driver in get_driver_distances \
            if driver["distance"] in driver_distance]
    