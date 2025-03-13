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
        safe_timeout: int = 1,
        date_format: str = "%Y%m%d%H",
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
        :param extra_str_params: Additional string parameters for URL formatting.
        """
        self.url_template = url_template
        self.update_times = update_times
        self.safe_timeout = safe_timeout
        self.date_format = date_format
        self.steps = steps
        self.packages = packages
        self.extra_str_params = self._parse_kwargs(**extra_str_params)

    def _parse_kwargs(self, **kwargs: Union[str, List[str]]) -> List[Dict[str, str]]:
        """
        Processes extra keyword arguments to support both single values and lists.
        
        :param kwargs: Extra parameters for string formatting.
        :return: A list of dictionaries with each combination of parameters.
        :raises ValueError: If a key in kwargs is not found in the URL template.
        """
        # Optionally, uncomment to enforce that all keys exist in the template:
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
                    urls.append(url)
        return urls

    def download(self, output_dir: Optional[str] = None) -> None:
        """
        Downloads files from constructed URLs and saves them to the output directory.
        
        :param output_dir: Optional directory to save downloads. If not provided, a default directory is used.
        """
        run_time, _ = self.get_latest_run()
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "data", "downloads", f"RUN_{run_time}")

        os.makedirs(output_dir, exist_ok=True)
        urls = self.construct_urls()

        for url in urls:
            file_name = os.path.basename(url)
            file_path = os.path.join(output_dir, file_name)
            print(f"Downloading {file_name} from {url} to {file_path}")
            subprocess.call(f'wget --output-document {file_path} {url}', shell=True)
            
            # HANDLE DECOMPRESSION
            if file_name.endswith('.bz2'):
                grib_file_path = file_path[:-4]  # Remove .bz2 extension
                print(f"Decompressing {file_name} to {grib_file_path}...")

                # Stream decompression (fixes memory issues and corruption)
                with bz2.BZ2File(file_path, 'rb') as compressed_file, open(grib_file_path, 'wb') as decompressed_file:
                    for chunk in iter(lambda: compressed_file.read(1024 * 1024), b''):
                        decompressed_file.write(chunk)

                # os.remove(file_path)  # Remove the compressed file after successful decompression
                print(f"Decompressed and saved: {grib_file_path}")

# TESTING DA SHIT
if __name__ == "__main__":
  arome_downloader = Downloader(
    url_template='https://object.data.gouv.fr/meteofrance-pnt/pnt/{run_time}Z/arome/0025/{package}/arome__0025__{package}__{step}__{run_time}Z.grib2',
    update_times=[ 0, 3, 6, 12, 18 ],
    steps=[ '00H06H', '07H12H' ],
    packages=[ 'HP1', 'HP2' ],
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
    levels=[ 1, 2 ]
    )
  arome_urls = arome_downloader.construct_urls()
  icon_urls = icon_downloader.construct_urls()
  icon_downloader.download()
  arome_downloader.download()
  # for url in arome_urls:
  #   print(url)
  # for url in icon_urls:
  #   print(url)
