import os
import subprocess
import gc
import re
import datetime
from osgeo import gdal
import h5py
from dateutil import parser
from universal_downloads import Downloader
from typing import Optional, List, TypedDict

class BandMetadata(TypedDict):
  element: str
  level: str
  valid_time: str
  unit: str
  center: str

class GribTools:
  def __init__(
    self,
    name: str,
    downloader: Downloader,
    output_dir: Optional[str]=None,
    output_formats: Optional[List[str]]=["cog", "hdf"],
    cog_parameters: Optional[List[str]]=["all"],
    hdf_parameters: Optional[List[str]]=["all"],
    levels: Optional[List[str]]=["all"],
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
    self.cog_parameters = cog_parameters
    self.hdf_parameters = hdf_parameters
    self.levels = levels
    self.resolution = resolution
    print(self.hdf_parameters)
    # update downloader class to fit what we want
    self.downloader.base_dir = os.path.join(self.output_dir, "downloads")
    self.downloader.name = self.name

    # create output directory
    os.makedirs(self.output_dir, exist_ok=True)
    
    # gdal configuration
    gdal.SetCacheMax(250)
    gdal.UseExceptions()

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
    try:
      ds = gdal.Open(file)
    except Exception as e:
      ds = None
    if not ds:
      print("Could not open downloaded file trying to regrid...")
      file = self.regrid(file)
    # process the downloaded file
    if ("list" in self.output_formats):
      self.list_metadata(file)
    if ("cog" in self.output_formats):
      self.grib_to_cog(file, self.output_dir)
    if ("hdf" in self.output_formats):
      self.grib_to_hdf(file, self.output_dir)
    # ...
  
  def get_band_metadata(
    self,
    metadata: dict,
  ) -> BandMetadata:
    """
    Extract band metadata with fallbacks for different providers.
    @param metadata: Band metadata
    @return: Extracted metadata as dict with keys: element, level, valid_time, unit, center
    """
    grib_element = (
      metadata.get('GRIB_ELEMENT',  # Primary choice
      metadata.get('PARAMETER',     # GRIB1 fallback
      metadata.get('VARIABLE')))    # Generic fallback
    )
    grib_level = (
      metadata.get('GRIB_SHORT_NAME',
      metadata.get('LEVEL',
      metadata.get('HEIGHT')))
    )
    grib_time = (
      metadata.get('GRIB_VALID_TIME',  # Primary choice
      metadata.get('VALIDTIME',
      metadata.get('TIME')))
    )
    # normalize to ISO, handling epoch‐seconds vs free‑text
    if grib_time:
      dt = None
      # pure digits → treat as epoch seconds
      if re.fullmatch(r'\d+', grib_time):
        try:
          dt = datetime.datetime.fromtimestamp(int(grib_time), tz=datetime.timezone.utc)
        except (OSError, OverflowError):
          dt = None
      else:
        try:
          dt = parser.parse(grib_time, fuzzy=True)
        except (ValueError, OverflowError):
          dt = None

      if dt:
        grib_time = dt.isoformat()
      else:
        # fallback or null out invalid times
        grib_time = None

    return {
      'element': grib_element,
      'level': grib_level,
      'valid_time': grib_time,
      'unit': metadata.get('GRIB_UNIT', 'unknown'),
      'center': metadata.get('GRIB_CENTER', 'unknown')
    }
  
  def select_band(
    self,
    metadata: dict,
    parameters: List[str],
  ) -> bool:
    """
    Select band based on metadata and wanted levels and variable
    @param element: Element to select
    @return: False or safe metadata
    """
    safe_metadata = self.get_band_metadata(metadata)
    name = safe_metadata['element']
    level = safe_metadata['level']
    if not parameters:
      raise ValueError("No parameters provided for selection")
    # check if the band is wanted
    if (
      ("all" not in parameters and name not in parameters) or
      ("all" not in self.levels and level not in self.levels)
    ):
      return False
    return safe_metadata
  
  def regrid(
    self,
    grib_file: str,
    resolution: Optional[float]=None,
    output_file: Optional[str]=None,
  ) -> str:
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
      
    if not resolution:
      resolution = self.resolution if self.resolution else 0.1  # Default resolution if not provided
    
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

  def list_metadata(
      self,
      input_grib: str,
      output_file: Optional[str]=None,
  ):
    """
    List metadata of GRIB file and append them to a common file (used to debug)
    @param input_grib: Path
    @param output_file: Path to output file
    """
    if not output_file:
      output_file = os.path.join(os.getcwd(), "data", "metadata_list.txt")

    # Read existing metadata first
    existing_metadata = []
    if os.path.exists(output_file):
      with open(output_file, "r") as f:
        existing_metadata = f.read().split("\n")
    
    print(existing_metadata)

    # open grib file
    ds = gdal.Open(input_grib)
    if ds is None:
      raise Exception(f"Could not open {input_grib}")
    
    # Get band information
    info = gdal.Info(ds, format='json')
    bands = info['bands']

    # Append new metadata
    with open(output_file, "a") as f:
      for band_idx, band_info in enumerate(bands, 1):
        try:
          # Extract metadata
          metadata = band_info['metadata']['']
          safe_metadata = self.get_band_metadata(metadata)
          var_name = safe_metadata['element']
          
          # check if the band is already in the file
          if var_name in existing_metadata:
            print(f"Skipping {var_name}...")
            continue
            
          existing_metadata.append(var_name)
          f.write(f"{var_name}\n")
        except Exception as e:
          print(f"Error processing band {band_idx}: {str(e)}")
          continue
        finally:
          band = None
          gc.collect()

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
    # open grib file
    ds = gdal.Open(input_grib)
    if ds is None:
      raise Exception(f"Could not open {input_grib}")
    
    print(f"Processing {input_grib} to cog...")

    # Get band information
    info = gdal.Info(ds, format='json')
    bands = info['bands']
    
    for band_idx, band_info in enumerate(bands, 1):
      try:
        # Direct band access
        band = ds.GetRasterBand(band_idx)
        if band is None:
          raise Exception(f"Could not access band {band_idx}")
        
        metadata = band_info['metadata']['']
        safe_metadata = self.get_band_metadata(metadata)
        var_name = safe_metadata['element']
        level = safe_metadata['level']
        # check if the band is wanted
        if not self.select_band(metadata, self.cog_parameters): continue
        time_dir = os.path.join(
          output_dir,
          safe_metadata['valid_time'].split(":")[0] + "_00Z"
        )
        os.makedirs(time_dir, exist_ok=True)
        output_file = f"{time_dir}/{var_name}_{level}.tif"
        print(f"\nProcessing band {var_name}_{level} at time {safe_metadata['valid_time']}")
        
        translate_options = gdal.TranslateOptions(
          bandList=[band_idx],
          creationOptions=[
            "BIGTIFF=YES",
            "COMPRESS=DEFLATE",
            "TILED=YES",
            "BLOCKXSIZE=256",
            "BLOCKYSIZE=256",
          ]
        )
        
        gdal.Translate(output_file, ds, options=translate_options)
            
      except Exception as e:
        print(f"Error processing band {band_idx}: {str(e)}")
        continue
      finally:
        band = None
        gc.collect()
    ds = None

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
    # Open GRIB2 file
    ds = gdal.Open(input_grib)
    if ds is None:
      raise Exception(f"Could not open {input_grib}")

    print(f"Processing {input_grib} to hdf5...")

    # Get band information
    info = gdal.Info(ds, format='json')
    bands = info['bands']


    # Create HDF5 file
    with h5py.File(os.path.join(output_dir, f"{self.name}.h5"), "w") as hdf5_file:
      # Loop through each band
      for band_idx, band_info in enumerate(bands, 1):
        try:
          band = ds.GetRasterBand(band_idx)
          if band is None:
            raise Exception(f"Could not access band {band_idx}")

          # Extract metadata
          metadata = band_info['metadata']['']
          safe_metadata = self.get_band_metadata(metadata)
          var_name = safe_metadata['element']
          units = safe_metadata['unit']
          level = safe_metadata['level']
          # check if the band is wanted
          if not self.select_band(metadata, self.hdf_parameters): continue

          print(f"\nProcessing band {band_idx}/{len(bands)}")
          print(f"Variable: {var_name}, Level: {level}, Units: {units}")

          # Read band data as a NumPy array
          band_data = band.ReadAsArray()

          # Create dataset in HDF5 file
          dataset_name = f"{var_name}_{level}_{band_idx}"
          hdf5_dataset = hdf5_file.create_dataset(dataset_name, data=band_data, compression="gzip")

          # Store metadata in the dataset attributes
          hdf5_dataset.attrs["GRIB_ELEMENT"] = var_name
          hdf5_dataset.attrs["GRIB_SHORT_NAME"] = level
          hdf5_dataset.attrs["GRIB_UNIT"] = units
        except Exception as e:
          print(f"Error processing band {band_idx}: {str(e)}")
          continue
        finally:
          band = None
          gc.collect()

      # Extract lat/lon information
      subdatasets = ds.GetSubDatasets()
      for name, desc in subdatasets:
        if "latitude" in desc.lower():
          lat_ds = gdal.Open(name)
          lat_data = lat_ds.ReadAsArray()
          hdf5_file.create_dataset("latitude", data=lat_data)
          lat_ds = None
        elif "longitude" in desc.lower():
          lon_ds = gdal.Open(name)
          lon_data = lon_ds.ReadAsArray()
          hdf5_file.create_dataset("longitude", data=lon_data)
          lon_ds = None
    ds = None
  

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
  # icon.download_and_process()

  arome_downloader = Downloader(
    url_template='https://object.data.gouv.fr/meteofrance-pnt/pnt/{run_time}Z/arome/0025/{package}/arome__0025__{package}__{step}__{run_time}Z.grib2',
    update_times=[ 0, 3, 6, 12, 18 ],
    steps=[ '00H06H' ],
    packages=[ 'HP1' ],
    safe_timeout=6,
    date_format="iso"
  )
  arome = GribTools(
    name="arome",
    downloader=arome_downloader,
    output_formats=[ "cog", "hdf" ],
    parameters=[ "TMP" ],
    levels=[ "all" ]
  )
  arome.download_and_process()