
from  NetatmoWeather import NetatmoWeather



net = NetatmoWeather()

test1 = net.get_home_info()
for id in test1:
    test2 = net.get_home_status(id)
    tmp = net.get_module_info(id)
    #need to change to struct
    if tmp:
        test2 = net.get_weather_info_cloud(tmp[0]['id'])
test2 = net.get_weather_info()
