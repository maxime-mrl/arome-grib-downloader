# from architecture-performance.fr/ap_blog/fetching-arome-weather-forecasts-and-plotting-temperatures

import os
import datetime
import subprocess

# arome runs are splitted into different time ranges up to 51h
arome_time_ranges = [ '00H06H', '07H12H', '13H18H', '19H24H', '25H30H', '31H36H', '37H42H', '43H48H', '48H51H' ]

# get last time arome updated their runs
def get_latest_run_timestamp(delay=4):
    update_times = [0, 3, 6, 12, 18] # Arome runs are updated at 00h, 03h, 06h, 12h, and 18h
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    # Subtract delay from the current utc hour (take times for arome's run to be published)
    last_possible_publish = utc_now - datetime.timedelta(hours=delay)
    # Find the latest run time before or equal to the candidate time
    latest_run_hour = max(hour for hour in update_times if hour <= last_possible_publish.hour)
    # Construct the run time
    run_time = datetime.datetime(utc_now.year, utc_now.month, utc_now.day, latest_run_hour)
    return run_time.isoformat()

run_time = get_latest_run_timestamp() + "Z" # Z at the ends of arome time idk what this is must mean something, will research soontm

def download_gribs(package, time_ranges=[]):
    # check function inputs
    assert len(time_ranges) > 0, "at least one time range required"
    assert package in ['HP1', 'HP2', 'HP3', 'IP1', 'IP2', 'IP3', 'IP4', 'IP5', 'SP1', 'SP2', 'SP3'], "invalid package"
    # defs
    files = []
    # sequentially download gribs for all time ranges wanted
    for time_range in time_ranges:
        url = f'https://object.data.gouv.fr/meteofrance-pnt/pnt/{run_time}/arome/0025/{package}/arome__0025__{package}__{time_range}__{run_time}.grib2'
        file_path = os.path.join(os.getcwd(), "data", f'arome__0025__{package}__{time_range}__{run_time}.grib2')  # set download path to [PROJECT]/data/filename.grib2
        cmd = f'wget --output-document {file_path} {url}'
        files.append(file_path) # keep track of the downloaded files
        subprocess.call(cmd, shell=True) # download data
    
download_gribs("HP1", [ '00H06H', '07H12H' ])