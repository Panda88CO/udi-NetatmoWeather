
from  NetatmoWeather import NetatmoWeather
from NetatmoControl import NetatmoControl
import time
mdata = {}
idata = {}
odata = {}
rdata = {}
wdata = {}


weather = NetatmoWeather()
ctrl = NetatmoControl()
home_ids = weather.get_homes()
#ctrl_ids = ctrl.get_homes_info()
id_test = '651b5a3d5688c0b6a0099b36'
id_saratoga = '5ea19b7f5f0d9668ce03609f'
id_tahoe = '60a013f74afaa9259c61dfea'
#for id in home_ids:
tst_id = id_saratoga


mod_list = []
tmp = weather.get_modules(tst_id)
for home in home_ids:
    home_name = home_ids[home]['name']
    main_modules =weather.get_main_modules(home)
    if main_modules:
        for m_module in main_modules:
            tst = {}
            tst['home'] = home
            tst['main_module'] = m_module
            mod_list.append(tst)
            tmp_s = weather.get_sub_modules(home, m_module)
            if tmp_s:
                for s_module in tmp_s:
                    sub_m = weather.get_module_info(home, s_module)

for nbr in range (0,len(mod_list)):
    temp= mod_list[nbr]
    module = weather.get_module_info(temp['home'], temp['main_module'])
    if 'name' in module:
        node_name = module['name']
    else:
        node_name = module['id']
    node_address = module['id']
    #node_name = self.getValidName(node_name)


tmp2 = weather.get_home_status(tst_id)

main_mods = weather.get_main_modules(tst_id)
indoor_mods = weather.get_indoor_modules(tst_id)
outdoor_mods = weather.get_outdoor_modules(tst_id)
rain_mods = weather.get_rain_modules(tst_id)
wind_mods = weather.get_wind_modules(tst_id)

    #test2 = weather.get_home_status(tst_id)
#test3 = weather.get_home_status()
#need to change to struct
if tmp2:
    weather.update_weather_info_cloud(tst_id)
    #test4 = weather.update_weather_info_cloud()
    weather.update_weather_info_instant(tst_id)

    
    for mod in main_mods:
        mdata[mod] = weather.get_main_module_data(tst_id, mod)
    for mod in indoor_mods:
        idata[mod] = weather.get_indoor_module_data(tst_id, mod)
    for mod in outdoor_mods:
        odata[mod] = weather.get_outdoor_module_data(tst_id, mod)
    for mod in rain_mods:
        rdata[mod] = weather.get_rain_module_data(tst_id, mod)
    for mod in wind_mods:
        wdata[mod] = weather.get_wind_module_data(tst_id, mod)
                    
    time.sleep(60)
    weather.update_weather_info_instant(tst_id)
    weather.update_weather_info_cloud(tst_id)


tst_id = id_test
home_ids = ctrl.get_homes()
#tmp = ctrl.get_module_info(tst_id)
#tmp2 = ctrl.get_home_status(tst_id)

#pwr_gateways = ctrl.get_power_gateways(tst_id)
#power_mods = ctrl.get_power_modules(tst_id)
#light_gateways = ctrl.get_lighting_gateways(tst_id)
#lighting_mods = ctrl.get_lighting_modules(tst_id)

print('Done')