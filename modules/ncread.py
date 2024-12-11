import netCDF4
import datetime

fn = './test.nc'
ds = netCDF4.Dataset(fn)

time_var = ds.variables['time']
print(time_var[:])
print(time_var.units)
print(time_var.calendar)
dtime = netCDF4.num2date(time_var[:],units=time_var.units)
print(dtime)
