from universal_downloads import Downloader
from grib_tools import GribTools
from typing import List, Optional
import re

def arome_025_helper(
  steps: List[str],
  packages: List[str],
  output_dir: Optional[str] = None,
  output_formats: Optional[List[str]] = ["cog", "hdf"],
  cog_parameters: Optional[List[str]] = ["all"],
  hdf_parameters: Optional[List[str]] = ["all"],
  levels: Optional[List[str]] = ["all"],
) -> GribTools:
  """
  helper to use arome 0.025° model

  @param steps: list of steps to download
  @param packages: list of packages to download
  @param output_dir: output directory for the downloaded files
  @param output_formats: list of output formats (cog, hdf)
  @param parameters: list of parameters to download
  @param levels: list of levels to download

  :raises AssertionError: if steps or packages are not valid
  
  :return: GribTools object
  """
  for step in steps:
    assert re.match(r'^[0-4][0-9]H[0-5][0-9]H$', step), f"steps should follow 00H06H 07H12H (max 49H51H), got {step}"
  for package in packages:
    assert re.match(r'^((HP[1-3])|(IP[1-5])|(SP[1-3]))$', package), f"available packages are: [HP1, HP2, HP3, IP1, IP2, IP3, IP4, IP5, SP1, SP2, SP3], got {package}"

  downloader = Downloader(
    url_template='https://object.data.gouv.fr/meteofrance-pnt/pnt/{run_time}Z/arome/0025/{package}/arome__0025__{package}__{step}__{run_time}Z.grib2',
    update_times=[ 0, 3, 6, 12, 18 ],
    safe_timeout=4,
    date_format="iso",
    packages=packages,
    steps=steps,
  )

  arome_processor = GribTools(
    name='arome_025',
    downloader=downloader,
    output_dir=output_dir,
    output_formats=output_formats,
    cog_parameters=cog_parameters,
    hdf_parameters=hdf_parameters,
    levels=levels,
  )
  return arome_processor


def arome_001_helper(
  steps: List[str],
  packages: List[str],
  output_dir: Optional[str] = None,
  output_formats: Optional[List[str]] = ["cog", "hdf"],
  cog_parameters: Optional[List[str]] = ["all"],
  hdf_parameters: Optional[List[str]] = ["all"],
  levels: Optional[List[str]] = ["all"],
) -> GribTools:
  """
  helper to use arome 0.001° model

  @param steps: list of steps to download
  @param packages: list of packages to download
  @param output_dir: output directory for the downloaded files
  @param output_formats: list of output formats (cog, hdf)
  @param parameters: list of parameters to download
  @param levels: list of levels to download

  :raises AssertionError: if steps or packages are not valid
  
  :return: GribTools object
  """
  for step in steps:
    assert re.match(r'^[0-5][0-9]H$', step), f"steps should follow 00H 01H, 02H... (max 51H), got {step}"
  for package in packages:
    assert re.match(r'^((HP1)|(SP[1-3]))$', package), f"available packages are: [HP1, SP1, SP2, SP3], got {package}"

  downloader = Downloader(
    url_template='https://object.data.gouv.fr/meteofrance-pnt/pnt/{run_time}Z/arome/001/{package}/arome__001__{package}__{step}__{run_time}Z.grib2',
    update_times=[ 0, 3, 6, 12, 18 ],
    safe_timeout=4,
    date_format="iso",
    packages=packages,
    steps=steps,
  )

  arome_processor = GribTools(
    name='arome_001',
    downloader=downloader,
    output_dir=output_dir,
    output_formats=output_formats,
    cog_parameters=cog_parameters,
    hdf_parameters=hdf_parameters,
    levels=levels,
  )
  return arome_processor

def icon_d2_helper( # Not 100% working
  steps: List[str],
  packages: List[str],
  output_dir: Optional[str] = None,
  output_formats: Optional[List[str]] = ["cog", "hdf"],
  cog_parameters: Optional[List[str]] = ["all"],
  hdf_parameters: Optional[List[str]] = ["all"],
  levels: Optional[List[str]] = ["all"],
) -> GribTools:
  for step in steps:
    assert re.match(r'^0[0-4][0-9]$', step), f"steps should follow 001, 002... (max 048), got {step}"

  for package in packages:
    assert package in [ "alb_rad", "alhfl_s",
    "apab_s", "ashfl_s", "asob_s", "asob_t", "aswdifd_s", "aswdifu_s", "aswdir_s", "athb_s", "athb_t", "aumfl_s", "avmfl_s", "c_t_lk", "cape_ml", "ceiling", "cin_ml", "clat", "clc", "clch", "clcl", "clcm", "clct", "clct_mod", "cldepth", "clon", "dbz_850", "dbz_cmax", "dbz_ctmax", "depth_lk", "echotop", "elat", "elon", "fi", "fr_ice", "fr_lake", "fr_land", "freshsnw", "grau_gsp", "h_ice", "h_ml_lk", "h_snow", "hbas_sc", "hhl", "hsurf", "htop_dc", "htop_sc", "hzerocl", "lai", "lpi", "lpi_max", "mh", "omega", "p", "plcov", "pmsl", "prg_gsp", "prr_gsp", "prs_gsp", "ps", "q_sedim", "qc", "qg", "qi", "qr", "qs", "qv", "qv_s", "rain_con", "rain_gsp", "relhum", "relhum_2m", "rho_snow", "rootdp", "runoff_g", "runoff_s", "sdi_2", "smi", "snow_con", "snow_gsp", "snowc", "snowlmt", "soiltyp", "synmsg_bt_cl_ir10.8", "synmsg_bt_cl_wv6.2", "t", "t_2m", "t_bot_lk", "t_g", "t_ice", "t_mnw_lk", "t_snow", "t_so", "t_wml_lk", "tch", "tcm", "tcond10_mx", "tcond_max", "td_2m", "tke", "tmax_2m", "tmin_2m", "tot_prec", "tqc", "tqc_dia", "tqg", "tqi", "tqi_dia", "tqr", "tqs", "tqv", "tqv_dia", "twater", "u", "u_10m", "uh_max", "uh_max_low", "uh_max_med", "v", "v_10m", "vis", "vmax_10m", "vorw_ctmax", "w", "w_ctmax", "w_i", "w_snow", "w_so", "w_so_ice", "ww", "z0" ], f"package {package} not supported, check what's supported on https://opendata.dwd.de/weather/nwp/icon-d2/grib/[any_run]" # not all packages follow the same pattern so yeah..

  downloader = Downloader(
    url_template='https://opendata.dwd.de/weather/nwp/icon-d2/grib/{run_hour}/{package}/icon-d2_germany_icosahedral_model-level_{run_time}_{step}_{levels}_{package}.grib2.bz2',
    update_times=[ 0, 3, 6, 9, 12, 15, 18, 21 ],
    safe_timeout=1,
    date_format="%Y%m%d%H",
    special_urls=[
      'https://opendata.dwd.de/weather/nwp/icon-d2/grib/{run_hour}/{invariant_params}/icon-d2_germany_icosahedral_time-invariant_{run_time}_000_0_{invariant_params}.grib2.bz2'
    ],
    invariant_params=[ 'clat', 'clon' ],
    levels=[ 1, 2 ], # should be user inputs but yeah..
    steps=steps,
    packages=packages,
  )

  icon_processor = GribTools(
    name='icon_d2',
    downloader=downloader,
    output_dir=output_dir,
    output_formats=output_formats,
    cog_parameters=cog_parameters,
    hdf_parameters=hdf_parameters,
    levels=levels,
    resolution=0.025,
  )
  return icon_processor


def aladin_helper( # Not final either
  packages: List[str],
  output_dir: Optional[str] = None,
  output_formats: Optional[List[str]] = ["cog", "hdf"],
  cog_parameters: Optional[List[str]] = ["all"],
  hdf_parameters: Optional[List[str]] = ["all"],
  levels: Optional[List[str]] = ["all"],
) -> GribTools:
  """
  helper to use aladin model

  @param steps: list of steps to download
  @param packages: list of packages to download
  @param output_dir: output directory for the downloaded files
  @param output_formats: list of output formats (cog, hdf)
  @param parameters: list of parameters to download
  @param levels: list of levels to download

  :raises AssertionError: if steps or packages are not valid
  
  :return: GribTools object
  """
  
  for package in packages:
    assert package in [
      "GEOPOTENTI", "HUMI_RELAT", "TEMPERATUR", "THETA_P_W", "VITESSE_VE", "WIND_U_COM", "WIND_V_COM", # some packages missing
    ], f"package {package} not supported, check what's supported on https://opendata.chmi.cz/meteorology/weather/nwp_aladin/Lambert_2.3km/[any_run]" # not all packages follow the same pattern so yeah..

  downloader = Downloader(
    url_template='https://opendata.chmi.cz/meteorology/weather/nwp_aladin/Lambert_2.3km/{run_hour}/ALADLAMB4opendata_{run_time}_{levels}{package}.grb.bz2{step}',
    update_times=[ 0, 6, 12, 18 ],
    safe_timeout=4,
    levels=["P00000", "P10000"], # should be user inputs but yeah.. -- other levels types: SURF, CLS, CLPsomething, MSL and P...
    date_format="%Y%m%d%H",
    steps=[""], # no steps for aladin
    packages=packages,
  )

  aladin_processor = GribTools(
    name='aladin',
    downloader=downloader,
    output_dir=output_dir,
    output_formats=output_formats,
    cog_parameters=cog_parameters,
    hdf_parameters=hdf_parameters,
    levels=levels,
  )
  
  return aladin_processor