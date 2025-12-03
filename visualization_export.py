"""
Functions to create & export deliverables (HTML map visualizations, dataframes) of canopy cover % by census tract.
"""
import os
import folium
import rasterio
from rasterio.plot import reshape_as_image


def create_yearly_canopy_maps(city_boundary, tracts_gdf, canopy_dataset, years, output_dir="outputs"):
    """
    Create interactive HTML maps showing canopy coverage layer by year
    
    Parameters:
        city_boundary: gdf of city boundary
        tracts_gdf: gdf with tract stats
        canopy_dataset: xarray.Dataset with canopy data
        years: list of years to map
        output_dir: directory to save HTML files
    
    Returns: list of file paths to created maps
    """
    os.makedirs(output_dir, exist_ok=True)
    created_maps = []
    
    # Get center point for map (Just use bounds):
    bounds = city_boundary.total_bounds  # [minx, miny, maxx, maxy]
    center_lon = (bounds[0] + bounds[2]) / 2
    center_lat = (bounds[1] + bounds[3]) / 2

    # Ensure all geometries are valid Polygons/MultiPolygons
    tracts_clean = tracts_gdf[tracts_gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()
    
    for year in years:
        print(f"Creating map for {year}...")
        
        # Create base map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles='CartoDB positron')
        
        # Add city boundary layer
        folium.GeoJson(
            city_boundary,
            name='City Boundary',
            style_function=lambda x: {
                'fillColor': 'none',
                'color': 'red',
                'weight': 3,
                'fillOpacity': 0
            }
        ).add_to(m)
        
        # Add census tracts with canopy stats
        folium.Choropleth(
            geo_data=tracts_clean,
            data=tracts_clean,
            columns=['GEOID', f'canopy_mean_{year}'],
            key_on='feature.properties.GEOID',
            fill_color='YlGn',  # Yellow-Green colormap
            fill_opacity=0.7,
            line_opacity=0.5,
            legend_name=f'Tree Canopy Cover {year} (%)',
            nan_fill_color='lightgray'
        ).add_to(m)
        
        # Add tract labels on hover
        style_function = lambda x: {'fillColor': 'transparent', 'color': 'transparent', 'weight': 0}
        highlight_function = lambda x: {'weight': 3, 'color': 'black', 'fillOpacity': 0}
        
        # tooltip
        tooltip = folium.GeoJsonTooltip(
            fields=['NAMELSAD', f'canopy_mean_{year}', f'canopy_pixels_{year}'],
            aliases=['Tract:', f'Canopy {year}:', 'Pixels:'],
            localize=True,
            style=("background-color: white; color: black; font-family: courier new; font-size: 12px; padding: 10px;")
        )
        
        folium.GeoJson(
            tracts_clean,
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=tooltip,
            name='Tract Details'
        ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Save map
        filename = f"{output_dir}/canopy_map_{year}.html"
        m.save(filename)
        created_maps.append(filename)
        print(f"  Saved: {filename}")
    
    return created_maps



def create_change_map(city_boundary, tracts_gdf, start_year, end_year, output_dir="outputs"):
    """
    Create interactive HTML map showing categories of avg canopy CHANGE by tract
    
    Parameters:
        city_boundary: gdf of city boundary
        tracts_gdf: gdf with change metrics
        start_year: int
        end_year: int
        output_dir: directory to save HTML files
    
    Returns: filepath to created map
    """
    os.makedirs(output_dir, exist_ok=True)

    # Get center point for map (Just use bounds):
    bounds = city_boundary.total_bounds  # [minx, miny, maxx, maxy]
    center_lon = (bounds[0] + bounds[2]) / 2
    center_lat = (bounds[1] + bounds[3]) / 2

    # Ensure all geometries are valid Polygons/MultiPolygons
    tracts_clean = tracts_gdf[tracts_gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()
    
    # Create base map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles='CartoDB positron')
    
    # Define color scheme for change categories
    category_colors = {
        'Major Loss': '#d73027',      # Dark red
        'Moderate Loss': '#fc8d59',   # Orange
        'Stable': '#ffffbf',           # Yellow
        'Moderate Gain': '#91cf60',   # Light green
        'Major Gain': '#1a9850',      # Dark green
        'No Data': '#d9d9d9'          # Gray
    }
    
    # Create a color function
    def style_function(feature):
        category = feature['properties']['change_category']
        return {
            'fillColor': category_colors.get(category, '#d9d9d9'),
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.7
        }
    
    def highlight_function(feature):
        return {'weight': 3, 'color': 'black', 'fillOpacity': 0.8}
    
    # Create detailed tooltip
    tooltip = folium.GeoJsonTooltip(
        fields=[
            'NAMELSAD', 
            f'canopy_mean_{start_year}', 
            f'canopy_mean_{end_year}',
            'canopy_change_pct',
            'change_category',
            'canopy_acres_change'
        ],
        aliases=[
            'Tract:', 
            f'Canopy {start_year}:', 
            f'Canopy {end_year}:',
            'Change (pct pts):',
            'Category:',
            'Acres Change:'
        ],
        localize=True,
        style=("background-color: white; color: black; font-family: arial; "
               "font-size: 12px; padding: 10px;")
    )
    
    # Add tracts with styling
    folium.GeoJson(
        tracts_clean,
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=tooltip,
        name='Canopy Change'
    ).add_to(m)
    
    # Add city boundary
    folium.GeoJson(
        city_boundary,
        name='City Boundary',
        style_function=lambda x: {
            'fillColor': 'none',
            'color': 'red',
            'weight': 3,
            'fillOpacity': 0
        }
    ).add_to(m)
    
    # Add custom legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p style="margin-bottom:10px;"><strong>Canopy Change</strong><br>
    {start_year} - {end_year}</p>
    '''
    
    for category, color in category_colors.items():
        count = len(tracts_clean[tracts_clean['change_category'] == category])
        if count > 0:
            legend_html += f'''
            <p style="margin:5px 0;">
                <span style="background-color:{color}; 
                            width:20px; height:20px; 
                            display:inline-block; margin-right:5px;"></span>
                {category} ({count})
            </p>
            '''
    
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save map
    filename = f"{output_dir}/canopy_change_map_{start_year}_{end_year}.html"
    m.save(filename)
    print(f"Created change map: {filename}")
    
    return filename



def export_shapefiles(city_boundary, tracts_gdf, city_name, start_year, end_year, output_dir="outputs"):
    """
    Export shapefiles to use in ArcGIS Pro
    
    Parameters:
        city_boundary: GeoDataFrame of city boundary
        tracts_gdf: GeoDataFrame with all analysis results
        city_name: str
        start_year: int
        end_year: int
        output_dir: directory to save shapefiles
    
    Returns: dict of exported file paths (boundary shp, data shp)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    exported_files = {}
    
    # Clean city name for filenames
    clean_name = city_name.replace(' ', '_').lower()
    
    # 1. Export city boundary
    boundary_file = f"{output_dir}/{clean_name}_boundary.shp"
    city_boundary.to_file(boundary_file)
    exported_files['boundary'] = boundary_file
    print(f"Exported: {boundary_file}")
    
    # 2. Export complete analysis results (all columns)
    # Shapefile field names limited to 10 chars, so simplify col names:
    shp_gdf = tracts_gdf[['GEOID', 'NAMELSAD', 'geometry']].copy()
    # Add canopy variables (with shortened names)
    shp_gdf['cnpy_2011'] = tracts_gdf[f'canopy_mean_{start_year}']
    shp_gdf['cnpy_2021'] = tracts_gdf[f'canopy_mean_{end_year}']
    shp_gdf['chng_pct'] = tracts_gdf['canopy_change_pct']
    shp_gdf['category'] = tracts_gdf['change_category']
    shp_gdf['acres_chg'] = tracts_gdf['canopy_acres_change']
    
    shp_filename = f"{output_dir}/{clean_name}_{start_year}_{end_year}.shp"
    shp_gdf.to_file(shp_filename)
    exported_files['shp_file'] = shp_filename
    print(f"Exported: {shp_filename}")
    
    return exported_files



def export_geodataframe(tracts_gdf, city_name, start_year, end_year, output_dir="outputs"):
    """
    Export GeoDataFrame in multiple formats
    
    Parameters:
        tracts_gdf: GeoDataFrame with analysis results
        city_name: str
        start_year: int
        end_year: int
        output_dir: directory to save files
    
    Returns: dict of exported file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    
    clean_name = city_name.replace(' ', '_').lower()
    exported_files = {}
    
    # 1. GeoPackage (preserves all data + geometry, can be opened in ArcGIS Pro, QGIS, Python, etc.)
    gpkg_file = f"{output_dir}/{clean_name}_complete_{start_year}_{end_year}.gpkg"
    tracts_gdf.to_file(gpkg_file, driver='GPKG')
    exported_files['geopackage'] = gpkg_file
    print(f"Exported GeoPackage: {gpkg_file}")
    
    # 2. GeoJSON (good for web, easy to read)
    geojson_file = f"{output_dir}/{clean_name}_complete_{start_year}_{end_year}.geojson"
    tracts_gdf.to_file(geojson_file, driver='GeoJSON')
    exported_files['geojson'] = geojson_file
    print(f"Exported GeoJSON: {geojson_file}")
    
    # 3. CSV with WKT geometry (can be read back into Python/pandas)
    csv_file = f"{output_dir}/{clean_name}_complete_{start_year}_{end_year}.csv"
    df_to_export = tracts_gdf.copy()
    df_to_export['geometry_wkt'] = df_to_export.geometry.to_wkt()
    df_to_export.drop(columns=['geometry']).to_csv(csv_file, index=False)
    exported_files['csv'] = csv_file
    print(f"Exported CSV: {csv_file}")
    
    return exported_files



def export_all_outputs(city_boundary, tracts_gdf, canopy_dataset, city_name, start_year, end_year, years, output_dir="outputs"):
    """
    Export all maps, shapefiles, and data files
    Returns: dict with all exported file paths
    """
    print("EXPORTING DELIVERABLES")
    
    all_exports = {}
    
    # 1. Create yearly maps
    print("\n1. Creating yearly canopy maps...")
    yearly_maps = create_yearly_canopy_maps(city_boundary, tracts_gdf, canopy_dataset, years, output_dir)
    all_exports['yearly_maps'] = yearly_maps
    
    # 2. Create change map
    print("\n2. Creating change choropleth map...")
    change_map = create_change_map(city_boundary, tracts_gdf, start_year, end_year, output_dir)
    all_exports['change_map'] = change_map
    
    # 3. Export shapefiles
    print("\n3. Exporting shapefiles...")
    shapefiles = export_shapefiles(city_boundary, tracts_gdf, city_name, start_year, end_year, output_dir)
    all_exports['shapefiles'] = shapefiles
    
    # 4. Export GeoDataFrames in multiple formats
    print("\n4. Exporting data files...")
    data_files = export_geodataframe(tracts_gdf, city_name, start_year, end_year, output_dir)
    all_exports['data_files'] = data_files
    
    print("EXPORT COMPLETE!")
    print(f"\nAll files saved to: {output_dir}/")
    print(f"Total files created: {len(yearly_maps) + 1 + len(shapefiles) + len(data_files)}")
    
    return all_exports