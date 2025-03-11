import datetime

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
              ):
    self.url_template = url_template
    self.update_times = update_times # runs update times
    self.safe_timeout = safe_timeout # how many hours to wait before the next run is available
    self.date_format = date_format # default date format
    self.steps = steps # forecast steps
    self.packages = packages # forecast packages

  def get_latest_run(self):
    utc_now = datetime.datetime.now(datetime.timezone.utc) # get current time
    last_possible_publish = utc_now - datetime.timedelta(hours=self.safe_timeout) # subtract safe_timeout from current time
    latest_run_hour = max(hour for hour in self.update_times if hour <= last_possible_publish.hour) # find the latest run time before or equal to the candidate time
    run_time = datetime.datetime(utc_now.year, utc_now.month, utc_now.day, latest_run_hour)
    return (
      (run_time.isoformat() if self.date_format == "iso" else run_time.strftime(self.date_format)), # specified format
      "{:02d}".format(latest_run_hour) # HH format for the run time
    )
  
  def construct_url(self):
    # check inputs params
    assert len(self.steps) > 0, "at least one time step required"
    assert len(self.packages) > 0, "at least one package required"
    assert type(self.url_template) == str, "url template required"
    # get latest run time
    run_time, run_hour = self.get_latest_run()
    # construct url
    for package in self.packages:
      for step in self.steps:
        url = self.url_template.format(
          run_hour=run_hour,
          run_time=run_time,
          step=step,
          package=package
        )
        print(url)
  



# TEST
arome_downloader = Downloader(
  url_template='https://object.data.gouv.fr/meteofrance-pnt/pnt/{run_time}Z/arome/0025/{package}/arome__0025__{package}__{step}__{run_time}Z.grib2',
  update_times=[ 0, 3, 6, 12, 18 ],
  steps=[ '00H06H', '07H12H' ],
  packages=[ 'HP1', 'HP2' ],
  safe_timeout=4,
  date_format="iso"
)
icon_downloader = Downloader(
  url_template='https://opendata.dwd.de/weather/nwp/icon-d2/grib/{run_hour}/{package}/icon-d2_germany_icosahedral_model-level_{run_time}_{step}_1_{package}.grib2.bz2',
  update_times=[ 0, 3, 6, 9, 12, 15, 18, 21 ],
  steps=[ "000", "001", "002", "003" ],
  packages=[ 't', 'u', 'v' ],
  safe_timeout=1,
  date_format="%Y%m%d%H"
  )

print(arome_downloader.construct_url())
print(icon_downloader.construct_url())