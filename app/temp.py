import os
import subprocess
import tempfile
from typing import Optional, Sequence, Literal

import numpy as np
import xarray as xr

def regrid_icon_with_cdo(
    input_path: str,
    output_path: str,
    resolution: float = 0.1,
    method: Literal["bilinear", "conservative", "nearest"] = "nearest",
    area: Optional[Sequence[float]] = None,
) -> None:
    """
    Regrid an ICON/ICON-D2 unstructured GRIB2 file to a regular lon-lat grid using CDO.

    Parameters
    ----------
    input_path
        Path to the source ICON-D2 GRIB2 file.
    output_path
        Path to write the regridded file (GRIB2 or NetCDF; CDO infers from extension).
    resolution
        Target grid spacing in degrees (∆lat = ∆lon). Default is 0.1°.
    method
        Remapping method:
          - "bilinear"     → CDO remapbil  (only for quadrilateral source grids)
          - "conservative" → CDO remapcon2
          - "nearest"      → CDO remapnn
    area
        [south, west, north, east] in degrees for the target domain.
        If None, defaults to global: [-90, -180, 90, 180].
    """
    # https://wiki.mpimet.mpg.de/doku.php?id=analysis:postprocessing_icon:regridding:shell:start

    # 1) Read the ICON grid from GRIB via xarray/cfgrib
    ds = xr.open_dataset(
        input_path,
        engine="cfgrib",
        backend_kwargs={"filter_by_keys": {"edition": 2}},
        decode_cf=False,
    )

    # 2) Pull cell-center & corner coords
    #    CF names vary: try CLAT/CLON first, then tlat/tlon
    latc = ds.get("CLAT") or ds.get("tlat")
    lonc = ds.get("CLON") or ds.get("tlon")
    #    corners: 
    latv = ds["ELAT"]  # shape (nv, ncell)
    lonv = ds["ELON"]  # same

    if latc is None or lonc is None:
        raise RuntimeError("No CLAT/CLON (or tlat/tlon) found in the GRIB")

    ncell = latc.size
    nv = latv.shape[0]  # number of vertices per cell

    # 3) Build unstructured-grid description text (CDO Appendix D.2) :contentReference[oaicite:0]{index=0}
    grid_txt = [
        "gridtype = unstructured",
        f"gridsize = {ncell}",
        f"nvertex  = {nv}",
        # flatten CLON/CLAT for xvals/yvals
        "xvals    = " + " ".join(map(str, lonc.values.flatten())),
        "yvals    = " + " ".join(map(str, latc.values.flatten())),
        # flatten ELON/ELAT for xbounds/ybounds, one cell after another
        "xbounds  = " + " ".join(map(str, lonv.values.flatten())),
        "ybounds  = " + " ".join(map(str, latv.values.flatten())),
    ]

    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as gf:
        gf.write("\n".join(grid_txt))
        gf.flush()
        src_grid_file = gf.name

    # 4) Create the target regular lon-lat grid file
    if area is None:
        south, west, north, east = -90.0, -180.0, 90.0, 180.0
    else:
        south, west, north, east = area

    nx = int((east  - west)  / resolution) + 1
    ny = int((north - south) / resolution) + 1

    tgt_grid_txt = (
        "gridtype = lonlat\n"
        f"gridsize = {nx * ny}\n"
        f"xsize    = {nx}\n"
        f"ysize    = {ny}\n"
        f"xname=lon\n"
        f"xlongname=longitude\n"
        f"xunits=degrees_east\n"
        f"yname=lat\n"
        f"ylongname=latitude\n"
        f"yunits=degrees_north\n"
        f"xfirst   = {west}\n"
        f"yfirst   = {south}\n"
        f"xinc     = {resolution}\n"
        f"yinc     = {resolution}\n"
    )
    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as gf2:
        gf2.write(tgt_grid_txt)
        gf2.flush()
        tgt_grid_file = gf2.name

    # 5) Map our method to CDO operator
    op = {
        "nearest":      "remapnn",
        "conservative": "remapcon2",
        "bilinear":     "remapbil",
    }[method]

    # 6) First tell CDO “this is an unstructured grid”
    tmp1 = tempfile.NamedTemporaryFile(suffix=".nc", delete=False).name
    subprocess.run(
        ["cdo", f"setgrid,{src_grid_file}", input_path, tmp1],
        check=True
    )
    # 7) Then remap to regular
    subprocess.run(
        ["cdo", f"{op},{tgt_grid_file}", tmp1, output_path],
        check=True
    )

    # 8) Cleanup
    for fn in (src_grid_file, tgt_grid_file, tmp1):
        try:
            os.remove(fn)
        except OSError:
            pass
