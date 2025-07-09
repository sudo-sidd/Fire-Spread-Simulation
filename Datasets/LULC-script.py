import ee
ee.Initialize()

# Example: Uttarakhand LULC for 2024
region = ee.Geometry.Rectangle([78.0, 29.0, 80.0, 31.0])
lulc = ee.ImageCollection('ESA/WorldCover/v100').first().clip(region)

task = ee.batch.Export.image.toDrive(
    image=lulc,
    description='Uttarakhand_LULC',
    scale=30,
    region=region.bounds().getInfo()['coordinates'],
    fileFormat='GeoTIFF'
)
task.start()
