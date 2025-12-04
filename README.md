# Urban Canopy Cover Analysis Tool
A Python tool that automatically downloads, processes, and analyzes urban tree canopy change for any U.S. city.
Given a city name, state name, and year range, the tool retrieves all required datasets (NLCD canopy layers, census tracts), computes zonal canopy trends across multiple years, and returns interactive maps, summary statistics, and datasets in multiple file formats.

This automates a workflow that would otherwise require manual, repetitive geoprocessing in ArcGIS Pro, making this analysis reproducible, scalable, and easy to run for any U.S. city.

## Features
- Automatic download of NLCD canopy datasets (2011–2021)
- Census tract extraction for the selected city
- Per-tract canopy statistics for multiple years
- Computation of canopy change (% and acres)
- Optional map and data export for all results
- CLI interface with simple arguments

## Installation
1. Create and activate a virtual environment
# Create environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
2. Install dependencies
pip install -r requirements.txt
Usage
Run the tool from the command line using main.py:

Basic example

python main.py --city "Portland" --state OR --start-year 2011 --end-year 2021
With a custom output directory

python main.py --city "Seattle" --state WA --start-year 2016 --end-year 2021 --output-dir seattle_results
Skip map/data exports

python main.py --city "Austin" --state TX --start-year 2011 --end-year 2019 --no-export
Display a canopy map plot

python main.py --city "Denver" --state CO --start-year 2011 --end-year 2021 --plot
Command Line Arguments
REQUIRED:

--city: City name ("Portland", "New York")
--state: State abbreviation (OR, NY)
--start-year: Start year (2011–2021)
--end-year: End year (2011–2021)
OPTIONAL:

--no-export: Skip exporting maps + data
--plot: Show matplotlib plot of final year canopy
--output-dir: Custom folder for exported files
Example Output
Processed canopy dataset (Xarray)
Census tracts with per-year canopy metrics
Summary statistics (printed to terminal)
Optional:

PNG maps
GeoPackage / shapefile
CSV summary tables
