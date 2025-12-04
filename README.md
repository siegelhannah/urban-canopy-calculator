# Urban Canopy Cover Analysis Tool
A Python tool that automatically downloads, processes, and analyzes urban tree canopy change for any U.S. city.
Given a city name, state name, and year range, the tool retrieves all required datasets (NLCD canopy layers, census tracts), computes zonal canopy trends across multiple years, and returns interactive maps, summary statistics, and datasets in multiple file formats.

This automates a workflow that would otherwise require manual, repetitive geoprocessing in ArcGIS Pro, making this analysis reproducible, scalable, and easy to run for any U.S. city.

## Features
- Automatic download of NLCD canopy datasets (available 2011–2021)
- Automatic census tract extraction for the selected city
- Per-tract calculation of canopy statistics for multiple years
- Computation of canopy change (% and acres)
- Optional map and data export for all results
- CLI interface with simple arguments (city and state name, year range)

## Installation
1. Create and activate a virtual environment
```python
# Create environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

2. Install dependencies
```python
pip install -r requirements.txt
```

## Usage
Run the tool from the command line using main.py:

Basic example:
```python
python main.py --city "Portland" --state OR --start-year 2011 --end-year 2021
```

With a custom output directory
```python
python main.py --city "Seattle" --state WA --start-year 2016 --end-year 2021 --output-dir seattle_results
```

Skip map/data exports
```python
python main.py --city "Austin" --state TX --start-year 2011 --end-year 2019 --no-export
```

Display a canopy map plot
```python
python main.py --city "Denver" --state CO --start-year 2011 --end-year 2021 --plot
```

## Command Line Arguments
REQUIRED:

- --city: City name ("Portland", "New York")
- --state: State abbreviation (OR, NY)
- --start-year: Start year (2011–2021)
- --end-year: End year (2011–2021)

OPTIONAL:

- --no-export: Skip exporting maps + data
- --plot: Show supplemental matplotlib plot of final year's raw NLCD canopy coverage data
- --output-dir: Customize folder name for exported files (default is {city}_{state}_outputs/)

## Outputs

HTML MAP FILES:
- Yearly maps of mean canopy by census tract
- Choropleth map of mean canopy change by census tract

SHAPEFILES:
- City boundary shapefile
- Shapefile with analysis results (includes GEOID, start year mean canopy, end year mean canopy, percent canopy change, change categories, change in acres)

GEODATAFRAMES in multiple formats:
- Geopackage (for compatibility across ArcPro, Python, etc)
- CSV with WKT geometry

PRINTED OUTPUTS / PLOTS:
- Summary statistics printed to terminal
- Supplementary plot of final year's raw NLCD canopy coverage data

