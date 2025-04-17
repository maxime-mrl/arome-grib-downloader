from helpers import arome_025_helper
from universal_downloads import Downloader
from grib_tools import GribTools
import os


arome_025 = arome_025_helper(
  steps=[ "00H06H" ],
  packages=[ "HP1" ],
  output_formats=[ "cog" ],
  cog_parameters=[ "TMP" ],
  levels=[ "all" ]
)



arome_025.download_and_process()
# print("PRES" in open(os.path.join(os.getcwd(), "data", "metadata_list.txt")).read().split("\n"))
# with open(os.path.join(os.getcwd(), "data", "metadata_list.txt"), "rw") as f:
#   print(f.read().split("\n"))
