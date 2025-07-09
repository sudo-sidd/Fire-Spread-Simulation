import cdsapi
from datetime import datetime, timedelta

# Global Configuration
AREA_UTTARAKHAND = [31.0, 77.5, 28.5, 81.5]  # [North, West, South, East]
TIME_HOURLY = [f"{h:02d}:00" for h in range(24)]

# Date Calculation
import datetime
today = datetime.datetime(2025, 7, 1).date()

dates = [
    (today - timedelta(days=1)).strftime("%Y-%m-%d"),  # yesterday
    today.strftime("%Y-%m-%d"),                        # today
    (today + timedelta(days=1)).strftime("%Y-%m-%d")   # tomorrow
]

# Group by year, month, day
year = str(today.year)
month = f"{today.month:02d}"
days = [d[-2:] for d in dates]

# API Request
c = cdsapi.Client()
c.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'variable': [
            '2m_temperature', '10m_u_component_of_wind', '10m_v_component_of_wind',
            'surface_pressure', 'total_precipitation', '2m_dewpoint_temperature'
        ],
        'year': year,
        'month': month,
        'day': days,
        'time': TIME_HOURLY,
        'format': 'netcdf',
        'area': AREA_UTTARAKHAND,
    },
    'uttarakhand_era5.nc'
)
