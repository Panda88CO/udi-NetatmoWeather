
from  NetatmoWeather import NetatmoWeather



net = NetatmoWeather()

home_id = net.get_home_info()
for id in home_id:
    tmp = net.get_module_info(id)
    test2 = net.get_home_status(id)
    #need to change to struct
    if tmp:
        test3 = net.update_weather_info_cloud(tmp[0]['id'])
        test4 = net.update_weather_info_instant(tmp[0]['id'])

