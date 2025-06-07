from helpers import arome_025_helper, aladin_helper
from universal_downloads import Downloader
from grib_tools import GribTools
import os

# here is me testing some shits enjoy it (or not)

arome_025 = arome_025_helper(
  steps=[ "00H06H" ],
  packages=[ "HP1", "HP2" ],
  output_formats=[ "hdf" ],
)

# arome_025.download_and_process()

# arome_025.downloader.merge_datasets(
#   input_files=[
#     "data/out/arome_025/downloads/arome_025_2025-05-22T03:00:00/hp1-1.grib2",
#     "data/out/arome_025/downloads/arome_025_2025-05-22T03:00:00/hp1-2.grib2",
#   ],
#   output_file="data/out/arome_025/downloads/arome_025_2025-05-22T03:00:00/hp1-merged.grib2",
# )



# arome_025.download_and_process()
# arome_025.grib_to_hdf(
#   "data/out/arome_025/downloads/arome_025_2025-04-28T03:00:00/arome_025_2025-04-28T03:00:00_combined.grib2",
#   "/app/data/out"
# )
# print("PRES" in open(os.path.join(os.getcwd(), "data", "metadata_list.txt")).read().split("\n"))
# with open(os.path.join(os.getcwd(), "data", "metadata_list.txt"), "rw") as f:
#   print(f.read().split("\n"))

# testing for aladin (not good rn)
# aladin_downloader = Downloader(
#   url_template='https://opendata.chmi.cz/meteorology/weather/nwp_aladin/Lambert_2.3km/{run_hour}/ALADLAMB4opendata_{run_time}_CLPVEIND_MOD_XFU.grb.bz2{step}{package}',
#   update_times=[ 0, 6, 12, 18 ],
#   safe_timeout=4,
#   date_format="%Y%m%d%H",
#   steps=[""],
#   packages=[""],
# )

# aladin = GribTools(
#   name='aladin',
#   downloader=aladin_downloader,
#   output_dir="/app/data/out/aladin",
#   output_formats=["cog"],
#   cog_parameters=["all"],
#   hdf_parameters=["all"],
#   levels=["all"],
# )

# aladin.download_and_process()

aladin = aladin_helper(
  packages=[ "TEMPERATUR" ],
  output_formats=[ "hdf" ],
)

aladin.download_and_process()

# date = "2025-04-17T11_00_00+00_00"
# date = date.split("_")[0] + "_00Z"
# print(f"date: {date}")