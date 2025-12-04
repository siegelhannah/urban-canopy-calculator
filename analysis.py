"""
Functions to perform analysis on canopy cover % per census tract
"""

import pygeohydro as gh
import pandas as pd
from pygris import places, tracts, counties, states
import numpy as np
from rasterstats import zonal_stats
import os

def get_city_canopy(city_name, state_abbr, years):
    """
    Download NLCD tree canopy data for any US city via API
    
    Parameters:
        city_name: str (like "Portland")
        state_abbr: str (abbreviation like "OR")
        years: list of years to analyze (i.e. [2011, 2019, 2021])

    Returns: city boundary GeoDataFrame, clipped canopy cover xarray.Dataset (WGS84 lat/lon)

    >>> portland_city, portland_canopy = get_city_canopy("Portland", "OR", [2011, 2021])
    """
    # Get city boundary
    city = places(state=state_abbr, cb=True, cache=True) # cache=true to reuse already-downloaded files
    city = city[city['NAME'] == city_name]
    
    if len(city) == 0:
        raise ValueError(f"City '{city_name}' not found in {state_abbr}")
    
    # Download canopy data
    canopy = gh.nlcd_bygeom(
        city.geometry,
        resolution=30,
        years={"canopy": years},
        region="L48" # CONUS
    )
    
    return city, canopy # return city boundary geometry and canopy cover raster data clipped to city boundary



def get_city_tracts(city_boundary, state_abbr, year=2021):
    """
    Get census tracts that intersect with city boundary via pygris package (census API)
    
    Parameters:
        city_boundary: GeoDataFrame (city boundary from pygris.places() )
        state_abbr: str (abbreviation like "OR)
        year: int (Census year, default 2021)
    
    Returns: GeoDataFrame of census tracts clipped to city boundary (WGS84 lat/lon)

    >>> get_city_tracts(portland_city, "OR")
    """
    # Download all tracts in the state (cache=True to use already-downloaded ones)
    print(f"Downloading census tracts for {state_abbr}...")
    state_tracts = tracts(state=state_abbr, year=year, cache=True) # state_tracts is a GDF
    
    # spatial join (keeps tracts that touch city) - preserves all original tract columns, no duplication
    city_tracts = state_tracts[state_tracts.intersects(city_boundary.union_all())]
    
    # # clip the geometries to city boundary
    # city_tracts = city_tracts.copy()
    # city_tracts['geometry'] = city_tracts.geometry.intersection(city_boundary.union_all())


    # CLEAN GEOMETRIES: Remove empty and non-polygon geometries
    # (intersection can create LineStrings, Points, or empty geometries at boundaries)
    initial_count = len(city_tracts)
    
    city_tracts = city_tracts[~city_tracts.is_empty]  # Remove empty geometries
    city_tracts = city_tracts[city_tracts.geometry.type.isin(['Polygon', 'MultiPolygon'])]  # Keep only polygons
    city_tracts = city_tracts[city_tracts.is_valid]  # Remove invalid geometries
    
    after_clean = len(city_tracts)
    if initial_count > after_clean:
        print(f"  Removed {initial_count - after_clean} non-polygon/invalid geometries")
    

    # Project to UTM for accurate area calculation
    utm_crs = city_tracts.estimate_utm_crs()
    city_tracts_projected = city_tracts.to_crs(utm_crs)
    city_tracts_projected = city_tracts_projected[city_tracts_projected.geometry.area > 100]
    
    # Reproject back to WGS84
    city_tracts = city_tracts_projected.to_crs(epsg=4326)
    
    print(f"Found {len(city_tracts)} census tracts in city")
    
    return city_tracts



def calculate_tract_canopy_stats(tracts_gdf, canopy_dataset, years):
    """
    Calculate zonal statistics for tree canopy by census tract for each year, using rasterstats package
    Add this data to the census tracts geodataframe.
    
    Parameters:
        tracts_gdf: GeoDataFrame of census tracts
        canopy_dataset: xarray.Dataset (canopy data from pygeohydro, all years)
        years: list of years to process
    
    Returns: GeoDataFrame with canopy statistics added for each year
    """
    
    # copy to avoid modifying original
    tracts_with_stats = tracts_gdf.copy()

    # DEFENSIVE CHECK: Ensure clean geometries before processing
    tracts_with_stats = tracts_with_stats[
        tracts_with_stats.geometry.type.isin(['Polygon', 'MultiPolygon'])
    ]
    tracts_with_stats = tracts_with_stats[tracts_with_stats.is_valid]
    
    
    # Process each year
    for year in years:
        print(f"Calculating canopy stats for {year}...")
        
        # Get canopy data for this year
        canopy = canopy_dataset[f'canopy_{year}']
        
        # Save to temporary file (rasterstats needs a file path)
        temp_file = f"temp_canopy_{year}.tif"
        canopy.rio.to_raster(temp_file)
        
        # Calculate zonal statistics
        stats = zonal_stats(
            tracts_with_stats,
            temp_file,
            stats=['mean', 'min', 'max', 'sum', 'count', 'std'],    # stats of interest
            nodata=np.nan  # Explicitly handle NaN values
        )
        
        # Add statistics to GeoDataFrame
        tracts_with_stats[f'canopy_mean_{year}'] = [s['mean'] if s['mean'] is not None else np.nan for s in stats]
        tracts_with_stats[f'canopy_min_{year}'] = [s['min'] if s['min'] is not None else np.nan for s in stats]
        tracts_with_stats[f'canopy_max_{year}'] = [s['max'] if s['max'] is not None else np.nan for s in stats]
        tracts_with_stats[f'canopy_std_{year}'] = [s['std'] if s['std'] is not None else np.nan for s in stats]
        # count represents the number of 30m x 30m pixels in the tract:
        tracts_with_stats[f'canopy_pixels_{year}'] = [s['count'] if s['count'] is not None else 0 for s in stats]
        # Clean up temp file
        os.remove(temp_file)
    
    return tracts_with_stats # geodataframe with stats added



def calculate_mean_canopy_change(tracts_gdf, start_year, end_year):
    """
    Calculate MEAN canopy change between two years
    Add this data to the gdf.
    
    Parameters:
        tracts_gdf: GeoDataFrame of tracts w/ canopy statistics
        start_year: int
        end_year: int
    
    Returns: GeoDataFrame with change metrics added
    """
    tracts_with_change = tracts_gdf.copy() # again copy gdf

    # FINAL SAFETY CHECK: Ensure geometries are still valid
    tracts_with_change = tracts_with_change[
        tracts_with_change.geometry.type.isin(['Polygon', 'MultiPolygon'])
    ]
    tracts_with_change = tracts_with_change[tracts_with_change.is_valid]
    
    
    # Calculate absolute change (percentage points)
    tracts_with_change['canopy_change_pct'] = (
        tracts_with_change[f'canopy_mean_{end_year}'] - 
        tracts_with_change[f'canopy_mean_{start_year}']
        )
    
    # Calculate relative change (percent of original)
    tracts_with_change['canopy_change_relative'] = (
       (tracts_with_change['canopy_change_pct'] / 
        tracts_with_change[f'canopy_mean_{start_year}'].replace(0, np.nan)) * 100
        )
    
    # Categorize change using percentage points
    def categorize_change(pct_change):
        if pd.isna(pct_change):
            return 'No Data'
        elif pct_change < -5:
            return 'Major Loss'
        elif pct_change < -2:
            return 'Moderate Loss'
        elif pct_change < 2:
            return 'Stable'
        elif pct_change < 5:
            return 'Moderate Gain'
        else:
            return 'Major Gain'
    
    tracts_with_change['change_category'] = tracts_with_change['canopy_change_pct'].apply(categorize_change)
    
    # Calculate canopy acres (each 30m pixel, counted by [count] = 900 sq meters = 0.222 acres)
    pixel_to_acres = 0.222
    for year in [start_year, end_year]:
        tracts_with_change[f'canopy_acres_{year}'] = (
            (tracts_with_change[f'canopy_mean_{year}'] / 100) * 
            tracts_with_change[f'canopy_pixels_{year}'] * 
            pixel_to_acres
        )
    
    tracts_with_change['canopy_acres_change'] = (
        tracts_with_change[f'canopy_acres_{end_year}'] - 
        tracts_with_change[f'canopy_acres_{start_year}']
    )
        
    return tracts_with_change # gdf with new columns added


