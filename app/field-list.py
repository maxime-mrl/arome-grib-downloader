# [NO REAL USE]
import os
import json
import pygrib

def write_to_json_file(data, output_path):
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)  # Convert the data to JSON
    return output_path

path = os.path.join(os.getcwd(), "results", "arome__0025__HP1__00H06H__2024-09-11T03:00:00Z.grib2")
output_json_path = path + "field-infos.json"

with pygrib.open(path) as ds:
    print(ds[1].keys())
    grib_name = []
    # Iterate through the GRIB messages
    for msg in ds:
        values = msg.values.flatten()
        mask = ~values.mask  # mask is the invert of the masked (null) values
        filtered_values = values[mask]
        grib_name.append(f"{msg.name} level {msg.level} number of valid values: {len(filtered_values)}")

    # Write the extracted data to a JSON file
    write_to_json_file(grib_name, output_json_path)

print(f"JSON file saved at {output_json_path}")
