import datetime
import os
import subprocess
from itertools import product

        # print(f"{base_url}/{run_hour}/{param}/icon-d2_germany_icosahedral_model-level_{run_time}_{step}_1_{param}.grib2.bz2")
        # FORMAT: BASE_URL/RUN_HOUR/PARAM/FILE_NAME
        # FILE_NAME: MODELINFOS_LEVELTYPE_RUNTIME_FORECASTSTEP_LEVEL_PARAM.grib2.bz2
        # url = f'https://object.data.gouv.fr/meteofrance-pnt/pnt/{run_time}/arome/0025/{param}/arome__0025__{param}__{STEP}__{run_time}.grib2'
        # FORMAT: BASE_URL/RUN_TIME/arome/0025/PARAM/FILE_NAME
        # FILE_NAME: arome__0025__PARAM__STEP__RUN_RIME.grib2


class Downloader:
  def __init__(self,
               url_template,
               update_times,
               steps,
               packages,
               safe_timeout=1,
               date_format="%Y%m%d%H",
               **extra_str_params
              ):
    self.url_template = url_template
    self.update_times = update_times # runs update times
    self.safe_timeout = safe_timeout # how many hours to wait before the next run is available
    self.date_format = date_format # default date format
    self.steps = steps # forecast steps
    self.packages = packages # forecast packages
    self.extra_str_params = self.parse_kwargs(**extra_str_params) # extra string parameters

  def parse_kwargs(self, **kwargs):
    # check that every kwargs has its corresponding template string value and vice versa
    # check and parse potential lists values
    # missing_keys = [key for key in kwargs if f'{{{key}}}' not in self.url_template]
    # if missing_keys:
    #   raise ValueError(
    #     f"Missing placeholders in template for keys: {', '.join(missing_keys)}"
    #   )
    list_keys = {k: v for k, v in kwargs.items() if isinstance(v, list)}
    single_keys = {k: v for k, v in kwargs.items() if not isinstance(v, list)}
    if not list_keys:
      return [ kwargs ]
    parsed_kwargs = []
    keys, values = zip(*list_keys.items())  # Extract keys and list values
    for combination in product(*values):  # Cartesian product of list values
        single_kwargs = dict(zip(keys, combination))  # Create a dict from list values
        single_kwargs.update(single_keys)  # Merge with single values
        parsed_kwargs.append(single_kwargs)
    return parsed_kwargs      

  def get_latest_run(self):
    utc_now = datetime.datetime.now(datetime.timezone.utc) # get current time
    last_possible_publish = utc_now - datetime.timedelta(hours=self.safe_timeout) # subtract safe_timeout from current time
    latest_run_hour = max(hour for hour in self.update_times if hour <= last_possible_publish.hour) # find the latest run time before or equal to the candidate time
    run_time = datetime.datetime(utc_now.year, utc_now.month, utc_now.day, latest_run_hour)
    return (
      (run_time.isoformat() if self.date_format == "iso" else run_time.strftime(self.date_format)), # specified format
      "{:02d}".format(latest_run_hour) # HH format for the run time
    )
  
  def construct_urls(self):
    # check inputs params
    assert len(self.steps) > 0, "at least one time step required"
    assert len(self.packages) > 0, "at least one package required"
    assert type(self.url_template) == str, "url template required"
    # get latest run time
    run_time, run_hour = self.get_latest_run()
    urls = []
    # construct url
    for package in self.packages: # loop through packages
      for step in self.steps: # loop through steps (time)
        for extra_params in self.extra_str_params: # loop through extra string parameters
          url = self.url_template.format(
            run_hour=run_hour,
            run_time=run_time,
            step=step,
            package=package,
            **extra_params
          )
          urls.append(url)
    return urls
  
  def download(self, output_dir=False):
    if not output_dir:
      run_time, run_hour = self.get_latest_run()
      output_dir = os.path.join(os.getcwd(), "data", "downloads", f"RUN_{run_time}")
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    urls = self.construct_urls()
    for url in urls:
      file_name = url.split("/")[-1]
      file_path = os.path.join(output_dir, file_name)
      print(f"Downloading {file_name} from {url} to {file_path}")
      subprocess.call(f'wget --output-document {file_path} {url}', shell=True)



# TEST
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
  steps=[ "000", "001", "002", "003" ],
  packages=[ 't', 'u', 'v' ],
  safe_timeout=1,
  date_format="%Y%m%d%H",
  levels=[1, 2, 3, 4]
  )


arome_urls = arome_downloader.construct_urls()
icon_urls = icon_downloader.construct_urls()

arome_downloader.download()

# for url in arome_urls:
#   print(url)
# for url in icon_urls:
#   print(url)

