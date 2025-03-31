# grib downloader for multiple models

/!\ WIP /!\

this should allow you to:

- download some grib2 files
- convert them to COG or HDF5

currently tested with.
- Arome 025 (Meteo France) grib2 files
- icon-d2 (DWD) grib2 files

Should work without problems for:
- other Arome models
- other icon models
- Aladin (chmi)

Untested for the rest (Work in progress!)

If you find some use of it... Enjoy!

## Usage

Usage with docker (and devcontainer) is highly recommended.

1. Clone the repo
2. Build the docker image (or use the devcontainer)
3. Use in the container at your convenience:
 - `grib_tools` to process the grib2 files
 - `universal_downloads` to download the grib2 files
 - `helpers` preconfig for arome and icon-d2 models

PS. I know it is not really detailed. will improve that SoonTM

## Usefuls links:

### data source:

- https://meteo.data.gouv.fr
- https://opendata.dwd.de/weather/nwp/
- https://opendata.chmi.cz/meteorology/weather/nwp_aladin/

