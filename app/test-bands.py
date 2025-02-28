from osgeo import gdal
import os
import gc

def get_band_metadata(metadata):
  """Extract band metadata with fallbacks for different providers."""
  return {
    'element': metadata.get('GRIB_ELEMENT',  # Primary choice
      metadata.get('PARAMETER',       # GRIB1 fallback
      metadata.get('VARIABLE', 'unknown'))), # Generic fallback
    'level': metadata.get('GRIB_SHORT_NAME',
      metadata.get('LEVEL',
      metadata.get('HEIGHT', 'unknown'))),
    'valid_time': metadata.get('GRIB_VALID_TIME',
      metadata.get('VALIDTIME', 
      metadata.get('TIME', 'unknown'))),
    'center': metadata.get('GRIB_CENTER', 'unknown')
  }

def print_bands(input_grib):
  # gdal configuration
  gdal.SetCacheMax(250)
  gdal.UseExceptions()

  try:
    # open grib file
    ds = gdal.Open(input_grib)
    if ds is None:
      raise Exception(f"Could not open {input_grib}")
    
    print(f"Processing {input_grib}...")

    # Get band information
    info = gdal.Info(ds, format='json')
    bands = info['bands']
    total_bands = len(bands)
    
    print(f"Total bands: {total_bands}")
    
    for band_idx, band_info in enumerate(bands, 1):
      try:
        # Direct band access
        band = ds.GetRasterBand(band_idx)
        if band is None:
          raise Exception(f"Could not access band {band_idx}")
        
        metadata = band_info['metadata']['']
        safe_metadata = get_band_metadata(metadata)
        
        print(f'\nband: {safe_metadata["element"]} at level {safe_metadata["level"]} at time {safe_metadata["valid_time"]}')
        
      except Exception as e:
        print(f"Error processing band {band_idx}: {str(e)}")
        continue
      finally:
        band = None
        gc.collect()
  finally:
    ds = None

# Example usage
print_bands("data/arome_ip1.grib2")