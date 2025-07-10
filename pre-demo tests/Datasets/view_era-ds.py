import xarray as xr

ds = xr.open_dataset("uttarakhand_era5.nc")
print(ds)


ds['2m_temperature']  # (time, latitude, longitude)
ds['total_precipitation']  # Accumulated per hour

temp_c = ds['2m_temperature'] - 273.15


df = ds.to_dataframe().reset_index()
df.to_csv("uttarakhand_era5.csv", index=False)

