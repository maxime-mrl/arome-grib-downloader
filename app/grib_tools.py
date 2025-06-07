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
    # first download the data
    self.downloader.download()
    # check if downloader has downloaded the file correctly (only one file should exist)
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
      # regrid
      file = self.regrid(file)
    # process the downloaded file to the wanted formats
    if ("list" in self.output_formats): # list are just for debugging (seeing what variables are available)
      self.list_metadata(file)
    if ("cog" in self.output_formats and "hdf" in self.output_formats): # if both cog and hdf are wanted (as it should be) loop through both at the same time to improve performance
      self.to_cog_and_hdf(file, self.output_dir)
    elif ("cog" in self.output_formats): # if only cloud optimized geotiff is wanted
      self.grib_to_cog(file, self.output_dir)
    elif ("hdf" in self.output_formats): # if only hdf5 is wanted
      self.grib_to_hdf(file, self.output_dir)
    print("download and process done")
  
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
      metadata.get('GRIB_SHORT_NAME', # same as GRIB_ELEMENT (this = primary choice)
      metadata.get('LEVEL',
      metadata.get('HEIGHT')))
    )
    grib_time = (
      metadata.get('GRIB_VALID_TIME',  # ...
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
    if ( # "all" means no check
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
    Handle reprojection of specials grids (mainly ICON models) to regular latlon grid
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
      if self.resolution:
        resolution = self.resolution
      else:
        resolution = 0.1  # Default resolution if not provided
        print("No resolution provided, using default 0.1 degrees -- You should generally set it")
    
    lon_points = int(360 / resolution) + 1
    lat_points = int(180 / resolution) + 1
    # wgrib2 command to reproject the GRIB file
    # -if ":GEOLAT:" and -if ":GEOLON:" are used to select the latitude and longitude variables and set the center to WMO standard (center 7) and store them as NLAT and ELON respectively
    # -grid_def is used to define the grid
    # -s is used to print the grid definition
    # -not_if "^(1|2):" is used to skip the first two messages (which are usually metadata)
    # -lola 0:{lon_points}:{resolution} -90:{lat_points}:{resolution} is used to define the grid in latitude and longitude
    cmd = (
      f'wgrib2 {grib_file}'
      f' -if ":GEOLAT:" -set center 7 -set_var NLAT -fi'
      f' -if ":GEOLON:" -set center 7 -set_var ELON -fi'
      f' -grid_def -s -not_if "^(1|2):"  -lola 0:{lon_points}:{resolution} -90:{lat_points}:{resolution} {output_file} grib'
    )
    
    subprocess.run(cmd, shell=True, check=True)
    print(f"Reprojection done : {output_file}")
    return output_file

  def to_cog_and_hdf(
    self,
    input_grib: str,
    output_dir: Optional[str]=None,
  ):
    """
    Convert GRIB file to Cloud Optimized GeoTIFF (COG) and HDF5
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
          # ---- COG PROCESSING ----
          # check if the band is wanted
          if self.select_band(metadata, self.cog_parameters):
            time_dir = os.path.join(
              output_dir,
              safe_metadata['valid_time'].split(":")[0] + "_00Z"
            )
            # create time directory if it does not exist
            os.makedirs(time_dir, exist_ok=True)
            output_file = f"{time_dir}/{var_name}_{level}.tif"
            print(f"\nProcessing band {var_name}_{level} at time {safe_metadata['valid_time']}")
            # gdal translate to cog
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
          # ---- HDF5 PROCESSING ----
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
        finally: # clean up
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
  