# grib downloader for multiple models

/!\ WIP /!\

this should allow you to:

- download some grib2 files
- convert them to COG or HDF5

currently tested and working with.
- Arome (Meteo France)
- icon-d2 (DWD)
- icon-eu (DWD)
- icon-global (DWD)
- Aladin (CHMI)

Curently tested but not working with:
- UKV (UK Met Office)

Untested for the rest (Work in progress!)

If you find some use of it... Enjoy!

## Usage

Usage with docker (and devcontainer) is highly recommended.

1. Clone the repo
2. Build the docker image (or use the devcontainer)
3. Use in the container at your convenience the python scripts -- examples in `app/main.py`


