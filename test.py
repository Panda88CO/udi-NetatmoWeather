
from  NetatmoWeather import NetatmoWeather

import time

net = NetatmoWeather()

home_ids = net.get_homes_info()
for id in home_ids:
    tmp = net.get_module_info(id)
    #test2 = net.get_home_status(id)
    #test3 = net.get_home_status()
    #need to change to struct
    if tmp:
        test3 = net.update_weather_info_cloud(id)
        #test4 = net.update_weather_info_cloud()
        net.update_weather_info_instant(id)
        
        data_main = net.get_main_module_data(id, tmp)

        time.sleep(60)
        net.update_weather_info_instant(id)
        test3 = net.update_weather_info_cloud(id)

