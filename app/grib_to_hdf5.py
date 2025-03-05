import os
import gc
import h5py
from osgeo import gdal

def grib_to_hdf5(input_grib, output_hdf5):
  # gdal configuration
  gdal.SetCacheMax(250)
  gdal.UseExceptions()

  try:
    # Open GRIB2 file
    ds = gdal.Open(input_grib)
    if ds is None:
      raise Exception(f"Could not open {input_grib}")

    print(f"Processing {input_grib}...")

    # Get band information
    info = gdal.Info(ds, format='json')
    bands = info['bands']
    total_bands = len(bands)

    print(f"Total bands: {total_bands}")

    # Create HDF5 file
    with h5py.File(output_hdf5, "w") as hdf5_file:
      # Loop through each band
      for band_idx, band_info in enumerate(bands, 1):
        try:
          band = ds.GetRasterBand(band_idx)
          if band is None:
            raise Exception(f"Could not access band {band_idx}")

          # Extract metadata
          metadata = band_info['metadata']['']
          var_name = metadata.get('GRIB_ELEMENT', f'band_{band_idx}')
          level = metadata.get('GRIB_SHORT_NAME', '')
          units = metadata.get('GRIB_UNIT', '')

          print(f"\nProcessing band {band_idx}/{total_bands}")
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

  finally:
    ds = None

# Example usage:
grib_to_hdf5("data/arome_ip1.grib2", "out/out.h5")
