import os
import subprocess
import datetime
from itertools import product
import bz2
from typing import Any, Dict, List, Optional, Union

class Downloader:
  def __init__(
    self,
    url_template: str,
    update_times: List[int],
    steps: List[Any],
    packages: List[Any],
    safe_timeout: Optional[int] = 1,
    date_format: Optional[str] = "%Y%m%d%H",
    special_urls: Optional[List[str]] = [],
    name: Optional[str] = None,
    **extra_str_params: Union[str, List[str]]
  ) -> None:
    """
    Initializes the Downloader instance.
    
    :param url_template: URL template with placeholders.
    :param update_times: List of update hours (e.g., [0, 6, 12, 18]).
    :param steps: Forecast steps.
    :param packages: Forecast packages.
    :param safe_timeout: Number of hours to wait before the next run is available.
    :param date_format: Format for the run time date.
    :param special_urls: any URL template with different format, template will be formated the same way as url_template.
    :param name: Optional model name (used for default outputs).
    :param extra_str_params: Additional string parameters for URL formatting.
    """
    self.url_template = url_template
    self.special_urls = special_urls
    self.update_times = update_times
    self.safe_timeout = safe_timeout
    self.date_format = date_format
    self.steps = steps
    self.packages = packages
    self.extra_str_params = self._parse_kwargs(**extra_str_params)
    self.name = name
    self.files = []

  def _parse_kwargs(self, **kwargs: Union[str, List[str]]) -> List[Dict[str, str]]:
    """
    Processes extra keyword arguments to support both single values and lists.
    
    :param kwargs: Extra parameters for string formatting.
    :return: A list of dictionaries with each combination of parameters.
    """
    # Optionally, uncomment to enforce that all keys exist in the template: [NOT RECOMMENDED SINCE SPECIAL URLS MAY NOT CONTAIN ALL KEYS]
    # missing_keys = [key for key in kwargs if f'{{{key}}}' not in self.url_template]
    # if missing_keys:
    #     raise ValueError(f"Missing placeholders in template for keys: {', '.join(missing_keys)}")
    
    list_params = {k: v for k, v in kwargs.items() if isinstance(v, list)}
    single_params = {k: v for k, v in kwargs.items() if not isinstance(v, list)}

    if not list_params:
      return [ {**single_params} ]

    parsed_kwargs = []
    keys, values = zip(*list_params.items())  # Extract keys and corresponding list values
    for combination in product(*values):  # Cartesian product of list values
      combo_dict = dict(zip(keys, combination))
      combo_dict.update(single_params)
      parsed_kwargs.append(combo_dict)
    return parsed_kwargs

  def get_latest_run(self) -> tuple[str, str]:
    """
    Determines the latest available run time based on update times and safe_timeout.
    
    :raises ValueError: If no valid update times are available based on the safe_timeout.
    :raises ValueError: If no steps or packages are provided.
    :return: A tuple containing the run time in the specified format and run hour (zero-padded).
    """
    
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    last_possible_publish = utc_now - datetime.timedelta(hours=self.safe_timeout)

    # Find the latest update time that is less than or equal to last_possible_publish.hour.
    valid_hours = [hour for hour in self.update_times if hour <= last_possible_publish.hour]
    if not valid_hours:
      raise ValueError("No valid update times available based on the safe_timeout.")
    latest_run_hour = max(valid_hours)

    run_time = datetime.datetime(utc_now.year, utc_now.month, utc_now.day, latest_run_hour)
    formatted_run_time = (
      run_time.isoformat() if self.date_format == "iso" else run_time.strftime(self.date_format)
    )
    formatted_hour = f"{latest_run_hour:02d}"
    return formatted_run_time, formatted_hour

  def construct_urls(self) -> List[str]:
    """
    Constructs URLs by iterating through packages, steps, and extra parameters.
    
    :raises ValueError: If no steps or packages are provided or URL template is not a string.
    :return: List of constructed URLs.
    """
    # Validate input parameters
    if not self.steps:
      raise ValueError("At least one time step is required.")
    if not self.packages:
      raise ValueError("At least one package is required.")
    if not isinstance(self.url_template, str):
      raise TypeError("URL template must be a string.")

    run_time, run_hour = self.get_latest_run()
    urls = []

    # Loop through packages, steps, and extra parameters to build each URL
    for package in self.packages:
      for step in self.steps:
        for extra_params in self.extra_str_params:
          url = self.url_template.format(
            run_hour=run_hour,
            run_time=run_time,
            step=step,
            package=package,
            **extra_params
          )
          # additionally add any special URLs with required parameters
          for special_url in self.special_urls:
            additional_url = special_url.format(
              run_hour=run_hour,
              run_time=run_time,
              step=step,
              package=package,
              **extra_params
            )
            if additional_url not in urls:
              urls.append(additional_url)
          if url not in urls:
            urls.append(url)
    return urls

  def download(self, output_dir: Optional[str] = None) -> None:
    """
    Downloads files from constructed URLs and saves them to the output directory.
    
    :param output_dir: Optional directory to save downloads. If not provided, directory will be ./data/downloads/RUN_{run_time}.
    """
    run_time, _ = self.get_latest_run()
    if output_dir is None:
      output_dir = os.path.join(
        os.getcwd(),
        "data",
        "downloads"
        f"{self.name if self.name else "RUN"}_{run_time}"
      )

    os.makedirs(output_dir, exist_ok=True)
    urls = self.construct_urls()

    for url in urls:
      file_name = os.path.basename(url)
      file_path = os.path.join(output_dir, file_name)
      print(f"Downloading {file_name} from {url} to {file_path}")
      subprocess.call(f'wget --output-document {file_path} {url}', shell=True)
      
      # HANDLE DECOMPRESSION
      if file_name.endswith('.bz2'):
        file_name = self.decompress_bz2(file_path)
      self.files.append(os.path.join(output_dir, file_name))

    # MERGE FILES      
    if len(self.files) > 0:
      self.merge_datasets(
        self.files,
        os.path.join(output_dir, f"{self.name if self.name else "RUN"}_{run_time}_combined.grib2")
      )
    
  def decompress_bz2(self, file_path: str) -> str:
    """
    Decompresses a file with the .bz2 extension.
    
    :param file_path: Path to the compressed file.
    :return: Path to the decompressed file.
    """
    assert file_path.endswith('.bz2'), "File must have a .bz2 extension"
    grib_file_path = file_path[:-4]  # Remove .bz2 extension
    print(f"Decompressing {file_path} to {grib_file_path}...")
    # Stream decompression (fixes memory issues and corruption)
    with bz2.BZ2File(file_path, 'rb') as compressed_file, open(grib_file_path, 'wb') as decompressed_file:
      for chunk in iter(lambda: compressed_file.read(1024 * 1024), b''):
        decompressed_file.write(chunk)

    os.remove(file_path)  # Remove the compressed file after successful decompression
    print(f"Decompressed and saved: {grib_file_path}")
    return grib_file_path

  def get_grib_records_signature(self, file_path: str) -> set[str]:
    """
    Extracts record metadata from a GRIB2 file using wgrib2.

    :param file_path: Path to the GRIB2 file.
    :return: Set of unique record metadata strings.
    """
    result = subprocess.run(
      ["wgrib2", file_path, "-s"],
      capture_output=True, 
      text=True, 
      check=True
    )
    records = set()
    
    for line in result.stdout.split("\n"):
      if line.strip():
        parts = line.split(":")
        key = ":".join(parts[2:6])  # Keep variable, level, and time info
        records.add(key)
    return records

  def merge_datasets(self, input_files: List[str], output_file: str) -> None:
    print("Merging datasets...")
    """
    Combine multiple GRIB files with optional deduplication
    
    Parameters:
    - input_files: List of paths to input GRIB files
    - output_file: Path to output combined GRIB file
    """
    out_dir = os.path.dirname(output_file)
    os.makedirs(out_dir, exist_ok=True)
    # Create a file to store the records
    records_file = os.path.join(out_dir, "inventory.txt")
  
    for i, file in enumerate(input_files):
      print(f"Processing {file} ({i+1}/{len(input_files)})...")
      if (i == 0):
        # First file, just copy it
        subprocess.run(
          f"cp {file} {output_file}",
          shell=True,
          check=True
        )
      else:
        # Subsequent files, append only new records
        subprocess.run(
          f"wgrib2 {file} -not_if {records_file} -append -grib {output_file}",
          shell=True,
          check=True,
          stdout=subprocess.DEVNULL
        )
      # Update the records file
      f = open(records_file, "w")
      f.write("\n".join(self.get_grib_records_signature(output_file)))
      f.close()
    # Clean up the records file
    subprocess.run(
      f"rm {records_file}",
      shell=True,
      check=True,
    )
    print(f"Merged file saved as: {output_file}")



# TESTING DA SHIT
if __name__ == "__main__":
  arome_downloader = Downloader(
    url_template='https://object.data.gouv.fr/meteofrance-pnt/pnt/{run_time}Z/arome/0025/{package}/arome__0025__{package}__{step}__{run_time}Z.grib2',
    update_times=[ 0, 3, 6, 12, 18 ],
    steps=[ '00H06H', '07H12H' ],
    packages=[ 'HP1' ],
    safe_timeout=6,
    date_format="iso"
  )
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
  arome_urls = arome_downloader.construct_urls()
  icon_urls = icon_downloader.construct_urls()
  print(icon_urls)
  icon_downloader.download()
  arome_downloader.download()

  # arome_downloader.merge_datasets(
  #     [
  #       "/workspaces/gdal/app/data/downloads/RUN_2025-03-20T03:00:00/arome__0025__HP1__00H06H__2025-03-20T03:00:00Z.grib2",
  #       "/workspaces/gdal/app/data/downloads/RUN_2025-03-20T03:00:00/arome__0025__HP1__00H06H__2025-03-20T03:00:00Z_c.grib2",
  #     ],
  #     "/workspaces/gdal/app/data/downloads/RUN_2025-03-20T03:00:00/arome_duplicate_combined.grib2"
  # )

  
  # f = open("test2.txt", "w")
  # f.write("\n".join(arome_downloader.get_grib_records_signature("/workspaces/gdal/app/data/downloads/RUN_2025-03-20T03:00:00/arome__0025__HP1__00H06H__2025-03-20T03:00:00Z.grib2")))
  # f.close()


  # icon_downloader.merge_datasets(
  #     [
  #       "/workspaces/gdal/app/data/downloads/RUN_2025032009/file1.grib2",
  #       "/workspaces/gdal/app/data/downloads/RUN_2025032009/file2.grib2",
  #       # "/workspaces/gdal/app/data/downloads/RUN_2025032009/icon-d2_germany_icosahedral_model-level_2025032009_001_2_t.grib2",
  #     ],
  #     "/workspaces/gdal/app/data/downloads/RUN_2025032009/arome_combined.grib2"
  # )
  # for url in arome_urls:
  #   print(url)
  # for url in icon_urls:
  #   print(url)
