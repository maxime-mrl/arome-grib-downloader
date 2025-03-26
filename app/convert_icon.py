############################################
# REPROJECT ICON GRIB FILES TO LATLON GRID #
############################################

# DWD use icoasahedral grid for their ICON model, which is difficult to work with.
# We need to reproject the data to a regular latlon grid (with wgrib or CDO, here we use wgrib2) to make it easier to work with.

# this takes a lot of time and resources, especially for the first grib key (need to analyse every latlon before reprojecting)
# for now on my semi potato pc (ryzen 5 3600) here are the time taken for depending on the resolution:
# - 1°: ~30s
# - 0.5°: ~2m
# - 0.1: ~1h
# - 0.02: ~5h
# so yeah... not great, not sure if it can be optimized (i hope tho)

import os
import subprocess
from typing import Optional

def regrid(
    grib_file: str,
    resolution: Optional[float]=0.1,
    output_file: Optional[str]=None,
  ):
  """
  Handle reprojection of specials grids (mainly ICON) to regular latlon grid
  @param grib_file: Path to input GRIB file
  @param resolution: Target resolution in degrees (icon-d2 ~ 0.02, icon-eu ~ 0.0625, and icon-global ~ 0.125) default to 0.1
  @param output_file: Path to output reprojected GRIB file
  
  @raise AssertionError: If input file does not exist
  @raise Exception: If wgrib2 command fails
  @return: Path to reprojected GRIB file
  """

  assert os.path.exists(grib_file), f"File not found: {grib_file}"

  if not output_file:
    output_file = f"{os.path.splitext(grib_file)[0]}_reprojected.grib2"
  
  lon_points = int(360 / resolution) + 1
  lat_points = int(180 / resolution) + 1

  cmd = (
    f'wgrib2 {grib_file}'
    f' -if ":GEOLAT:" -set center 7 -set_var NLAT -fi'
    f' -if ":GEOLON:" -set center 7 -set_var ELON -fi'
    f' -grid_def -s -not_if "^(1|2):"  -lola 0:{lon_points}:{resolution} -90:{lat_points}:{resolution} {output_file} grib'
  )
  
  subprocess.run(cmd, shell=True, check=True)
  print(f"Reprojection done : {output_file}")
  return output_file


# Example usage
if __name__ == "__main__":
  regrid(os.path.join(os.getcwd(),"data/downloads/RUN_2025032409/icon.grib2"), 0.02)

