import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings('ignore')


class TariffForecaster:
    def __init__(self, start_year=2002, end_year=2025, db_config=None):
        self.start_year = start_year
        self.end_year = end_year
        self.data = None
        self.engine = None
        self.db_config = db_config
        self._connect_to_db()

    def _connect_to_db(self):
        """Establish database connection"""
        try:
            connection_string = f"postgresql://{self.db_config["DB_USERNAME"]}:{self.db_config["DB_PASSWORD"]}@{self.db_config["DB_URL"]}"
            self.engine = create_engine(connection_string)
            print(f"Connected to database")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise

    def load_data(self):
        """Load all tariff tables from start_year to end_year"""
        dfs = []

        for year in range(self.start_year, self.end_year + 1):
            table_name = f"tariff_hts{year}"
            try:
                query = f"SELECT * FROM tariffs.{table_name}"
                df = pd.read_sql(query, self.engine)
                df['year'] = year
                dfs.append(df)
                print(f"Loaded {table_name}: {len(df)} rows")
            except Exception as e:
                print(f"Warning: Could not load {table_name}: {e}")

        if not dfs:
            raise ValueError("No data tables found!")

        self.data = pd.concat(dfs, ignore_index=True)
        print(f"\nTotal rows loaded: {len(self.data)}")
        return self.data

    def preprocess_data(self):
        """Clean and prepare data for forecasting"""
        # Convert dates
        self.data['effectivedate'] = pd.to_datetime(self.data['effectivedate'])
        self.data['expirydate'] = pd.to_datetime(self.data['expirydate'])

        # Handle 'Free' values in category column
        self.data['advalorem'] = pd.to_numeric(
            self.data['advalorem'], errors='coerce')
        self.data['specificperunit'] = pd.to_numeric(
            self.data['specificperunit'], errors='coerce')

        # Fill NaN with 0 for tariff values
        self.data['advalorem'].fillna(0, inplace=True)
        self.data['specificperunit'].fillna(0, inplace=True)

        # Extract base tariff code (remove year suffix)
        # Pattern: tariffid ends with country code (2 chars) + year (4 digits)
        self.data['base_tariffid'] = self.data['tariffid'].astype(str).str[:-6]

        print(f"\nData preprocessed. Shape: {self.data.shape}")
        print(
            f"Unique base tariff IDs: {self.data['base_tariffid'].nunique()}")
        print(f"Years covered: {sorted(self.data['year'].unique())}")
        return self.data

    def create_time_series(self, group_by_cols=['base_tariffid', 'partnercountry']):
        """Create time series for each tariff product"""
        # Group by base tariff ID and partner country to track changes over time
        time_series = self.data.groupby(group_by_cols + ['year']).agg({
            'advalorem': 'mean',
            'specificperunit': 'mean',
            'descriptionwcountry': 'first',
            'unitname': 'first',
            'tariffid': 'first'  # Keep one example of the full tariffid
        }).reset_index()

        return time_series

    def forecast_tariff(self, base_tariff_id, partner_country, forecast_years=3, method='linear'):
        """
        Forecast tariff values for a specific product

        Parameters:
        - base_tariff_id: The base tariff ID to forecast (without year)
        - partner_country: The partner country code
        - forecast_years: Number of years to forecast (default: 3)
        - method: 'linear' or 'rf' (Random Forest)
        """
        # Filter data for specific tariff and partner
        mask = (self.data['base_tariffid'] == base_tariff_id) & \
               (self.data['partnercountry'] == partner_country)
        tariff_data = self.data[mask].copy()

        if len(tariff_data) == 0:
            return None

        # Sort by year
        tariff_data = tariff_data.sort_values('year')

        # Prepare features (X) and targets (y)
        X = tariff_data[['year']].values
        y_advalorem = tariff_data['advalorem'].values
        y_specific = tariff_data['specificperunit'].values

        # Forecast years
        future_years = np.array([[self.end_year + i]
                                for i in range(1, forecast_years + 1)])

        results = {
            'base_tariffid': base_tariff_id,
            'partnercountry': partner_country,
            'description': tariff_data['descriptionwcountry'].iloc[0],
            'unitname': tariff_data['unitname'].iloc[0],
            'historical_years': X.flatten().tolist(),
            'historical_advalorem': y_advalorem.tolist(),
            'historical_specific': y_specific.tolist(),
            'forecast_years': future_years.flatten().tolist(),
            'num_historical_points': len(X)
        }

        # Forecast advalorem
        if method == 'linear':
            model_ad = LinearRegression()
            model_sp = LinearRegression()
        else:
            model_ad = RandomForestRegressor(n_estimators=100, random_state=42)
            model_sp = RandomForestRegressor(n_estimators=100, random_state=42)

        model_ad.fit(X, y_advalorem)
        model_sp.fit(X, y_specific)

        results['forecast_advalorem'] = model_ad.predict(future_years).tolist()
        results['forecast_specific'] = model_sp.predict(future_years).tolist()

        return results

    def forecast_all_tariffs(self, forecast_years=3, method='linear', min_historical_points=3):
        """
        Forecast all tariffs that have sufficient historical data

        Parameters:
        - forecast_years: Number of years to forecast
        - method: 'linear' or 'rf'
        - min_historical_points: Minimum number of historical data points required
        """
        # Get unique base tariff-partner combinations
        combinations = self.data.groupby(
            ['base_tariffid', 'partnercountry']).size().reset_index(name='count')
        combinations = combinations[combinations['count']
                                    >= min_historical_points]

        print(
            f"\nForecasting {len(combinations)} tariff-partner combinations...")
        print(
            f"(Filtered from {self.data.groupby(['base_tariffid', 'partnercountry']).ngroups} total combinations)")

        forecasts = []
        for idx, row in combinations.iterrows():
            if idx % 1000 == 0:
                print(f"  Processing {idx}/{len(combinations)}...")

            result = self.forecast_tariff(
                row['base_tariffid'],
                row['partnercountry'],
                forecast_years=forecast_years,
                method=method
            )
            if result:
                forecasts.append(result)

        print(f"  Completed: {len(forecasts)} forecasts generated")
        return forecasts

    def save_forecasts_to_db(self, forecasts, table_name, if_exists='replace'):
        """
        Save forecasts to PostgreSQL database

        Parameters:
        - forecasts: List of forecast dictionaries
        - table_name: Name of the table to save to (can include schema: 'schema.table')
        - if_exists: 'replace', 'append', or 'fail'
        """
        records = []
        for forecast in forecasts:
            # Combine base_tariffid and partnercountry
            combined_tariffid = f"{forecast['base_tariffid']}{forecast['partnercountry']}"
            
            for i, year in enumerate(forecast['forecast_years']):
                records.append({
                    'tariffid': combined_tariffid,
                    'description': forecast['description'],
                    'unitname': forecast['unitname'],
                    'forecast_year': year,
                    'forecast_advalorem': forecast['forecast_advalorem'][i],
                    'forecast_specificperunit': forecast['forecast_specific'][i],
                    'num_historical_points': forecast['num_historical_points'],
                    'forecast_method': 'linear',
                    'created_at': pd.Timestamp.now()
                })

        df_forecast = pd.DataFrame(records)

        # Parse schema and table name
        if '.' in table_name:
            schema, table = table_name.split('.', 1)
        else:
            schema = None
            table = table_name

        # Save to database
        try:
            df_forecast.to_sql(
                table,
                self.engine,
                schema=schema,
                if_exists=if_exists,
                index=False,
                method='multi',
                chunksize=1000
            )
            print(
                f"\n✓ Forecasts saved to table '{table_name}' ({len(df_forecast)} rows)")
            print(f"  Mode: {if_exists}")

            # Show table info with proper schema handling
            with self.engine.connect() as conn:
                if schema:
                    query = text(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
                else:
                    query = text(f'SELECT COUNT(*) FROM "{table}"')
                result = conn.execute(query)
                count = result.scalar()
                print(f"  Total rows in table: {count}")

        except Exception as e:
            print(f"Error saving to database: {e}")
            raise

        return df_forecast

    def save_forecasts_to_csv(self, forecasts, output_file='tariff_forecasts.csv'):
        """Save forecasts to CSV file (backup option)"""
        records = []
        for forecast in forecasts:
            for i, year in enumerate(forecast['forecast_years']):
                records.append({
                    'base_tariffid': forecast['base_tariffid'],
                    'partnercountry': forecast['partnercountry'],
                    'description': forecast['description'],
                    'unitname': forecast['unitname'],
                    'forecast_year': year,
                    'forecast_advalorem': forecast['forecast_advalorem'][i],
                    'forecast_specificperunit': forecast['forecast_specific'][i],
                    'num_historical_points': forecast['num_historical_points']
                })

        df_forecast = pd.DataFrame(records)
        df_forecast.to_csv(output_file, index=False)
        print(f"\nForecasts also saved to {output_file}")
        return df_forecast


async def forecast_tariffs(db_config):
    try:
        forecaster = TariffForecaster(
            start_year=2002,
            end_year=2025,
            db_config=db_config
        )

        print("Loading data from DB")
        forecaster.load_data()
        forecaster.preprocess_data()
        print("Generating forecasts...")
        forecasts = forecaster.forecast_all_tariffs(
            forecast_years=3,
            method='linear',  # Use 'rf' for Random Forest
            min_historical_points=3
        )

        forecaster.save_forecasts_to_db(
            forecasts,
            table_name='tariffs.tariff_forecasts',
            if_exists='replace'
        )

        # Optionally save to CSV as backup
        # forecaster.save_forecasts_to_csv(forecasts, 'tariff_forecasts_backup.csv')

        print(f"\nForecast complete! Generated {len(forecasts)} forecasts.")

        if forecaster.engine:
            forecaster.engine.dispose()
            print("\nDatabase connection closed")
        return {
            "success": True,
            "message": f"Generated {len(forecasts)} forecasts."
        }
    except Exception as e:
        print(e)
        return {
            "success": False,
            "message": str(e)
        }
