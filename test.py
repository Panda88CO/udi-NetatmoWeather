
from  NetatmoWeather import NetatmoWeather
from NetatmoControl import NetatmoControl
import time
mdata = {}
idata = {}
odata = {}
rdata = {}
wdata = {}
#net = NetatmoWeather()
net = NetatmoControl()
home_ids = net.get_homes_info()
id_test = '651b5a3d5688c0b6a0099b36'
id_saratoga = '5ea19b7f5f0d9668ce03609f'
id_tahoe = '60a013f74afaa9259c61dfea'
#for id in home_ids:
id = id_test
tmp = net.get_module_info(id)
tmp2 = net.get_home_status()
#main_mods = net.get_main_modules(id)
#indoor_mods = net.get_indoor_modules(id)
#outdoor_mods = net.get_outdoor_modules(id)
#rain_mods = net.get_rain_modules(id)
#wind_mods = net.get_wind_modules(id)

    #test2 = net.get_home_status(id)
#test3 = net.get_home_status()
#need to change to struct
if tmp:
    test3 = net.update_weather_info_cloud(id)
    #test4 = net.update_weather_info_cloud()
    net.update_weather_info_instant(id)

    
    for mod in main_mods:
        mdata[mod] = net.get_main_module_data(id, mod)
    for mod in indoor_mods:
        idata[mod] = net.get_indoor_module_data(id, mod)
    for mod in outdoor_mods:
        odata[mod] = net.get_outdoor_module_data(id, mod)
    for mod in rain_mods:
        rdata[mod] = net.get_rain_module_data(id, mod)
    for mod in wind_mods:
        wdata[mod] = net.get_wind_module_data(id, mod)
                    
    time.sleep(60)
    net.update_weather_info_instant(id)
    test3 = net.update_weather_info_cloud(id)


