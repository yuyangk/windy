#! /bin/python3
import os, argparse
import pandas as pd
import numpy as np
import time
import json
import shutil
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from PIL import Image
from time import sleep
from datetime import datetime
from datetime import timedelta
from scipy.interpolate import griddata
from modules.ncwrite import NcWritter

class Windy:
    def __init__(self, account, passwd, model, img_path='./screenshot_tmp/') -> None:
        self.account = account 
        self.passwd = passwd
        self.model = model
        self.output_img_path = img_path

        windy_url = f'https://www.windy.com/?{str.lower(self.model)},23.647,121.122,7'
        options = webdriver.ChromeOptions()
        # TODO Find API to specify cetificate files
        options.set_capability("acceptInsecureCerts", True)
        options.add_argument('--proxy-server=mitmproxy:8080')
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')
        options.add_argument('window-size=1920,1080')

        self.driver = webdriver.Chrome(options=options) 
        self.driver.fullscreen_window()
        self.driver.implicitly_wait(10)
        self.driver.get(windy_url)

        return

    def _login(self):
        #self.driver.find_element(By.XPATH, '//*[@id="login-and-premium"]/div[2]').click()
        sleep(1)
        #self.driver.find_element(By.XPATH, '//*[@id="device-desktop"]/body/div[3]/div[1]/div[2]').click()
        self.driver.find_element(By.XPATH, '//*[@id="plugin-rhpane-top"]/div[1]/div[2]').click()
        sleep(1)
        self.driver.find_element(By.XPATH, '//*[@id="email"]').send_keys(self.account)
        sleep(1)
        self.driver.find_element(By.XPATH, '//*[@id="password"]').send_keys(self.passwd)
        sleep(3)
        self.driver.find_element(By.XPATH, '//*[@id="submitLogin"]').click()
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' | [登入作業]完成!')
        sleep(3)
        #self.driver.find_element(By.XPATH, '//*[@id="plugin-rhbottom"]/nav[1]/a[1]').click()
        self.driver.find_element(By.XPATH, '//*[@id="plugin-rhpane-top"]/section/section/a[4]/div[2]').click()

        return

    def _get_init_time(self):
        self.driver.find_element(By.XPATH, '//*[@id="plugin-rhbottom"]/nav[2]/a[5]').click()
        sleep(1)
        self.init_time = self.driver.find_element(By.XPATH, '//*[@id="plugin-info"]/div[2]/section[1]/span').text
        self.init_time = self.init_time[0:10] + ' ' + self.init_time[11:13] + 'Z'
        self.init_time_dt = datetime.strptime(self.init_time, "%Y-%m-%d %HZ")
        print(self.init_time)
        self.driver.refresh()
        
        return

    def _create_time_list(self):
        run = self.init_time[11:13]
        run_list = ['00','06','12','18']
        run_final_hour_list = [240, 236, 228, 228]
        self.final_hour = run_final_hour_list[run_list.index(run)]

        if self.model == 'EC':
            Timelist_1h = (pd.date_range(start = (self.init_time_dt + timedelta(hours=3)).strftime('%Y-%m-%d %H'),
                                        end = (self.init_time_dt + timedelta(hours=86)).strftime('%Y-%m-%d %H'), 
                                        freq='1H')).to_pydatetime().tolist()
                                        
            if run=='00' or run=='12':
                Timelist_3h = (pd.date_range(start = (self.init_time_dt + timedelta(hours=87)).strftime('%Y-%m-%d %H'), 
                                            end = (self.init_time_dt + timedelta(hours=144)).strftime('%Y-%m-%d %H'), 
                                            freq='3H')).to_pydatetime().tolist()
                Timelist_6h = (pd.date_range(start = (self.init_time_dt + timedelta(hours=150)).strftime('%Y-%m-%d %H'), 
                                            end = (self.init_time_dt + timedelta(hours=self.final_hour)).strftime('%Y-%m-%d %H'), 
                                            freq='6H')).to_pydatetime().tolist()
            else:
                Timelist_3h = (pd.date_range(start = (self.init_time_dt + timedelta(hours=87)).strftime('%Y-%m-%d %H'), 
                                            end = (self.init_time_dt + timedelta(hours=138)).strftime('%Y-%m-%d %H'), 
                                            freq='3H')).to_pydatetime().tolist()
                Timelist_6h = (pd.date_range(start = (self.init_time_dt + timedelta(hours=144)).strftime('%Y-%m-%d %H'), 
                                            end = (self.init_time_dt + timedelta(hours=self.final_hour)).strftime('%Y-%m-%d %H'), 
                                            freq='6H')).to_pydatetime().tolist()
            
            Timelist_dt = Timelist_1h + Timelist_3h + Timelist_6h
            self.time_list = [Timelist_dt[t].strftime('%Y-%m-%d-%H') for t in range(len(Timelist_dt))]  #UTC
            self.frcst_timegap = np.concatenate((np.ones(len(Timelist_1h)), 
                                                np.ones(len(Timelist_3h))*3, 
                                                np.ones(len(Timelist_6h))*6))

        else:  #self.model == 'GFS'
            Timelist_1h = (pd.date_range(start = (self.init_time_dt + timedelta(hours=3)).strftime('%Y-%m-%d %H'),
                                        end = (self.init_time_dt + timedelta(hours=86)).strftime('%Y-%m-%d %H'), 
                                        freq='1H')).to_pydatetime().tolist()
            Timelist_3h = (pd.date_range(start = (self.init_time_dt + timedelta(hours=87)).strftime('%Y-%m-%d %H'), 
                                            end = (self.init_time_dt + timedelta(hours=self.final_hour)).strftime('%Y-%m-%d %H'), 
                                            freq='3H')).to_pydatetime().tolist()
            
            Timelist_dt = Timelist_1h + Timelist_3h
            self.time_list = [Timelist_dt[t].strftime('%Y-%m-%d-%H') for t in range(len(Timelist_dt))]  #UTC
            self.frcst_timegap = np.concatenate((np.ones(len(Timelist_1h)), 
                                                np.ones(len(Timelist_3h))*3))

        return self.time_list

    def _remove_advertisement(self):
        try :
            advertisement = WebDriverWait(self.driver, 0.5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="plugin-whats-new"]')))
            self.driver.execute_script("""var element = arguments[0];element.parentNode.removeChild(element);""", advertisement)
            print('Ad is found, remove it ')
        except : 
            pass 

    def _remove_ty_advertisement(self):
        try :
            self.driver.find_element(By.XPATH, '//*[@id="window-us-ht-promo3-desktop"]/div').click()
        except : 
            pass 
    
    def _do_screen_shot(self, time,loc_x, loc_y, img_full_path = './screenshot_tmp'):
        url = f'https://www.windy.com/zh-TW/-降雨、雷暴-rain?{str.lower(self.model)},rain,23.647,121.122,7'
        self.driver.get(url)
        text = self.driver.find_element(By.XPATH, '//*[@id="leaflet-map"]/div[1]/div[4]')
        self.driver.execute_script("""var element = arguments[0];element.parentNode.removeChild(element);""", text)
        mapline = self.driver.find_element(By.XPATH, '//*[@id="leaflet-map"]/div[1]/div[1]/div[1]')
        self.driver.execute_script("""var element = arguments[0];element.parentNode.removeChild(element);""", mapline)
        self._remove_advertisement()
        self._remove_ty_advertisement()

        action = ActionBuilder(self.driver)
        action.pointer_action.move_to_location(loc_x, loc_y)
        action.pointer_action.click()
        action.perform()
        
        sleep(1)
        img_name = os.path.join(img_full_path, f'rain_{self.model}_{time}.png')
        self.driver.save_screenshot(img_name)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | [截圖作業] 已完成：{time}")
        
        return

    def get_1st_day_xloc(self):
        return 60

    def get_10th_day_xloc(self):
        element = self.driver.find_element(By.XPATH, f'//*[@id="calendar"]/div[10]')
        return element.location['x']

    def cal_px_per_hour(self):
        px_per_hour = 6.37
        return px_per_hour

    def get_1st_time_in_progress_bar(self):
        run = self.init_time[11:13]
        if run=='00' or run=='06':
            datetime_1st = datetime.strptime(self.init_time_dt.strftime("%Y%m%d"), "%Y%m%d")
        else: # run=='12' or run=='18'
            datetime_1st = datetime.strptime(self.init_time_dt.strftime("%Y%m%d"), "%Y%m%d") + timedelta(hours=24)
        return datetime_1st

    def get_click_loc(self, click_time, time_1st, px_per_hour):
        delta_hour = (click_time - time_1st).total_seconds()//3600
        delta_px = (delta_hour + 0.5) * px_per_hour 
        click_px = self.get_1st_day_xloc() + delta_px
        return click_px
        
    def _create_dictionary(self):
        d = dict()
        d['init_time_dt'] = self.init_time_dt
        d['time_list'] = self.time_list
        d['frcst_timegap'] = self.frcst_timegap
        d['final_hour'] = self.final_hour
        return d

    def get_img_folder_name(self):
        str_yyyy = self.init_time_dt.strftime('%Y')  
        str_jjj = self.init_time_dt.strftime('%j') 
        str_mmm = self.init_time_dt.strftime('%b') 
        str_dd = self.init_time_dt.strftime('%d') 
        str_hh = self.init_time_dt.strftime('%H') 
        img_full_path = os.path.join(self.output_img_path, 
                                     str_yyyy, 
                                     f'{str_jjj}{str_mmm}{str_dd}',
                                     str_hh,
                                     self.model)
        check_path_exist(img_full_path)
        return img_full_path

    def screen_shot(self):
        self._login()
        self._get_init_time()
        time_list = self._create_time_list()
        img_full_path = self.get_img_folder_name()
        self.driver.implicitly_wait(1)

        time_1st = self.get_1st_time_in_progress_bar()
        px_per_hour = self.cal_px_per_hour()

        for time in time_list:
            loc_x = self.get_click_loc(click_time=datetime.strptime(time, "%Y-%m-%d-%H"), time_1st=time_1st, px_per_hour=px_per_hour)
            loc_y = 1050
            self._do_screen_shot(time, loc_x, loc_y, img_full_path=img_full_path)

        self.driver.quit()
        time_pack = self._create_dictionary()

        return time_pack, img_full_path


class WindyData:
    def __init__(self, time_pack, model, input_img_path = './screenshot_tmp/', output_data_path='./data') :
        self.input_img_path = input_img_path
        self.output_data_path = output_data_path
        self.model = model
        self.init_time_dt = time_pack['init_time_dt']
        self.time_list = time_pack['time_list']
        self.frcst_timegap = time_pack['frcst_timegap']
        self.final_hour = time_pack['final_hour']

        return

    def _create_array(self):
        (lon_R, lon_L, lat_U, lat_D) = (125, 117, 27, 20)
        (pix_R, pix_L, pix_U, pix_D) = (1313, 583, 202, 897)
        grid_gap = 0.05
        pix_lon_gap = (pix_R-pix_L) / ((lon_R-lon_L)/grid_gap)
        pix_lat_gap = (pix_D-pix_U) / ((lat_U-lat_D)/grid_gap)

        self.lon_domain = np.arange(lon_L, lon_R + grid_gap, grid_gap)
        self.lon_grid   = np.round(np.arange(pix_L, pix_R + pix_lon_gap, pix_lon_gap))
        self.lat_domain = np.flipud(np.arange(lat_D, lat_U + grid_gap, grid_gap))
        self.lat_grid   = np.flipud(np.round(np.arange(pix_U, pix_D + pix_lat_gap, pix_lat_gap)))
        self.array_lon  = int((lon_R-lon_L)/grid_gap) + 1
        self.array_lat  = int((lat_U-lat_D)/grid_gap) + 1
        grid_x, grid_y = np.mgrid[0:self.array_lon, 0:self.array_lat]
        self.grid_xy = (grid_x, grid_y)

        self.array_Rain_max = np.ones([self.array_lon, self.array_lat])*220
        self.array_Lowerbound = np.ones([self.array_lon, self.array_lat])*191
        self.rain_data_output = np.ones((self.array_lat, self.array_lon, self.final_hour))*-9999
        
        return self.rain_data_output

    def _image2num(self, time):
        inputimg_path = os.path.join(self.input_img_path, f'rain_{self.model}_{time}.png')
        img_RGB = Image.open(inputimg_path).convert('RGB')
        array_Rain = np.zeros([self.array_lon, self.array_lat])
        for i in range( self.array_lon ):
            for j in range( self.array_lat ):
                array_Rain[i][j] = img_RGB.getpixel(( self.lon_grid[i], self.lat_grid[j] ))[0]

        array_Rain = self.array_Rain_max - array_Rain / self.array_Lowerbound * self.array_Rain_max
        array_Rain[array_Rain < 0] = 0
        rain_POS = np.where(array_Rain >= 0)
        rain_POS = np.transpose(rain_POS).tolist()
        rainfall = array_Rain[array_Rain >= 0]
        rain_data = griddata(rain_POS, rainfall, self.grid_xy, method='linear')  #linear雨量空間插值
        rain_interp_N = griddata(rain_POS, rainfall, self.grid_xy, method='nearest')  #nearest雨量空間插值
        rain_data[np.isnan(rain_data)] = rain_interp_N[np.isnan(rain_data)]  #由於linear插值會於邊界附近或缺值較多處無法進行空間插值，經空間插值後會變為nan值，其值將以nearest雨量空間插值取代
        rain_data[rain_data < 0] = 0  #若空間插值後有負值則設為0mm
        rain_data = np.round(np.rot90(rain_data, 1), 1)
        
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | [數化作業] 已完成：{time}")
        return rain_data

    '''
    #  new colorbar version
    def _image2num(self, time):
        inputimg_path = f'{self.input_img_path}rain_{self.model}_{time}.png'
        img_RGB = Image.open(inputimg_path).convert('RGB')
        array_Rain = np.zeros([self.array_lon, self.array_lat])
        for i in range( self.array_lon ):
            for j in range( self.array_lat ):
                array_Rain[i][j] = img_RGB.getpixel(( self.lon_grid[i], self.lat_grid[j] ))[0]

        rain_POS = np.where(array_Rain >= 0)
        rain_POS = np.transpose(rain_POS).tolist()
        rainfall = array_Rain[array_Rain >= 0]
        rain_data = griddata(rain_POS, rainfall, self.grid_xy, method='linear')  #linear雨量空間插值
        rain_interp_N = griddata(rain_POS, rainfall, self.grid_xy, method='nearest')  #nearest雨量空間插值
        rain_data[np.isnan(rain_data)] = rain_interp_N[np.isnan(rain_data)]  #由於linear插值會於邊界附近或缺值較多處無法進行空間插值，經空間插值後會變為nan值，其值將以nearest雨量空間插值取代
        rain_data[rain_data < 0] = 0  #若空間插值後有負值則設為0mm
        rain_data = np.round(np.rot90(rain_data/2 , 1), 1)
        
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | [數化作業] 已完成：{time}")
        return rain_data
    '''

    def make_rain_data(self):
        rain_data_output = self._create_array()
        h = 0
        for t in range(len(self.time_list)):
            time = self.time_list[t]
            rain_data = self._image2num(time)
            rain_hourly = rain_data/3 

            values, counts = np.unique(rain_hourly, return_counts=True)
            if (min(values) != 0 and max(counts) > 10000):
                print("Angel Warning: NO AVAILABLE DATA, replace with previous time step data")
                rain_hourly = rain_data_output[:,:,h-1]

            if self.frcst_timegap[t]==1:
                rain_data_output[ :, :, h] = rain_hourly 
                h += int(self.frcst_timegap[t])
            
            elif self.frcst_timegap[t]==3:
                data_tmp = rain_hourly 
                rain_data_output[ :, :, h:h+3] = np.repeat(data_tmp[:, :, np.newaxis], 3, axis=2)
                h += int(self.frcst_timegap[t])

            else:  #forecast_timegap[t]==6
                data_tmp = rain_hourly 
                rain_data_output[ :, :, h:h+6] = np.repeat(data_tmp[:, :, np.newaxis], 6, axis=2)
                h += int(self.frcst_timegap[t])
                
        # shutil.rmtree(self.input_img_path)
        return rain_data_output

    def get_data_folder_name(self):
        str_yyyy = self.init_time_dt.strftime('%Y')  
        str_jjj = self.init_time_dt.strftime('%j') 
        str_mmm = self.init_time_dt.strftime('%b') 
        str_dd = self.init_time_dt.strftime('%d') 
        str_hh = self.init_time_dt.strftime('%H') 
        self.nc_path = os.path.join(self.output_data_path, 
                                    'nc',
                                    str_yyyy, 
                                    f'{str_jjj}{str_mmm}{str_dd}',
                                    str_hh)
        self.json_path = os.path.join(self.output_data_path, 
                                      'json',
                                      str_yyyy, 
                                      f'{str_jjj}{str_mmm}{str_dd}',
                                      str_hh)
        check_path_exist(self.nc_path)
        check_path_exist(self.json_path)
        return  

    def write_init_time(self):
        init_time = self.init_time_dt.strftime('%Y%m%d_%H')
        with open("./log/init_time.env", "w") as f:
            f.write(f'INIT={init_time}')
        return  

    def save_json(self, data):
        rain_timeseries = (pd.date_range(
        start = self.init_time_dt + timedelta(hours=8),
        end = self.init_time_dt + timedelta(hours = self.final_hour-1+8),
        freq='1H')).strftime('%Y-%m-%d-%H').tolist()
        self.init_time = self.init_time_dt.strftime('%Y-%m-%d %HZ')
        rain_data_output_json = {"Time(TST)": rain_timeseries ,
                            "Information": {"model": self.model, 
                                            "initial time(UTC)": self.init_time,
                                            "element": '1-hr accumulated rainfall forecast(mm)', 
                                            "lon": self.lon_domain.tolist(), 
                                            "lat": self.lat_domain.tolist()}, 
                            "Rain_data_1h": data.tolist()}
            
        self.list_datetime = [datetime.strptime(str_time,"%Y-%m-%d-%H") for str_time in rain_timeseries] # [str] str: yyyy-mm-dd HH:MM:SS
        self.str_init_time = self.init_time_dt.strftime('%Y%m%d_%HZ')
        json_file = os.path.join(self.json_path, f'{self.model}_{self.str_init_time}.json')
        with open(json_file, "w") as file:
            json.dump(rain_data_output_json, file)

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | [資料輸出] 已完成：JSON")
        return

    def save_nc(self, data):
        input_to_nc ={
                'lon' : self.lon_domain, # float 
                'lat' : self.lat_domain, # float 
                'time_list' : self.list_datetime, # datetime format 
                'rain' : np.transpose(data, (2, 0, 1)), # np array
                'file_path' : self.nc_path, # float  
                'file_name' : f'{self.model}_{self.str_init_time}.nc' , # float  
                }
        nc_data = NcWritter(**input_to_nc)
        nc_data()

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | [資料輸出] 已完成：NC")
        return

def check_path_exist(path_list):
    if isinstance(path_list, str):
        if not os.path.exists(path_list):
            os.makedirs(path_list)
    if isinstance(path_list,list):
        for path in path_list:
            if not os.path.exists(path):
                os.makedirs(path)
    return 

def main(account, passwd, model, output_path):
    img_path  = os.path.join(output_path, 'screenshot')
    json_path = os.path.join(output_path, 'json')
    nc_path   = os.path.join(output_path, 'nc')
    needed_path = [img_path, json_path, nc_path]
    check_path_exist(needed_path)

    windy_driver = Windy(account, passwd, model, img_path = img_path)
    time_pack, img_full_path = windy_driver.screen_shot()

    windy_data = WindyData(time_pack = time_pack, 
                           model = model,
                           input_img_path = img_full_path,
                           output_data_path = output_path)
    data = windy_data.make_rain_data()
    windy_data.get_data_folder_name()
    windy_data.save_json(data)
    windy_data.save_nc(data)
    windy_data.write_init_time()
    sleep(5)
    return 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--account", type=str, 
                        help="enter your windy account") 
    parser.add_argument("-p", "--passwd", type=str,  
                        help="enter your windy password")
    parser.add_argument("-m", "--model", type=str, default='EC',
                        help="enter the model want to download : 'EC' or 'GFS'")
    parser.add_argument("-o", "--output_path", type=str, default='./data',
                        help="enter the data output path: ")
    args = parser.parse_args()
    main(args.account, args.passwd, args.model, args.output_path)
