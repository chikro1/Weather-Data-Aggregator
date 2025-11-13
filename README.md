# Weather Data Aggregator

Flexible tooling to collect, cache, and explore weather observations and forecasts from multiple providers. The repo bundles:

- Provider clients with batch/concurrency utilities
- A configurable export runner for automated data pulls
- Offline API notes and example notebooks

This README documents every moving part so you can configure, run, and extend the project confidently.

---

## Repository Layout

```
.
├── clients/                   # Provider-specific API clients + batch mixin
├── api_docs/                  # Offline HTML docs/links for each provider
├── data/                      # Cached CSV output (provider/location/date)
├── logs/                      # Export logs (created on demand)
├── notebooks/                 # Demos and export notebooks
├── weather_config.json        # Project configuration (copy from *.template)
├── weather_config.json.template
├── weather_data_export.py     # Continuous exporter (CLI)
├── requirements.txt           # Python dependencies
└── README.md
```

---

## Supported Providers

Implemented under `clients/` and configured via `weather_config.json`:

- `tomorrow_io` – Tomorrow.io Timelines (5m/1h current, forecast, recent history)
- `open_meteo` – Open‑Meteo forecast + archive (hourly/daily variables)
- `visual_crossing` – Visual Crossing timeline (current/forecast/history)
- `noaa_isd` – NOAA ISD via Access Data Service (global‑hourly)
- `noaa_lcd` – NOAA LCD via Access Data Service (local‑climatological‑data)
- `weatherapi_com` – WeatherAPI.com (current/forecast/history/future)
- `openweather` – OpenWeather (current + hourly history)
- `weatherbit` – Weatherbit (hourly forecast + sub‑hourly history)
- `meteostat` – Meteostat Python SDK (hourly)
- `nasa_power` – NASA POWER hourly point
- `iem_asos` – Iowa Environmental Mesonet ASOS 1‑minute
- `copernicus_era5_single` – ERA5 single levels (NetCDF)
- `copernicus_era5_land` – ERA5‑Land (NetCDF, 0.1°)
- `copernicus_era5_pressure` – ERA5 pressure levels (NetCDF)
- `copernicus_era5_land_timeseries` – ERA5‑Land point CSV series

Each client exposes single‑call and batch helpers (for concurrency) and normalises common inputs like locations and date/time ranges. See inline docstrings and the examples below.

---

## Environment & Installation

Prereqs: Python 3.9+.

Setup a virtualenv and install deps:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Notes:
- `matplotlib` runs with the `Agg` backend for headless rendering.
- Copernicus parsing uses `xarray` and `netcdf4`; ensure system libs for NetCDF/HDF5 are present in your environment.
- Optional SDKs are listed in `requirements.txt` and are imported lazily with clear error messages if missing.

---

## Configuration (`weather_config.json`)

Start from the template:

```
cp weather_config.json.template weather_config.json
```

Fill in provider credentials and review location metadata. Top‑level keys:

- `providers` – One object per provider with credentials, URLs, defaults, and batching hints.
- `locations` – Named sites with `lat`/`lon` plus provider‑specific extras (e.g., station IDs, Copernicus areas).

Location extras used by the exporter:
- NOAA ISD: `noaaIsdStation`
- NOAA LCD: `noaaLcdStation`
- IEM ASOS: `iemStation`, `iemNetwork`
- Copernicus ERA5/Pressure: `copernicusEra5Area` (N, W, S, E bounding box)
- Copernicus ERA5‑Land: `copernicusEra5LandArea`

Provider config highlights (see template for full shape):
- Tomorrow.io: `apiKeys[]`, `baseUrl`, `defaultTimesteps`, `defaultUnits`
- Open‑Meteo: `forecastUrl`, `historicalUrl`, `defaultHourly[]`, `defaultDaily[]`, `defaultUnits{}`
- Visual Crossing: `apiKey`, `baseUrl`, `defaultUnitGroup`, `defaultInclude[]`
- NOAA Access (ISD/LCD): `dataset`, `token`, `defaultDataTypes[]`, `responseFormat`
- WeatherAPI.com: `apiKeys[]` or `apiKey`, `baseUrl`, `defaultForecastDays`, `defaultAqi`, `defaultAlerts`
- OpenWeather: `apiKey`, `currentUrl`, `historyUrl`, `defaultUnits`, `defaultHistoryType`
- Weatherbit: `apiKey`, `forecastUrl`, `historicalUrl`, `defaultUnits`, `defaultHours`, `defaultTimezone`
- Meteostat: `defaultTimezone`, `includeModelData`, `requestThrottleSeconds`
- NASA POWER: `baseUrl`, `parameters[]`, `community`, `timeStandard`, `format`
- Copernicus: `apiUrl`, `apiKey`, `dataset`, `mode`, `productType`, `variables[]`, `timeSteps[]`, `pressureLevels[]`, `format`, `grid[]`, `batchSize`, `retryMax`, `sleepMax`

Security: never commit real keys or tokens. Keep only the template under version control.

---

## Export Runner (`weather_data_export.py`)

The exporter fetches data for all enabled providers across all configured locations and date ranges, writes daily CSVs, and optionally renders a coverage heatmap.

Key defaults (top of script):
- Dates: `START_DATE = 2000-01-01`, `END_DATE = 2025-11-05` (override via CLI)
- Cooldown: `COOLDOWN_SECONDS = 300` between cycles
- Pending flush cap: `MAX_PENDING_REQUESTS_PER_FLUSH = 25`
- Provider toggles: Copernicus providers enabled by default; others disabled. Override with `--providers`.

CLI usage:

```
python3 weather_data_export.py [--once] [--skip-coverage] \
  [--providers p1,p2,...] [--since YYYY-MM-DD] [--until YYYY-MM-DD] \
  [--limit-locations N]
```

Flags:
- `--once` – Run a single export cycle and exit
- `--skip-coverage` – Skip coverage chart generation
- `--providers` – Comma‑separated provider keys to run; forces those toggles on for this run
- `--since`, `--until` – Limit the date range for this run (inclusive)
- `--limit-locations` – Only process the first N locations

Behaviour:
- Skips days already cached to `data/<provider>/<location>/<YYYY-MM-DD>.csv`, except always revisits “today”.
- Runs providers concurrently; each client also batches its own API calls with a thread pool.
- Writes logs to `logs/weather_export.log` and progress bars via `tqdm`.
- Renders `data/cache_coverage.png` unless `--skip-coverage` is given.

Examples:
- Run Copernicus ERA5‑Land only for Jan 2020, first 2 locations:
  `python3 weather_data_export.py --once --providers copernicus_era5_land --since 2020-01-01 --until 2020-01-31 --limit-locations 2`
- Refresh Open‑Meteo + Visual Crossing for last week: 
  `python3 weather_data_export.py --once --providers open_meteo,visual_crossing --since 2025-11-01 --until 2025-11-08`

Provider notes:
- Tomorrow.io: Only last ~24h of history are requested by default; fields and timesteps are configurable.
- Open‑Meteo/Visual Crossing: Uses contiguous missing‑day spans and range endpoints with provider‑specific max days per request.
- NOAA ISD/LCD: Requires station IDs in `locations`; token configured under provider.
- IEM ASOS: Requires `iemStation` and `iemNetwork` per location.
- Copernicus: Grid downloads (NetCDF) or point CSVs; areas are read from `locations` extras when required.
- OpenWeather/WeatherAPI/Weatherbit: Use their hourly history/forecast capabilities; clients normalise timestamps/units where possible.

Outputs:
- CSV data per day: `data/<provider>/<location>/<YYYY-MM-DD>.csv`
- Coverage chart: `data/cache_coverage.png`
- Logs: `logs/weather_export.log`

Stopping: Press `Ctrl+C`. The script exits immediately in `--once` mode or after sleep if interrupted between cycles.

---

## Provider Clients (Python)

The `clients/` package contains one module per provider plus shared utilities:

- `clients/__init__.py` – `BatchExecutorMixin` implements batched, threaded execution (`_run_batch`) used by all clients.
- `clients/request_utils.py` – `build_request_headers()` generates randomized headers to reduce request fingerprinting.
- `clients/tomorrow_io_client.py` – Timelines (`get_forecast`, `get_historical`, `*_batch`), with API key rotation.
- `clients/open_meteo_client.py` – Forecast + archive wrappers with unit overrides; `get_*_batch` helpers.
- `clients/visual_crossing_client.py` – Timeline requests composed via path segments; JSON parsing to per‑day/hour rows.
- `clients/noaa_access_client.py` – Access Data Service (ISD/LCD) with token header; station‑scoped requests and batch helpers.
- `clients/iem_asos_client.py` – 1‑minute CSV to Pandas DataFrame; station/network + variable selection.
- `clients/meteostat_client.py` – Meteostat `Hourly(Point)` to list‑of‑dicts records.
- `clients/nasa_power_client.py` – Hourly point parameters; configurable list of variables.
- `clients/openweather_client.py` – Current + history (`type=hour`) with UNIX timestamp conversions.
- `clients/weatherapi_com_client.py` – Forecast/history/current/future with API key rotation and language/AQI/alerts options.
- `clients/weatherbit_client.py` – Hourly forecast and sub‑hourly history with timezone parameter support.
- `clients/copernicus_cds_client.py` – CDS API for ERA5/ERA5‑Land/Pressure/Timeseries; parses NetCDF/CSV to Pandas and supports area boxes.

See the module docstrings for official API references; additional HTML quick references live in `api_docs/`.

---

## Notebooks

Located under `notebooks/` and driven by the same configuration file:

- `weather_api_clients_demo.ipynb` – Interactive walkthrough of all clients (single calls and batch requests).
- `weather_data_export.ipynb` – Notebook version of the exporter (skips cached days and renders the coverage chart).

Run with your preferred Jupyter environment after activating the virtualenv.

---

## Troubleshooting

- Missing packages: Error messages point to the `pip install` line for the specific client (e.g., `cdsapi`, `meteostat`). Install the package and retry.
- NetCDF/HDF5 issues: Ensure system libraries are available for `netcdf4`/`xarray`.
- API rate limits: Lower provider `batchSize` in `weather_config.json` or increase `requestThrottleSeconds` where supported.
- Empty CSVs: Some providers legitimately return no data for a day/location; the exporter logs these as skipped.
- Credentials: Verify keys/tokens in `weather_config.json` and that location extras (stations/areas) are present where required.

---

## Legal

You are responsible for complying with each provider’s Terms of Service and attribution requirements. This project does not include any provider credentials.

---

## License

No explicit license provided. Add your preferred license if you plan to distribute this project.
