from universal_downloads import Downloader
from grib_tools import GribTools

# Here helpers are not used, since they are NOT fully functional yet.

# GENERAL function:
# 1- create classes for downloading and processing grib files whith the correct parameters for the model
# 2- configure the classes to get what you want (e.g. steps, packages, output formats, etc.)
# 3- call the download_and_process() method to download and convert the grib files at once with the specified parameters

# --- AROME 0.025° BASE ---
# downloader for grib files
arome_downloader = Downloader(
  url_template='https://object.data.gouv.fr/meteofrance-pnt/pnt/{run_time}Z/arome/0025/{package}/arome__0025__{package}__{step}__{run_time}Z.grib2',
  update_times=[ 0, 3, 6, 12, 18 ],
  steps=[ '00H06H' ],
  packages=[ 'HP1', 'HP2' ],
  safe_timeout=6,
  date_format="iso"
)
# processor to convert grib files to COG or HDF5
arome_processor = GribTools(
  name='arome',
  downloader=arome_downloader,
  output_formats=[ "hdf", "cog" ],
)
# general function to do everything at once as specified in the classes
arome_processor.download_and_process()

# --- ICON-D2 BASE ---
# downloader for grib files
icon_downloader = Downloader(
  url_template='https://opendata.dwd.de/weather/nwp/icon-d2/grib/{run_hour}/{package}/icon-d2_germany_icosahedral_model-level_{run_time}_{step}_{levels}_{package}.grib2.bz2',
  update_times=[ 0, 3, 6, 9, 12, 15, 18, 21 ],
  steps=[ "000", "001", "002" ],
  packages=[ 't', "u", "v" ],
  safe_timeout=1,
  date_format="%Y%m%d%H",
  special_urls=[
    'https://opendata.dwd.de/weather/nwp/icon-d2/grib/{run_hour}/{invariant_params}/icon-d2_germany_icosahedral_time-invariant_{run_time}_000_0_{invariant_params}.grib2.bz2'
  ],
  levels=[ 1, 2 ],
  invariant_params=[ 'clat', 'clon' ]
)

# processor to regrid and convert grib files to COG or HDF5
icon_processor = GribTools(
  name='icon_d2',
  downloader=icon_downloader,
  output_formats=[ "hdf", "cog" ],
  resolution=0.05,
)

# general function to do everything at once as specified in the classes
icon_processor.download_and_process()
