# GetSwift Codetest

import requests
import json
import time
from haversine import haversine

# Co-ordinates of the depot from Google Maps
DEPO_LAT = -37.816664
DEPO_LONG = 144.963848
SECONDS_IN_HOUR = 3600
SPEED_OF_DRONE = 50

class Package:
    def __init__(self, pid, deadline, dest_lat, dest_long):
        self.pid = pid
        self.deadline = deadline
        self.dest_lat = dest_lat
        self.dest_long = dest_long

    # So we can sort a list of package objects using their deadlines
    def __cmp__(self, other):
        return cmp(self.deadline, other.deadline)

class Drone:
    def __init__(self, did, lat, long, dest_lat, dest_long):
        self.did = did
        self.lat = lat
        self.long = long
        self.dest_lat = dest_lat
        self.dest_long = dest_long
        self.dist = haversine((self.lat, self.long), (self.dest_lat, self.dest_long))
        # If (drone is already assigned a package)
        if dest_lat != DEPO_LAT:
            self.dist = self.dist + haversine((DEPO_LAT, DEPO_LONG), (self.dest_lat, self.dest_long))

    # So we can sort a list of drone objects based on their total travel distance to the depot
    def __cmp__(self, other):
        return cmp(self.dist, other.dist)

def is_valid_assignment(package, drone):
    current_time = int(time.time())
    needed_time = ((haversine((package.dest_lat, package.dest_long), (DEPO_LAT, DEPO_LONG)) + drone.dist)/SPEED_OF_DRONE ) * SECONDS_IN_HOUR

    # If (drone can service package by package's deadline)
    if (current_time + needed_time) <= package.deadline:
        return True
    else:
        return False

# GETS /drones, creates and returns a priority queue of drones
def queue_drones():
    url = 'https://codetest.kube.getswift.co/drones'
    drones = []
    resp = requests.get(url=url, params='')
    data = json.loads(resp.text)
    for i in data:
        dest_lat = DEPO_LAT
        dest_long = DEPO_LONG
        if i.get("packages"):
            dest_lat = i["packages"][0]["destination"]["latitude"]
            dest_long = i["packages"][0]["destination"]["longitude"]
        drones.append(Drone( i["droneId"], i["location"]["latitude"], i["location"]["longitude"], dest_lat, dest_long ))
    return sorted(drones)

# GETS /packages, creates and returns a priority queue of packages
def queue_packages():
    url = 'https://codetest.kube.getswift.co/packages'
    packages = []
    resp = requests.get(url=url, params='')
    data = json.loads(resp.text)
    for i in data:
        packages.append(Package( i["packageId"], int(i["deadline"]), i["destination"]["latitude"], i["destination"]["longitude"] ))
    return sorted(packages)

assigned = []
unassigned = [] 
packages = queue_packages()
drones = queue_drones()

# Iterate over packages and assign them to a drone if possible
for package in packages:
    if drones and is_valid_assignment(package, drones[0]):
        assigned.append( {"droneId": drones[0].did, "packageId": package.pid} )
        del drones[0]
    else:
        unassigned.append(package.pid)

print json.dumps({"assignments": assigned, "unassignedPackageIds": unassigned})
