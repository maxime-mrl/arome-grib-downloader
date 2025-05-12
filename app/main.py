from helpers import arome_025_helper, icon_d2_helper
from universal_downloads import Downloader
from grib_tools import GribTools
import os


arome_025 = arome_025_helper(
  steps=[ "00H06H" ],
  packages=[ "HP1" ],
  output_formats=[ "hdf" ],
)


icon = icon_d2_helper(
  steps=[ "000" ],
  packages=[ "t", "u", "v" ],
  output_formats=[ "hdf" ],
  levels=[ 1 ],
  output_resolution=0.05
)

icon.download_and_process()


# arome_025.download_and_process()
# arome_025.grib_to_hdf(
#   "data/out/arome_025/downloads/arome_025_2025-04-28T03:00:00/arome_025_2025-04-28T03:00:00_combined.grib2",
#   "/app/data/out"
# )
# print("PRES" in open(os.path.join(os.getcwd(), "data", "metadata_list.txt")).read().split("\n"))
# with open(os.path.join(os.getcwd(), "data", "metadata_list.txt"), "rw") as f:
#   print(f.read().split("\n"))

# testing for aladin
# download working - GRIB1 format so can't be merged / processed for now
# aladin_downloader = Downloader(
#   url_template='https://opendata.chmi.cz/meteorology/weather/nwp_aladin/Lambert_2.3km/{run_hour}/ALADLAMB4opendata_{run_time}_{levels}{package}.grb.bz2',
#   update_times=[ 0, 6, 12, 18 ],
#   safe_timeout=4,
#   date_format="%Y%m%d%H",
#   levels=[ "P00000", "P10000" ],
#   steps=[''], # no steps for aladin
#   packages=["TEMPERATUR", "WIND_U_COM", "WIND_V_COM" ],
# )


# date = "2025-04-17T11_00_00+00_00"
# date = date.split("_")[0] + "_00Z"
# print(f"date: {date}")