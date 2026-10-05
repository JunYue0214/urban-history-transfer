# Download plan (execution 1005-6) - HUMAN-EXECUTED ONLY

**Claude Code has not downloaded, and is not authorized to download, any real
research data.** Everything below is to be run by the human operator. Status of
the design is PROVISIONAL, so the plan has a mandatory documentation-first
step. **PI acquisition recommendation: NOT YET** (authorize data acquisition
only after Step 0 resolves the listed unknowns).

## Target

| Item | Value |
|---|---|
| Dataset | Yale Center for Earth Observation (YCEO) Surface Urban Heat Islands, Version 4, 2003-2018 (Chakraborty & Lee 2023), NASA SEDAC |
| DOI | 10.7927/S5M5-ZK14 (verified via multiple search snippets; landing page not read by Claude) |
| Landing/download page | https://sedac.ciesin.columbia.edu/data/set/sdei-yceo-sfc-uhi-v4/data-download |
| Documentation PDF | https://sedac.ciesin.columbia.edu/downloads/docs/sdei/sdei-yceo-sfc-uhi-v4-documentation.pdf |
| File wanted | the package labelled "UHI (urban cluster means)" - Shapefile, reported ~4.7 MB zip |
| NOT wanted | pixel-level GeoTIFF packages (e.g. winter-pixel zip, reported 814 MB); global rasters; MODIS LST |
| Access | free NASA Earthdata login required (SEDAC) |
| Expected volume | ~5 MB for the primary file; monthly/yearly cluster packages: UNKNOWN (record sizes at Step 0) |

## Step 0 - documentation only (before any data file)

Open the two pages above in a browser (documentation, not research data) and
send the PI the following, copied from the pages:

1. exact filenames and sizes of every package listed (record in
   `results/1005-6/data_manifest_template.csv`, rows THERM-001/003);
2. the shapefile attribute table (field names, meaning, units), geometry type,
   cluster ID definition, whether name/country fields exist;
3. whether annual/summer/winter day/night cluster means (2003-2018) are in the
   "urban cluster means" file or in a different package;
4. exact definitions of "summer"/"winter" for tropical clusters and the
   rural-pixel/elevation filter thresholds in v4;
5. the number of urban clusters in v4 and the filtering rules;
6. whether Terra and Aqua are combined for night values and how;
7. the licence/citation statement.

If Step 0 shows that the cluster file lacks annual nighttime means or any
geometry/coordinates, the design must be re-evaluated (stay PROVISIONAL or
REJECTED) and no further acquisition should happen.

## Step 1 - download the primary file (after PI approval)

Preferred (browser, because Earthdata login is interactive): log in at the
SEDAC page, download "UHI (urban cluster means)" into
`D:\claudecode\urban-history-transfer\data\raw\thermal_response\yceo_suhi_v4\`
keeping the original filename.

If you have a direct file URL and an Earthdata bearer token (generated in your
Earthdata profile), the project script can fetch it. PowerShell, session-scoped
variables only (no `setx`, no global proxy/Git changes):

```powershell
cd D:\claudecode\urban-history-transfer

# only if your network needs Clash; session-scoped, discarded when the window closes
$env:HTTP_PROXY  = "http://127.0.0.1:7890"
$env:HTTPS_PROXY = "http://127.0.0.1:7890"

# only for the script route: token read from an environment variable, never written to disk
$env:EARTHDATA_TOKEN = "<paste token>"

conda run -n py311 python scripts/download_thermal_response.py `
  --url "<EXACT_FILE_URL_FROM_SEDAC_PAGE>" `
  --dest "data/raw/thermal_response/yceo_suhi_v4" `
  --dataset-key yceo_suhi_v4 `
  --auth-env EARTHDATA_TOKEN `
  --confirm-human-operator
```

The script refuses to overwrite, resumes `.part` files, logs a UTC timestamp,
size and SHA-256 in `<file>.download_log.json`, and strips the token on
cross-host redirects. `<EXACT_FILE_URL_FROM_SEDAC_PAGE>` is intentionally not
filled in: Claude could not read the page, and no URL is guessed.

## Step 2 - verify

```powershell
conda run -n py311 python scripts/verify_thermal_response.py `
  "data/raw/thermal_response/yceo_suhi_v4/<FILENAME>.zip" `
  --min-bytes 1000000 `
  --require-columns "<FIELD_NAMES_FROM_STEP_0, comma separated>"
```

The verifier checks existence, size, SHA-256 (add `--sha256 <hex>` if SEDAC
publishes one), ZIP integrity, the presence of .shp/.shx/.dbf members and the
DBF field names. Record the observed SHA-256 in the manifest. Do NOT commit
the file (data/raw is untracked research data).

## Step 3 - report back

Return the verifier JSON and the Step 0 findings to the PI; the Gate 2
execution prompt then fixes the schema-dependent items in the pre-registration
amendment log before R is analysed.

## Optional, only if the PI wants the alternate rural-reference check

Yang et al. 2024 (DOI 10.6084/m9.figshare.24821538) is distributed as a
Figshare README with links to Baidu Cloud / Google Drive and a gridded 1 km
Earth Engine collection; no scriptable city-table URL was verified. Do NOT
download its gridded data. Step 0 equivalent: read its Figshare README and
report whether a city-level table exists, its size, columns and end year.

## Not required

* No global raster download is needed for the primary design.
* No new climate data: nested C is built from fields already in the UCDB files
  downloaded in 1005-4 (checked locally).
