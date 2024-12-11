import numpy as np
import netCDF4
import os
import datetime

class NcWritter:
    def __init__(self, lon:float,lat:float,time_list, rain, file_path ='./', file_name='test.nc') -> None:
        '''
        The precipitation data the size :  (time, lat, lon)
        '''
        self.lon  = lon 
        self.lat  = lat
        self.init_time = time_list[0].strftime('%Y-%m-%d-T%H:%M:%S')
        self.fcst_time = [(time - time_list[0]).total_seconds()/3600 for time in time_list]
        self.rain = rain
        self.file_path = file_path
        self.file_name = file_name

    def __call__(self) :
        self.create_nc_file()
        self.set_global_attributes()
        self.create_dimensions()
        self.write_variables()

    def set_global_attributes(self):
        self.nc.title = 'ECMWF Hourly Precipitation from Windy' 
        self.nc.summary = 'ECMWF Hourly Precipitation from Windy'
        self.nc.institution = 'Center for Weather Climate and Disaster Reaearch, National Taiwan University.'
        self.nc.history = f'{datetime.datetime.now().strftime("%Y-%m-%d")} creation of {self.file_name} netcdf file.'
    
    def create_nc_file(self,):
        # Create NetCDF File
        output_nc = os.path.join(self.file_path, self.file_name)
        self.nc = netCDF4.Dataset(output_nc, 'w')

    def create_dimensions(self): 
        self.nc.createDimension('latitude', size=len(self.lat))
        self.nc.createDimension('longitude', size=len(self.lon))
        self.nc.createDimension('time', size=None)

        str_raw = self.init_time
        str_len = len(str_raw) 
        self.str_out = netCDF4.stringtochar(np.array(str_raw, f'S{str_len}'))
        self.nc.createDimension('nchar', str_len)
        
    def write_variables(self): 
        lat_var = self.nc.createVariable('latitude', np.float64, ('latitude'))
        lat_var.units = 'degrees_north'
        lat_var.standard_name = 'latitude'
        lat_var.axis = 'Y'
        lat_var[:] = self.lat

        lon_var = self.nc.createVariable('longitude', np.float64, ('longitude'))
        lon_var.units = 'degrees_east'
        lon_var.standard_name = 'longitude'
        lon_var.axis = 'X'
        lon_var[:] = self.lon

        time_var = self.nc.createVariable('time', np.int32, ('time'))
        time_var.standard_name = 'model_forecast_time'
        time_var.calendar = 'gregorian'
        time_var.time_step = 'Hourly'
        time_var.units = f'hours since {self.init_time}'  # initial time formaat 1970-01-01 00:00:00
        time_var.axis = 'T'
        time_var[:] = self.fcst_time

        init_time_var = self.nc.createVariable('initial_time', 'S1', ('nchar'))
        init_time_var.standard_name = 'model_initial_time'
        init_time_var[:] = self.str_out

        rain_var = self.nc.createVariable('precipitation', 
                                           np.float64, 
                                           ('time', 'latitude', 'longitude'),
                                           fill_value=-9999.)
        rain_var.units = 'mm/hr'
        rain_var.long_name = 'hourly precpitation '
        rain_var.short_name = 'precipitation'
        rain_var[:,:,:] = self.rain

        self.nc.close()


if __name__=="__main__":
    # set the input data
    test_lat = np.linspace(-90,90,181)
    test_lon = np.linspace(0,360,361)
    init_time = datetime.datetime(2022,1,13,0,0,0)
    test_time = [init_time+datetime.timedelta(hours = t) for t in range(90)] 
    test = np.ones((len(test_time),len(test_lat),len(test_lon)))

    # use 
    input_to_nc ={
            'lon' : test_lon , # float 
            'lat' : test_lat , # float 
            'time_list' : test_time , # [str] str: yyyy-mm-dd HH:MM:SS
            'rain' : test , # float  
            'file_path' : './' , # float  
            'file_name' : 'test.nc' , # float  
            }
    data = NcWritter(**input_to_nc)
    data()
