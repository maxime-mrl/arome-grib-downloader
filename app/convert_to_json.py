import os
import json
import pygrib
import numpy as np
import re;

path = os.path.join(os.getcwd(), "data", "arome__0025__HP1__00H06H__2024-09-11T03:00:00Z.grib2")

def write_to_json_file(data, output_path):
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)  # Convert the data to JSON
    return output_path

def filter_loc(data):
    lats, lons = data.latlons()
    lats = lats.flatten()
    lons = lons.flatten()
    values = data.values.flatten()
    # create a mask to remove undefined values
    if np.ma.isMaskedArray(values): # is masked array
        mask = ~values.mask  # mask is the invert of the masked (null) values
    else: # is not masked array
        mask = values != data.missingValue # if not masked array revert back to the missing value defined by the grib
    return lats[mask], lons[mask], mask

with pygrib.open(path) as grib:
    lats, lons, mask = filter_loc(grib[1])
    # split the grib to previsions hours to make some smaller working files and (hopefully) not crash my computer
    grb_hours = []
    for grb in grib:
        isTimeExist = next((i for i, item in enumerate(grb_hours) if item["forecastTime"] == grb.forecastTime), None)
        if (type(isTimeExist) == int):
            grb_hours[isTimeExist]["data"].append(grb)
        else:
            grb_hours.append({
                "forecastTime": grb.forecastTime,
                "data": [ grb ]
            })

    for forecast in grb_hours:
        grib_data = []
        print(f"--- parsing hour {forecast["forecastTime"]} ---")
        for data in forecast["data"]:
            # U and V component are kinda redondant to wind dir and speed and so I don't need them
            if (re.search("[UV](\swind\s|\s)component", data.name)): continue
            print(f"parsing: {data.name} at level {data.level}")
            # Get values
            values = data.values.flatten()
            # removes undefined coordinates
            filtered_values = values[mask]
            
            # Extract relevant data from the GRIB message
            msg_data = {
                "parameter_name": data.name,
                "short_name": data.shortName,
                "level": data.level,
                "units": data.units,
                "values": filtered_values.tolist(),  # Convert to list for JSON serialization
            }
            grib_data.append(msg_data)
        # Write the extracted data to a JSON file
        output_json_path = os.path.join(os.getcwd(), "results", f"arome_hp1_{forecast["forecastTime"]}.json")
        write_to_json_file({
            "lats": lats.tolist(),
            "lons": lons.tolist(),
            "data": grib_data
        }, output_json_path)
        print(f"JSON file saved at {output_json_path}")
