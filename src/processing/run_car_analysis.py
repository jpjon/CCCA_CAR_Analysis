#!/usr/bin/env python3
import time
import argparse
from jinja2 import Template
from sqlalchemy import text

from db_loader import PostGISLoader

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run CAR analysis on loaded data')
    parser.add_argument(
        '--years',
        type=str,
        required=True,
        help='Comma-separated list of years to analyze (e.g., 2023,2024,2025)'
    )
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()
    
    # Parse years from comma-separated string
    years = [int(year.strip()) for year in args.years.split(',')]
    
    # Initialize loader
    loader = PostGISLoader()
        
    ##############################################
    #  Subdivide Prodes Geometry for later use   #
    ##############################################
    start_time = time.time()
    
    with open('db/sql/01_subdivide_prodes.sql', 'r') as f:
        sql_query = f.read()
        
        loader.execute_sql(sql_query)
    
    end_time = time.time()
    
    print(f"Created complete Prodes subdivided geometry table for use in analysis in {end_time - start_time:.2f} seconds")
        
    ##############################################
    #         Run SQL Analysis for All Pairs    #
    ##############################################

    # Read the SQL template for car analysis
    with open('db/sql/02_car_analysis.sql.j2', 'r') as f:
        sql_template = Template(f.read())
        
    # Create year pairs: (2020,2021), (2021,2022), ..., (2024,2025)
    year_pairs = [(years[i], years[i+1]) for i in range(len(years)-1)]

    for earlier_year, later_year in year_pairs:
        print(f"\n{'='*60}")
        print(f"ANALYZING: {earlier_year} → {later_year}")
        print(f"{'='*60}")
        
        # Render SQL template
        sql_query = sql_template.render(
            earlier_year=earlier_year,
            later_year=later_year
        )
        
        # Execute SQL analysis
        start_time = time.time()
        try:
            # Execute the SQL script
            loader.execute_sql(sql_query)
            
            # Get summary statistics for this year pair
            summary_query = f"""
            SELECT 
                COUNT(*) as total_parcels_no_longer_intersecting,
                AVG(geodesic_distance) as avg_distance_moved_meters,
                MAX(geodesic_distance) as max_distance_moved_meters,
                MIN(geodesic_distance) as min_distance_moved_meters
            FROM car_changed_to_exclude_prodes
            WHERE year_earlier = {earlier_year} AND year_later = {later_year};
            """
            
            with loader.engine.connect() as conn:
                results = conn.execute(text(summary_query)).fetchall()
            
            end_time = time.time()
            
            if results[0][0] > 0:  # If there are results
                print(f"Analysis completed in {end_time - start_time:.2f} seconds")
                print(f"Results:")
                print(f"  - Parcels that changed geometry and no longer intersect PRODES: {results[0][0]:,}")
                print(f"  - Average distance moved: {results[0][1]:.2f} meters")
                print(f"  - Maximum distance moved: {results[0][2]:.2f} meters")
                print(f"  - Minimum distance moved: {results[0][3]:.2f} meters")
            else:
                print(f"Analysis completed in {end_time - start_time:.2f} seconds")
                print("No parcels found that changed geometry and no longer intersect PRODES")
            
        except Exception as e:
            print(f"Error processing {earlier_year}-{later_year}: {str(e)}")
            continue

    print(f"\n{'='*60}")
    print("ALL ANALYSES COMPLETED!")
    print(f"{'='*60}")

    # Create a summary table across all years
    print("\nCreating summary table across all year pairs...")

    summary_sql = """
    DROP TABLE IF EXISTS car_analysis_summary;
    CREATE TABLE car_analysis_summary AS
    SELECT 
        year_earlier,
        year_later,
        CONCAT(year_earlier, '-', year_later) as year_pair,
        COUNT(*) as parcel_count,
        AVG(geodesic_distance) as avg_distance_meters,
        MAX(geodesic_distance) as max_distance_meters,
        MIN(geodesic_distance) as min_distance_meters,
        STDDEV(geodesic_distance) as stddev_distance_meters,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY geodesic_distance) as median_distance_meters
    FROM car_changed_to_exclude_prodes
    GROUP BY year_earlier, year_later
    ORDER BY year_earlier;
    """

    try:
        # Use fresh connection for summary table creation
        with loader.engine.connect() as conn:
            conn.execute(text(summary_sql))
            conn.commit()
        
        # Show the summary results
        summary_results_query = """
        WITH year_totals AS (
            SELECT 
                year,
                COUNT(DISTINCT cod_imovel) as total_cadastres
            FROM car_data
            GROUP BY year
        )
        SELECT 
            s.year_pair,
            s.parcel_count,
            t.total_cadastres,
            ROUND((s.parcel_count::numeric / t.total_cadastres * 100), 2) as percentage,
            ROUND(s.avg_distance_meters::numeric, 2) as avg_distance_m,
            ROUND(s.median_distance_meters::numeric, 2) as median_distance_m,
            ROUND(s.max_distance_meters::numeric, 2) as max_distance_m
        FROM car_analysis_summary s
        JOIN year_totals t ON s.year_later = t.year
        ORDER BY s.year_earlier;
        """
        
        with loader.engine.connect() as conn:
            summary_results = conn.execute(text(summary_results_query)).fetchall()
        
        print("Summary table created successfully!")
        print("\nSUMMARY ACROSS ALL YEAR PAIRS:")
        print("-" * 110)
        print(f"{'Year Pair':<12} {'Moved':<10} {'Total':<12} {'%':<8} {'Avg Dist (m)':<15} {'Median Dist (m)':<15} {'Max Dist (m)':<12}")
        print("-" * 110)
        for row in summary_results:
            print(f"{row[0]:<12} {row[1]:<10,} {row[2]:<12,} {row[3]:<8.2f} {row[4]:<15} {row[5]:<15} {row[6]:<12}")
        
        # Overall summary
        overall_query = """
        WITH total_unique_cadastres AS (
            SELECT COUNT(DISTINCT cod_imovel) as total_unique
            FROM car_data
        ),
        moved_unique_cadastres AS (
            SELECT COUNT(DISTINCT cod_imovel) as moved_unique
            FROM car_changed_to_exclude_prodes
        )
        SELECT 
            COUNT(*) as total_movements,
            moved.moved_unique as unique_cadastres_moved,
            total.total_unique as total_unique_cadastres,
            ROUND((moved.moved_unique::numeric / total.total_unique * 100), 2) as percentage_moved,
            ROUND(AVG(geodesic_distance)::numeric, 2) as overall_avg_distance,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY geodesic_distance)::numeric, 2) as overall_median_distance
        FROM car_changed_to_exclude_prodes
        CROSS JOIN total_unique_cadastres total
        CROSS JOIN moved_unique_cadastres moved
        GROUP BY moved.moved_unique, total.total_unique;
        """
        
        # Use fresh connection for overall results
        with loader.engine.connect() as conn:
            overall_results = conn.execute(text(overall_query)).fetchone()
        
        print("\n" + "=" * 110)
        print(f"OVERALL STATISTICS:")
        print(f"Total movement records across all years: {overall_results[0]:,}")
        print(f"Unique cadastres that moved: {overall_results[1]:,} out of {overall_results[2]:,} total ({overall_results[3]:.2f}%)")
        print(f"Overall average distance moved: {overall_results[4]} meters")
        print(f"Overall median distance moved: {overall_results[5]} meters")
        
    except Exception as e:
        print(f"Error creating summary table: {str(e)}")

    # Read the SQL template for car analysis
    with open('db/sql/03_create_relevant_prodes_view.sql', 'r') as f:
        sql_query = f.read()
        loader.execute_sql(sql_query)
        
    print("\nScript completed!")


if __name__ == "__main__":
    main()