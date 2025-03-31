from helpers import arome_025_helper


arome_025 = arome_025_helper(
  steps=[ "00H06H" ],
  packages=[ "HP1" ],
  output_formats=[ "cog", "hdf" ],
  parameters=[ "TMP" ],
  levels=[ "all" ]
)

print(arome_025.downloader.get_latest_run())