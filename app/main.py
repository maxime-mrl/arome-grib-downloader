from osgeo import gdal
import os
import gc

def grib_to_cog(input_grib, output_dir):
  # Create output directory if it does not exist
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)

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
        var_name = metadata.get('GRIB_ELEMENT', f'band_{band_idx}')
        level = metadata.get('GRIB_SHORT_NAME', '')
        
        output_file = f"{output_dir}/{var_name}_{level}_{band_idx}.tif"
        print(f"\nProcessing band {band_idx}/{total_bands}")
        print(f"Variable: {var_name}, Level: {level}")
        
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
  finally:
    ds = None

# Example usage
grib_to_cog("data/icon-d2_germany_t_2m_000_2d.grib2", "out/icon")