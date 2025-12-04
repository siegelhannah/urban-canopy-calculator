from analysis import get_city_canopy, get_city_tracts, calculate_tract_canopy_stats, calculate_mean_canopy_change
from visualization_export import export_all_outputs

import numpy as np
import matplotlib.pyplot as plt
import argparse


### MAIN ANALYSIS WORKFLOW FUNCTION ###
def analyze_city_canopy(city_name, state_abbr, start_year, end_year, export=True):
    """
    Complete analysis pipeline for city tree canopy change
    1. Download NLCD data within city boundary
    2. get gdf of city's census tracts
    3. calculate per-tract stats, per-year
    4. calculate per-tract change metric (AVERAGE canopy cover % change per tract)
    
    Parameters:
        city_name: str
        state_abbr: str
        start_year: int
        end_year: int
        export: bool (whether or not to export maps)
    
    Returns: tuple (city_boundary geodataframe, tracts_with_analysis geodataframe, canopy_dataset xarray.Dataframe)

    >>> city_boundary, portland_analysis, canopy_dataset = analyze_city_canopy("Portland", "OR", 2011, 2021)
    """
    # list of all years needed
    years = list(range(start_year, end_year + 1))
    # Filter to only years with NLCD data (2011-2021)
    available_years = [y for y in years if y in np.arange(2011, 2022)]
    
    if len(available_years) == 0:
        raise ValueError(f"No NLCD data available for years {start_year}-{end_year}")
    
    print(f"Analyzing {city_name}, {state_abbr} for years: {available_years}")

    # 1. Get city boundary and canopy data using function
    print("\nStep 1: Downloading canopy data")
    city_boundary, canopy_data = get_city_canopy(city_name, state_abbr, available_years)
    canopy_dataset = list(canopy_data.values())[0]
    
    # 2. Get census tracts gdf using function
    print("\nStep 2: Getting census tracts")
    city_tracts = get_city_tracts(city_boundary, state_abbr)
    
    # 3. Calculate zonal statistics using function, add to gdf
    print("\nStep 3: Calculating canopy statistics by tract")
    tracts_with_stats = calculate_tract_canopy_stats(city_tracts, canopy_dataset, available_years)
    
    # 4. Calculate change metrics using function, add to gdf
    print("\nStep 4: Calculating mean canopy change")
    tracts_with_analysis = calculate_mean_canopy_change(tracts_with_stats, available_years[0], available_years[-1])
        
    # 5. Print summary statistics
    print_summary_stats(tracts_with_analysis, city_name, available_years[0], available_years[-1])
    
    # 6. Export all outputs (maps, files, etc) (optional)
    exports = None
    if export:
        exports = export_all_outputs(
            city_boundary=city_boundary,
            tracts_gdf=tracts_with_analysis,
            canopy_dataset=canopy_dataset,
            city_name=city_name,
            start_year=available_years[0],
            end_year=available_years[-1],
            years=available_years,
            output_dir=f"{city_name}_outputs"
        )

    return city_boundary, tracts_with_analysis, canopy_dataset, exports


def print_summary_stats(analysis_gdf, city_name, start_year, end_year):
    """Print summary statistics to console"""
    print("\n" + "="*60)
    print(f"{city_name.upper()} CANOPY ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"\nTotal census tracts analyzed: {len(analysis_gdf)}")
    print(f"\nCanopy Coverage:")
    print(f"  {start_year}: {analysis_gdf[f'canopy_mean_{start_year}'].mean():.2f}% (mean)")
    print(f"  {end_year}: {analysis_gdf[f'canopy_mean_{end_year}'].mean():.2f}% (mean)")
    print(f"  Change: {analysis_gdf['canopy_change_pct'].mean():.2f} percentage points")
    
    print(f"\nChange Categories:")
    for category, count in analysis_gdf['change_category'].value_counts().items():
        pct = (count / len(analysis_gdf)) * 100
        print(f"  {category}: {count} tracts ({pct:.1f}%)")
    
    print(f"\nTotal Canopy Acres:")
    print(f"  {start_year}: {analysis_gdf[f'canopy_acres_{start_year}'].sum():.0f} acres")
    print(f"  {end_year}: {analysis_gdf[f'canopy_acres_{end_year}'].sum():.0f} acres")
    print(f"  Change: {analysis_gdf['canopy_acres_change'].sum():.0f} acres")
    print("="*60 + "\n")



### MAIN FUNCTION WITH COMMAND LINE IMPLEMENTED ###
def main():
    """Main function that has command line argument parsing"""
    parser = argparse.ArgumentParser(
        description='Analyze tree canopy change for any US city using NLCD data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --city "Portland" --state "OR" --start-year 2011 --end-year 2021
  python main.py --city "Seattle" --state "WA" --start-year 2016 --end-year 2021 --output-dir seattle_results
  python main.py --city "Austin" --state "TX" --start-year 2011 --end-year 2019 --no-export
        """
    )
    
    # Required arguments
    parser.add_argument('--city', '--city-name', required=True, help='City name (e.g., "Portland", "New York")')
    parser.add_argument('--state', '--state-abbr', required=True, help='State abbreviation (e.g., "OR", "NY")')
    parser.add_argument('--start-year', type=int, required=True, help='Start year for analysis (NLCD data available 2011-2021)')
    parser.add_argument('--end-year', type=int, required=True, help='End year for analysis (NLCD data available 2011-2021)')
    
    # Optional arguments    
    parser.add_argument('--no-export', action='store_true', help='Skip exporting visualizations and data files')
    parser.add_argument('--plot', action='store_true', help='Display supplementary matplotlib plot of final year canopy coverage')
    args = parser.parse_args()
    
    # Validate years
    if args.start_year < 2011 or args.end_year > 2021:
        print("WARNING: NLCD data only available for years 2011-2021")
    
    if args.start_year >= args.end_year:
        parser.error("--start-year must be less than --end-year")
    
    # RUN analysis
    try:
        city_boundary, analysis_gdf, canopy_dataset, exports = analyze_city_canopy(
            city_name=args.city.title(),
            state_abbr=args.state.upper(),
            start_year=args.start_year,
            end_year=args.end_year,
            export=not args.no_export
        )
        
        # Optional plot
        if args.plot:
            # Use the actual analyzed years, not the requested years
            # list of all years needed
            years = list(range(args.start_year, args.end_year + 1))
            # Filter to only years with NLCD data (2011-2021)
            available_years = [y for y in years if y in np.arange(2011, 2022)]
            actual_end_year = available_years[-1]

            print(f"\nDisplaying plot of {actual_end_year} canopy cover data...")

            fig, ax = plt.subplots(figsize=(10, 8))
            canopy_dataset[f'canopy_{actual_end_year}'].plot(
                ax=ax, cmap='Greens', vmin=0, vmax=100
            )
            city_boundary.boundary.plot(ax=ax, color='red', linewidth=2)
            plt.title(f"{args.city} Tree Canopy Cover {actual_end_year} (%)")
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
            plt.tight_layout()
            plt.show()
        
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"\n Error during analysis: {e}")
        raise




if __name__ == "__main__":
    main()