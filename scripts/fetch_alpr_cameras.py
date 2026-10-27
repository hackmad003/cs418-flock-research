#!/usr/bin/env python3
"""
##############################
# OSM ALPR Cameras (primary) #
##############################

# Pull ALPR (Automated License Plate Reader) camera locations from OpenStreetMap via the Overpass API. 
# This is the same data source DeFlock/antiflock.org use # Verify this
# OSM nodes tagged surveillance:type=ALPR.

Example User Usage:
    python fetch_alpr_cameras.py --state Illinois
    python fetch_alpr_cameras.py --state Illinois --out illinois_alpr.geojson
    python fetch_alpr_cameras.py --bbox 41.6,-87.9,42.1,-87.5   # south,west,north,east
    python fetch_alpr_cameras.py --place "Orland Park, Illinois"  # geocoded via Nominatim
    python fetch_alpr_cameras.py --nationwide                   # all of the US (slow, large) # explore parallel pipeline for increase speed up.

Requires: pip install requests
SO This is a uv project (it has a uv.lock), so don't edit the file by hand. Run:
Requires: uv sync, since that command installs everything in the .toml.

In the Future use uv add package that will:
    add package to dependencies listed in .toml
    Update uv.lock with that exact version
    Install it into your .venv

VVV Sources VVV
https://wiki.openstreetmap.org/wiki/Overpass_API
https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL
https://wiki.openstreetmap.org/wiki/Tag:surveillance:type%3DALPR
https://nominatim.org/release-docs/latest/api/Search/
https://operations.osmfoundation.org/policies/nominatim/
https://datatracker.ietf.org/doc/html/rfc7946 (GeoJSON format)
https://deflock.me

Imports Used:
import argparse # https://docs.python.org/3/library/argparse.html
import json # https://docs.python.org/3/library/json.html
import sys # https://docs.python.org/3/library/sys.html
import time # https://docs.python.org/3/library/time.html
import requests # https://requests.readthedocs.io/en/latest/

Built-In Functions Used:
print() https://docs.python.org/3/library/functions.html#print
len() https://docs.python.org/3/library/functions.html#len
float() https://docs.python.org/3/library/functions.html#float
open() https://docs.python.org/3/library/functions.html#open
RuntimeError https://docs.python.org/3/library/exceptions.html#RuntimeError
Exception https://docs.python.org/3/library/exceptions.html#Exception

Object Methods Used:
requests.get() https://requests.readthedocs.io/en/latest/api/#requests.get
.raise_for_status() https://requests.readthedocs.io/en/latest/api/#requests.Response.raise_for_status
requests.post() https://requests.readthedocs.io/en/latest/api/#requests.post
.json() (response) https://requests.readthedocs.io/en/latest/api/#requests.Response.json
argparse.ArgumentParser() https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser
.add_argument() https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument
.parse_args() https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.parse_args
.add_mutually_exclusive_group() https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_mutually_exclusive_group
json.dump() https://docs.python.org/3/library/json.html#json.dump
time.sleep() https://docs.python.org/3/library/time.html#time.sleep
sys.exit() https://docs.python.org/3/library/sys.html#sys.exit
.get() (dict) https://docs.python.org/3/library/stdtypes.html#dict.get
.append() https://docs.python.org/3/tutorial/datastructures.html#more-on-lists
.lower() https://docs.python.org/3/library/stdtypes.html#str.lower
.replace() https://docs.python.org/3/library/stdtypes.html#str.replace
.split(",") https://docs.python.org/3/library/stdtypes.html#str.split

Data Structures / Techniques Used:
dict (HEADERS, the GeoJSON feature) https://docs.python.org/3/tutorial/datastructures.html#dictionaries
list (ENDPOINTS, features = []) https://docs.python.org/3/tutorial/datastructures.html#more-on-lists
f-strings (f"...{x}") https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals
tuple unpacking (min_lat, max_lat, ... = ...) https://docs.python.org/3/tutorial/datastructures.html#tuples-and-sequences
generator expression ((float(x) for x in ...)) https://docs.python.org/3/reference/expressions.html#generator-expressions
list comprehension ([float(x) for x in ...]) https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions
* argument unpacking (build_query_by_bbox(*parts)) https://docs.python.org/3/tutorial/controlflow.html#unpacking-argument-lists
try / except (server fallback) https://docs.python.org/3/tutorial/errors.html#handling-exceptions
with open(...) as f: https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files
type hints (-> str, -> dict) https://docs.python.org/3/library/typing.html
if __name__ == "__main__": https://docs.python.org/3/library/__main__.html
User-Agent header https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/User-Agent
"""

###########
# IMPORTS #
###########
import argparse # https://docs.python.org/3/library/argparse.html
# reads command line arguments

import json # https://docs.python.org/3/library/json.html
# converts between JSON text and dicts

import sys # https://docs.python.org/3/library/sys.html#module-sys
# used for sys.exit()

import time # https://docs.python.org/3/library/time.html#module-time
#used for sys.sleep()

import requests # https://pypi.org/project/requests/
# sends HTTP requests to websites and APIs



#############
# ENDPOINTS #
#############
"""
# A list of Overpass API server URLs, 
"""
ENDPOINTS = [
    "https://overpass.deflock.org/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
#


###########
# HEADERS #
###########
"""
Overpass operators ask that the User-Agent include a way to contact you, like.
Adding one makes it less likely your requests get blocked.
"""
HEADERS = {
    "User-Agent": 
    "CS418-flock-research-project/1.0 (student research, non-commercial)"
}

#################
# NOMINATIM_URL #
#################
"""
the web address of Nominatim, OpenStreetMap's free "geocoder".
A geocoder turns a place NAME ("Orland Park, Illinois") into map
COORDINATES (latitude/longitude). It's a different service from Overpass:
Nominatim answers "where is this place?"
Overpass answers "what's tagged inside this area?"
"""
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"




#################
# GEOCODE_PLACE #
#################
def geocode_place(place_name: str):
    """
    Look up a place name via Nominatim (OSM's geocoder) and return a bbox
    tuple in (south, west, north, east) order -- the order this script's
    Overpass queries expect.

    Nominatim itself returns boundingbox as [min_lat, max_lat, min_lon, max_lon]
    i.e. [south, north, west, east] -- note the different order -- so this
    function does the reordering for you.
    """
    # Show what we're looking up.
    print(f"  geocoding '{place_name}' via Nominatim...")

    # Send a GET request to Nominatim. (GET = "ask for data". 
    # run_query() uses POST instead because Overpass queries can be long.)
    # params= adds these to the end of the URL as ?q=...&format=json&limit=1
    #   - "q": the place we're searching for
    #   - "format": "json": send the answer back as JSON
    #   - "limit": 1: only give us the single best match
    # headers=HEADERS: our User-Agent. Nominatim REQUIRES one and blocks
    #   requests without it.
    # timeout=15: give up after 15 seconds (a lookup is much faster than an
    #   Overpass query, so we don't need 180).
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": place_name, "format": "json", "limit": 1},
        headers=HEADERS,
        timeout=15,
    )

    # If the server sent back an error code, stop here with an exception.
    resp.raise_for_status()

    # Turn the response into Python. Nominatim returns a LIST of matches.
    results = resp.json()

    # An empty list means Nominatim didn't recognize the place
    # (e.g. a typo). Stop with a clear error message.
    if not results:
        raise RuntimeError(f"Nominatim found no match for '{place_name}'")

    # Take the first (best) match from the list.
    result = results[0]

    # result["boundingbox"] is a list of 4 STRINGS, like
    # ["41.57", "41.66", "-87.91", "-87.80"].
    # float(x) converts each one to a number, and the 4 numbers are
    # "unpacked" into 4 variables in the order Nominatim uses:
    # min_lat (south), max_lat (north), min_lon (west), max_lon (east).
    min_lat, max_lat, min_lon, max_lon = (float(x) for x in result["boundingbox"])

    # Show which place was matched, so you can check it found the right one
    # (for example, the Springfield in Illinois and not the one in Missouri).
    print(f"  matched: {result['display_name']}")
    print(f"  bbox (south,west,north,east): {min_lat},{min_lon},{max_lat},{max_lon}")

    # Nominatim's rules allow at most 1 request per second, so wait
    # 1 second to be polite.
    time.sleep(1)

    # IMPORTANT: return the numbers REORDERED to south, west, north, east,
    # which is the order build_query_by_bbox() expects.
    # Nominatim order: south, north, west, east
    # Overpass order:  south, west, north, east
    return min_lat, min_lon, max_lat, max_lon



########################
# BUILD_QUERY_BY_STATE #
########################
def build_query_by_state(state_name: str, timeout: int = 60) -> str:
    """
    Build the Overpass query text that searches one US state for ALPR cameras.
    "state_name: str" means the state name is text, like "Illinois".
    timeout defaults to 60 seconds if you don't pass one.
    "-> str" means the function returns text.   
    """

    """
    [out:json][timeout:{timeout}];
       -> Send the results back as JSON, and let the server work for up to
          "timeout" seconds before it gives up.
    
    area["name"="{state_name}"]["admin_level"="4"]->.searchArea;
       -> Find the area whose name matches the state. admin_level=4 means
          a state or province border in OpenStreetMap (admin_level=2 is a
          country). "->.searchArea" saves this area under the name
          "searchArea" so later lines can use it.
    
    ();
       -> The parentheses combine the results of every line inside them
          into one set (a "union").
    
    node["surveillance:type"="ALPR"](area.searchArea);
       -> Find every point (node) tagged as an ALPR camera inside the state.
    
    node["man_made"="surveillance"]["surveillance:type"="ALPR"](area.searchArea);
       -> Find points tagged BOTH as a surveillance object AND as ALPR.
          (This line finds nothing new: anything it matches is already
          matched by the line above.)
    
    out meta;
       -> Output each camera's ID, location, and tags, PLUS "meta": when it was
          last edited (timestamp) and its version number. Needed for Q1.
    """
    
    return f"""
    [out:json][timeout:{timeout}];
    area["name"="{state_name}"]["admin_level"="4"]->.searchArea;
    (
      node["surveillance:type"="ALPR"](area.searchArea);
      node["man_made"="surveillance"]["surveillance:type"="ALPR"](area.searchArea);
    );
    out meta;
    """



#######################
# BUILD_QUERY_BY_BBOX #
#######################
def build_query_by_bbox(south, west, north, east, timeout: int = 60) -> str:
    """
    Build the Overpass query text that search a rectangle on the map
    a bounding box for ALPR cameras
    south, west, north, easy are the 4 edges of the rectangle, as decimal
    lat/lon numbers
    """

    bbox = f"{south},{west},{north},{east}" # Overpass wants order: s, w, n, e

    """
    Return the query as an f-string written in Overpass QL.
    
    [out:json][timeout:{timeout}];
       -> Send the results back as JSON, and let the server work for up to
          "timeout" seconds before it gives up.
    
    ( ... );
      -> The parentheses combine the results of every line inside them
          into one set.
    
    node["surveillance:type"="ALPR"]({bbox});
       -> Find every point (node) tagged as an ALPR camera inside the box.
          Putting ({bbox}) after a search limits it to that rectangle.
    
    node["man_made"="surveillance"]["surveillance:type"="ALPR"]({bbox});
       -> Find points tagged BOTH as a surveillance object AND as ALPR.
          (This line finds nothing new: anything it matches is already
          matched by the line above.)
    
    out meta;
       -> Output each camera's ID, location, and tags, PLUS "meta": when it was
          last edited (timestamp) and its version number. Needed for Q1.
    """
    
    return f"""
    [out:json][timeout:{timeout}];
    (
      node["surveillance:type"="ALPR"]({bbox});
      node["man_made"="surveillance"]["surveillance:type"="ALPR"]({bbox});
    );
    out meta;
    """


##########################
# BUILD_QUERY_NATIONWIDE #
##########################
def build_query_nationwide(timeout: int = 180) -> str:
    """
    Build the Overpass query text that searches the entire
    US for ALPR cameras.
    timeout int = 180 
    "-> str" function returns text
    """

    """
    This returns an f-string written in Overpass QL, the query language
    the Overpass API uses. 

    [out:json][timeout:{timeout}]; # Send the results back as JSON, and let server work until timeout seconds

    area["name"="United States"]["admin_level"="2"]->.searchArea; # Find US, admin_level means country border in OSM

    () parentheses combine results of every line into one set

    node["surveillance:type"="ALPR"](area.searchArea);
       -> Find every point (node) tagged as an ALPR camera
          inside the United States area.
    
    node["man_made"="surveillance"]["surveillance:type"="ALPR"](area.searchArea);
       -> Find points tagged BOTH as a surveillance object AND as ALPR.
          (This line finds nothing new: anything it matches is already
          matched by the line above.)
    
    out meta;
       -> Output each camera's ID, location, and tags, PLUS "meta": when it was
          last edited (timestamp) and its version number. Needed for Q1.
    
    """
    
    return f"""
    [out:json][timeout:{timeout}]; 
    
    area["name"="United States"]["admin_level"="2"]->.searchArea;
    
    (
      node["surveillance:type"="ALPR"](area.searchArea);
      node["man_made"="surveillance"]["surveillance:type"="ALPR"](area.searchArea);
    );
    
    out meta;
    """



#############
# RUN_QUERY #
#############
def run_query(query: str) -> dict:
    """
    Send a query to the Overpass API and return the results.
    query: str means the input is text and "-> dict" means the function
    returns a dictionary (the JSON data the server sends back)
    """
    last_err = None # Keep track of errors

    # ENDPOINTS is a list of Overpass server URLs, try one at a time
    for endpoint in ENDPOINTS:
 
        try:
            print(f"  trying {endpoint} ...") # show which server the loop is on 

            # Send a POST request (a way of sending data to a web server)
            # - data={"data": query}: Overpass expects the query in a field called "data"
            # - headers=HEADERS: extra info sent with the request, like who we are
            #   (defined earlier in the file)
            # - timeout=180: give up if the server takes longer than 180 seconds
            resp = requests.post( 
                endpoint, data={"data": query}, headers=HEADERS, timeout=180
            )

            resp.raise_for_status() # Defense Prog
            
            return resp.json() # Success, return response text into dict and return
        except Exception as e:

            print(f"  failed ({e}), trying next endpoint...")

            last_err = e # save error

            time.sleep(2) # wait before trying next server

    # Err Defense Prog
    raise RuntimeError(f"All Overpass endpoints failed. Last error: {last_err}")




##############
# TO_GEOJSON #
##############
def to_geojson(overpass_json: dict) -> dict:
    """
    convert the raw overpass api results into geojson
    a standard map format.
    "overpas_json: dict" means the input should be a dictionary, 
    and "-> dict" means the function also returns a dictionary.
    """
    features = [] # Empty list, We'll add one features (one map point) per camera

    # go through each item overpass returned 
    for el in overpass_json.get("elements", []): # if "elements" is missing loop doesnt run

        # OpenStreetMap has 3 kinds of items: nodes (single points), ways
        # (lines/shapes), and relations (groups). A camera is a single point,
        # so we skip anything that isn't a node.
        if el.get("type") != "node":
            continue 

        # Tags are the labels people add in OSM, like 
        # {"operator": "Flock Safety"}.
        # default is empty dict if this camera has no tags
        tags = el.get("tags", {}) 

        # Build one GeoJSON "Feature" for this camera and add it to the list.        
        features.append(
            {
                "type": "Feature",                          # Every GeoJSON feature needs "type": "Features"
                "geometry": {                               # "geometry" says Where the camera is on the map
                    "type": "Point",                        # a camera is a single location, so it's a "Point"
                    "coordinates": [el["lon"], el["lat"]],  # GeoJSON wants [lon, lat]. reverse the usual [lat, lon] order
                },
                # "properties" holds extra information about the camera.
                # tags.get(...) returns None if a tag is missing
                # code doesn't crash when a camera is only partly labeled.
                "properties": {
                    "osm_id": el.get("id"),                                             # Camera's UID # in OpenStreetMap
                    "operator": tags.get("operator"),                                   # Who runs the camera
                    "manufacturer": tags.get("manufacturer") or tags.get("brand"),      # some mappers use manufacturer or brand
                    "direction": tags.get("camera:direction") or tags.get("direction"), # some mappers use two notations
                    "surveillance_type": tags.get("surveillance:type"),                 # The kind of surveillance (ALPR)
                    "man_made": tags.get("man_made"),                                   # Man_Made
                    # From "out meta" (Q1). timestamp = LAST edit, not creation.
                    # If version == 1 the camera was never edited, so timestamp = when it was first added.
                    "timestamp": el.get("timestamp"),                                   # e.g. "2025-03-14T18:22:05Z"
                    "version": el.get("version"),                                       # 1 = never edited since added
                    "all_tags": tags,                                                   
                    # Keep every original tag too, in case we need one we didnt pull out above
                },
            }
        )

    # Wrap all the features in a FeatureCollection. 
    # Top Level GeoJSON object that map tools expect when they open the file. 
    return {"type": "FeatureCollection", "features": features}


###########################################################################################################################

########
# MAIN #
########
def main():

    # Create an argument parser. Reads options the user types on the
    # command line (like --state Illinois) and turns them into Python values
    p = argparse.ArgumentParser(description="Pull ALPR camera locations from OSM/Overpass")

    # Make a group of options where the user must pick exactly ONE.
    scope = p.add_mutually_exclusive_group(required=True)

    # Option 1: search a whole US state by its name.
    scope.add_argument("--state", help='US state name, e.g. "Illinois"')

    # Option 2: search a rectangle on the map (a "bounding box")
    # The user gives 4 numbers: the south, west, north, and east edges
    scope.add_argument(
        "--bbox",
        help="south,west,north,east decimal degrees, e.g. 41.6,-87.9,42.1,-87.5",
    )

    # Option 3: search the entire US. action="store_true" means this is an
    # on/off flag: if the user types --nationwide it becomes True, otherwise False.
    scope.add_argument("--nationwide", action="store_true", help="Pull all of the US (large, slow)")

    # Optional: the name of the file to save results to.
    # if the user doesn't give one, it stays None and we choose a name later.
    p.add_argument("--out", default=None, help="Output GeoJSON path (default: auto-named)")

    # Option 4 (NEW): search by place name. The script looks up the
    # place's bounding box for you, so you don't have to type the numbers.
    # It's in the same "pick exactly ONE" group, so you can't use
    # --place and --state together.
    scope.add_argument(
        "--place",
        help='Place name to geocode via Nominatim, e.g. "Orland Park, Illinois"',
    )

    # Read what the user actually typed and store it in "args"
    # e.g. args.state holds the state name, or None if it wasn't used.
    args = p.parse_args()

    # Choose which query to build based on the option the user picked
    if args.state: # State
        query = build_query_by_state(args.state) # Build a query that search inside the given state.
        default_out = f"{args.state.lower().replace(' ', '_')}_alpr.geojson" # Make a default file name from state name
    elif args.bbox: # Bounding Box
        parts = [float(x) for x in args.bbox.split(",")] # Split the text "41.6,-87.9,42.1,-87.5" at each comma and  convert to float
        if len(parts) != 4: # Defense Prog
            sys.exit("--bbox must be south,west,north,east")

        query = build_query_by_bbox(*parts) # The * "unpacks" the list, so the 4 numbers are passed as 4 separate arguments to the func
        default_out = "bbox_alpr.geojson"
    elif args.place: # Place name (NEW)
        # Ask Nominatim for the place's box, and get the 4 edges back
        # already in south, west, north, east order.
        south, west, north, east = geocode_place(args.place)

        # Reuse the EXISTING bbox query. A place search is really just a
        # bbox search where the computer found the numbers for us,
        # so no new query function is needed.
        query = build_query_by_bbox(south, west, north, east)

        # Make a file-name-friendly version of the place name:
        # "Orland Park, Illinois" -> lowercase -> remove commas -> spaces to _
        # -> "orland_park_illinois"
        safe_name = args.place.lower().replace(",", "").replace(" ", "_")
        default_out = f"{safe_name}_alpr.geojson"
    else: # if no --state, --bbox, or --place was used, it must be --nationwide
        query = build_query_nationwide()
        default_out = "us_nationwide_alpr.geojson" # Might Wanna Change This .



    out_path = args.out or default_out # Use filename or default

    print("Querying Overpass API...") # requests can take a while

    data = run_query(query) # send query to overpass API over internet and get results back as a Python Dict

    n = len(data.get("elements", [])) # Count the results

    print(f"Got {n} camera nodes.") # How many cameras were found

    geojson = to_geojson(data) # Convert the raw result into GeoJSON, standard map format, tools: QGIS, geojson.io, Leaflet

    with open(out_path, "w") as f: # Open or create output file for w writing
        json.dump(geojson, f, indent=2) # write the GeoJSON to file with indent=2 spaces out

    print(f"Wrote {len(geojson['features'])} features to {out_path}") # Confirm how many map features were saved, and where.



###############
# ENTRY_POINT #
###############
if __name__ == "__main__":
    main()


#######
# EOF #
#######