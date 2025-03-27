import os
from osgeo import gdal
from universal_downloads import Downloader
from typing import Optional, List

class GribTools:
  def __init__(
    self,
    name: str,
    downloader: Downloader,
    output_dir: Optional[str]=None,
    output_formats: Optional[List[str]]=[],
    parameters: Optional[List[str]]=[],
    levels: Optional[List[str]]=[],
    resolution: Optional[float]=1,
  ):
    """
    Initializes the GribTools instance.
    and update the downloader class to fit accordingly.
    
    :param name: model output name (can be anything).
    :param downloader: Downloader class instance. (can be a custom class if it follow universal_downloads Downloader structure)
    :param output_dir: Output directory for downloaded files.
    :param output_formats: Output formats to convert to. (accepts 'cog', 'hdf')
    :param parameters: Parameters to extract from GRIB files. (eg. TMP, RH, UGRD, VGRD...)
    :param levels: Levels to extract from GRIB files.
    :param resolution: Target resolution in degrees when regridding is needed.
    """
    self.name = name
    self.downloader = downloader
    self.output_dir = output_dir if output_dir else os.path.join(os.getcwd(), "data", "out", name)
    self.output_formats = output_formats
    self.parameters = parameters

    # update downloader class to fit what we want
    self.downloader.base_dir = os.path.join(self.output_dir, "downloads")
    self.downloader.name = self.name

  def download_and_process(
    self,
  ) -> None:
    """
    Helper function to download and process data automatically
    """
    self.downloader.download()
    # check if downloader has downloaded the file correctly (only one file which exists)
    if len(self.downloader.files) != 1:
      raise Exception("Downloader should output one file")
    file = self.downloader.files[0]
    if not os.path.exists(file):
      raise Exception("Downloaded file does not exist")
    print(f"Downloaded file: {file}")
    # check if we need to regrid the file
    ds = gdal.Open(file)
    if not ds:
      print("Could not open downloaded file trying to regrid...")
      file = self.regrid(file)
    # process the downloaded file
    if ("cog" in self.output_formats):
      self.grib_to_cog(file, self.output_dir)
    if ("hdf" in self.output_formats):
      self.grib_to_hdf(file, self.output_dir)
    # ...
  
  def get_band_metadata(
    self,
    metadata: dict,
  ):
    """
    Extract band metadata with fallbacks for different providers.
    @param metadata: Band metadata
    @return: Extracted metadata
    """
    pass
  
  def grib_to_cog(
    self,
    input_grib: str,
    output_dir: str,
  ):
    """
    Convert GRIB file to Cloud Optimized GeoTIFF (COG)
    @param input_grib: Path to input GRIB file
    @param output_dir: Path to output directory
    """
    print("Converting GRIB to COG...")
    pass

  def regrid(
    self,
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
    print("Regridding GRIB file...")
    pass

  def grib_to_hdf(
    self,
    input_grib: str,
    output_dir: str,
  ):
    """
    Convert GRIB file to Hierarchical Data Format (HDF5)
    @param input_grib: Path to input GRIB file
    @param output_dir: Path to output directory
    """
    print("Converting GRIB to HDF...")
    pass
  

# TEST
if __name__ == "__main__":
  icon_downloader = Downloader(
    url_template='https://opendata.dwd.de/weather/nwp/icon-d2/grib/{run_hour}/{package}/icon-d2_germany_icosahedral_model-level_{run_time}_{step}_{levels}_{package}.grib2.bz2',
    update_times=[ 0, 3, 6, 9, 12, 15, 18, 21 ],
    steps=[ "001", "002" ],
    packages=[ 't' ],
    safe_timeout=1,
    date_format="%Y%m%d%H",
    special_urls=[
      'https://opendata.dwd.de/weather/nwp/icon-d2/grib/{run_hour}/{invariant_params}/icon-d2_germany_icosahedral_time-invariant_{run_time}_000_0_{invariant_params}.grib2.bz2'
    ],
    levels=[ 1, 2 ],
    invariant_params=[ 'clat', 'clon' ]
  )
  icon = GribTools(
    name="icon",
    downloader=icon_downloader,
    output_formats=[ "cog" ],
    parameters=[ "TMP" ],
    levels=[ "2m", "10m" ]
  )
  icon.download_and_process()