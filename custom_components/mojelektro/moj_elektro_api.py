import requests
from datetime import datetime, timedelta
import logging
import json

_LOGGER = logging.getLogger(__name__)


class MojElektroApi:

    meter_id = None
    token = None

    
    date_from = None
    date_to = None
    
    cache = None
    cacheDate = None
    cacheOK = False
    
    #setup sensor tags
    setupTag15Array = '[{"oznaka": "A+", "sensor": "15min_input"}, {"oznaka": "A-", "sensor": "15min_output"} ] '
    setupTagArray = '[{"oznaka": "A+_T5", "sensor": "montly_input"},{"oznaka": "A+_T0", "sensor": "daily_input"}, {"oznaka": "A+_T1", "sensor": "daily_input_peak"}, {"oznaka": "A+_T2", "sensor": "daily_input_offpeak"}, {"oznaka": "A-_T0", "sensor": "daily_output"}, {"oznaka": "A-_T1", "sensor": "daily_output_peak"}, {"oznaka": "A-_T2", "sensor": "daily_ouput_offpeak"}]'
    readingTypeArray = '[ { "naziv": "Prejeta 15 minutna delovna energija", "opis": "15 minutna energija, A+, kWh", "oznaka": "A+", "perioda": "15 min", "readingType": "32.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.72.0", "readingTypeBrezObracuna": "0.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.72.0", "readingTypeObracun": "8.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.72.0", "tip": "delovna prejem", "vrsta": "KOLICINA" }, { "naziv": "Oddana 15 minutna delovna energija", "opis": "15 minutna energija, A-, kWh", "oznaka": "A-", "perioda": "15 min", "readingType": "32.0.2.4.19.2.12.0.0.0.0.0.0.0.0.3.72.0", "readingTypeBrezObracuna": "0.0.2.4.19.2.12.0.0.0.0.0.0.0.0.3.72.0", "readingTypeObracun": "8.0.2.4.19.2.12.0.0.0.0.0.0.0.0.3.72.0", "tip": "delovna oddaja", "vrsta": "KOLICINA" }, { "naziv": "Prejeta 15 minutna jalova energija", "opis": "15 minutna energija, R+, kVArh", "oznaka": "R+", "perioda": "15 min", "readingType": "32.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.73.0", "readingTypeBrezObracuna": "0.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.73.0", "readingTypeObracun": "8.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.73.0", "tip": "jalova prejem", "vrsta": "KOLICINA" }, { "naziv": "Oddana 15 minutna jalova energija", "opis": "15 minutna energija, R-, kVArh", "oznaka": "R-", "perioda": "15 min", "readingType": "32.0.2.4.19.2.12.0.0.0.0.0.0.0.0.3.73.0", "readingTypeBrezObracuna": "0.0.2.4.19.2.12.0.0.0.0.0.0.0.0.3.73.0", "readingTypeObracun": "8.0.2.4.19.2.12.0.0.0.0.0.0.0.0.3.73.0", "tip": "jalova oddaja", "vrsta": "KOLICINA" }, { "naziv": "Prejeta 15 minutna delovna moč", "opis": "15 minutna moč, A+, kW", "oznaka": "P+", "perioda": "15 min", "readingType": "32.0.2.4.1.2.37.0.0.0.0.0.0.0.0.3.38.0", "readingTypeBrezObracuna": "0.0.2.4.1.2.37.0.0.0.0.0.0.0.0.3.38.0", "readingTypeObracun": "8.0.2.4.1.2.37.0.0.0.0.0.0.0.0.3.38.0", "tip": "delovna prejem", "vrsta": "KOLICINA" }, { "naziv": "Oddana 15 minutna delovna moč", "opis": "15 minutna moč, A-, kW", "oznaka": "P-", "perioda": "15 min", "readingType": "32.0.2.4.19.2.37.0.0.0.0.0.0.0.0.3.38.0", "readingTypeBrezObracuna": "0.0.2.4.19.2.37.0.0.0.0.0.0.0.0.3.38.0", "readingTypeObracun": "8.0.2.4.19.2.37.0.0.0.0.0.0.0.0.3.38.0", "tip": "delovna oddaja", "vrsta": "KOLICINA" }, { "naziv": "Prejeta 15 minutna jalova moč", "opis": "15 minutna moč, R+, kVAr", "oznaka": "Q+", "perioda": "15 min", "readingType": "32.0.2.4.1.2.37.0.0.0.0.0.0.0.0.3.63.0", "readingTypeBrezObracuna": "0.0.2.4.1.2.37.0.0.0.0.0.0.0.0.3.63.0", "readingTypeObracun": "8.0.2.4.1.2.37.0.0.0.0.0.0.0.0.3.63.0", "tip": "jalova prejem", "vrsta": "KOLICINA" }, { "naziv": "Oddana 15 minutna jalova moč", "opis": "15 minutna moč, R-, kVAr", "oznaka": "Q-", "perioda": "15 min", "readingType": "32.0.2.4.19.2.37.0.0.0.0.0.0.0.0.3.63.0", "readingTypeBrezObracuna": "0.0.2.4.19.2.37.0.0.0.0.0.0.0.0.3.63.0", "readingTypeObracun": "8.0.2.4.19.2.37.0.0.0.0.0.0.0.0.3.63.0", "tip": "jalova oddaja", "vrsta": "KOLICINA" }, { "naziv": "Prejeta delovna energija ET", "opis": "24 urno stanje, A+, kWh, T0", "oznaka": "A+_T0", "perioda": "24 h", "readingType": "32.0.4.1.1.2.12.0.0.0.0.0.0.0.0.3.72.0", "readingTypeBrezObracuna": "0.0.4.1.1.2.12.0.0.0.0.0.0.0.0.3.72.0", "readingTypeObracun": "8.0.4.1.1.2.12.0.0.0.0.0.0.0.0.3.72.0", "tip": "delovna prejem ET", "vrsta": "STANJE" }, { "naziv": "Prejeta delovna energija VT", "opis": "24 urno stanje, A+, kWh, T1", "oznaka": "A+_T1", "perioda": "24 h", "readingType": "32.0.4.1.1.2.12.0.0.0.0.1.0.0.0.3.72.0", "readingTypeBrezObracuna": "0.0.4.1.1.2.12.0.0.0.0.1.0.0.0.3.72.0", "readingTypeObracun": "8.0.4.1.1.2.12.0.0.0.0.1.0.0.0.3.72.0", "tip": "delovna prejem VT", "vrsta": "STANJE" }, { "naziv": "Prejeta delovna energija MT", "opis": "24 urno stanje, A+, kWh, T2", "oznaka": "A+_T2", "perioda": "24 h", "readingType": "32.0.4.1.1.2.12.0.0.0.0.2.0.0.0.3.72.0", "readingTypeBrezObracuna": "0.0.4.1.1.2.12.0.0.0.0.2.0.0.0.3.72.0", "readingTypeObracun": "8.0.4.1.1.2.12.0.0.0.0.2.0.0.0.3.72.0", "tip": "delovna prejem MT", "vrsta": "STANJE" }, { "naziv": "Oddana delovna energija ET", "opis": "24 urno stanje, A-, kWh, T0", "oznaka": "A-_T0", "perioda": "24 h", "readingType": "32.0.4.1.19.2.12.0.0.0.0.0.0.0.0.3.72.0", "readingTypeBrezObracuna": "0.0.4.1.19.2.12.0.0.0.0.0.0.0.0.3.72.0", "readingTypeObracun": "8.0.4.1.19.2.12.0.0.0.0.0.0.0.0.3.72.0", "tip": "delovna oddaja ET", "vrsta": "STANJE" }, { "naziv": "Oddana delovna energija VT", "opis": "24 urno stanje, A-, kWh, T1", "oznaka": "A-_T1", "perioda": "24 h", "readingType": "32.0.4.1.19.2.12.0.0.0.0.1.0.0.0.3.72.0", "readingTypeBrezObracuna": "0.0.4.1.19.2.12.0.0.0.0.1.0.0.0.3.72.0", "readingTypeObracun": "8.0.4.1.19.2.12.0.0.0.0.1.0.0.0.3.72.0", "tip": "delovna oddaja VT", "vrsta": "STANJE" }, { "naziv": "Oddana delovna energija MT", "opis": "24 urno stanje, A-, kWh, T2", "oznaka": "A-_T2", "perioda": "24 h", "readingType": "32.0.4.1.19.2.12.0.0.0.0.2.0.0.0.3.72.0", "readingTypeBrezObracuna": "0.0.4.1.19.2.12.0.0.0.0.2.0.0.0.3.72.0", "readingTypeObracun": "8.0.4.1.19.2.12.0.0.0.0.2.0.0.0.3.72.0", "tip": "delovna oddaja MT", "vrsta": "STANJE" }, { "naziv": "Prejeta jalova energija ET", "opis": "24 urno stanje, R+, kVArh, T0", "oznaka": "R+_T0", "perioda": "24 h", "readingType": "32.0.4.1.1.2.12.0.0.0.0.0.0.0.0.3.73.0", "readingTypeBrezObracuna": "0.0.4.1.1.2.12.0.0.0.0.0.0.0.0.3.73.0", "readingTypeObracun": "8.0.4.1.1.2.12.0.0.0.0.0.0.0.0.3.73.0", "tip": "jalova prejem ET", "vrsta": "STANJE" }, { "naziv": "Prejeta jalova energija VT", "opis": "24 urno stanje, R+, kVArh, T1", "oznaka": "R+_T1", "perioda": "24 h", "readingType": "32.0.4.1.1.2.12.0.0.0.0.1.0.0.0.3.73.0", "readingTypeBrezObracuna": "0.0.4.1.1.2.12.0.0.0.0.1.0.0.0.3.73.0", "readingTypeObracun": "8.0.4.1.1.2.12.0.0.0.0.1.0.0.0.3.73.0", "tip": "jalova prejem VT", "vrsta": "STANJE" }, { "naziv": "Prejeta jalova energija MT", "opis": "24 urno stanje, R+, kVArh, T2", "oznaka": "R+_T2", "perioda": "24 h", "readingType": "32.0.4.1.1.2.12.0.0.0.0.2.0.0.0.3.73.0", "readingTypeBrezObracuna": "0.0.4.1.1.2.12.0.0.0.0.2.0.0.0.3.73.0", "readingTypeObracun": "8.0.4.1.1.2.12.0.0.0.0.2.0.0.0.3.73.0", "tip": "jalova prejem MT", "vrsta": "STANJE" }, { "naziv": "Oddana jalova energija ET", "opis": "24 urno stanje, R-, kVArh, T0", "oznaka": "R-_T0", "perioda": "24 h", "readingType": "32.0.4.1.19.2.12.0.0.0.0.0.0.0.0.3.73.0", "readingTypeBrezObracuna": "0.0.4.1.19.2.12.0.0.0.0.0.0.0.0.3.73.0", "readingTypeObracun": "8.0.4.1.19.2.12.0.0.0.0.0.0.0.0.3.73.0", "tip": "jalova oddaja ET", "vrsta": "STANJE" }, { "naziv": "Oddana jalova energija VT", "opis": "24 urno stanje, R-, kVArh, T1", "oznaka": "R-_T1", "perioda": "24 h", "readingType": "32.0.4.1.19.2.12.0.0.0.0.1.0.0.0.3.73.0", "readingTypeBrezObracuna": "0.0.4.1.19.2.12.0.0.0.0.1.0.0.0.3.73.0", "readingTypeObracun": "8.0.4.1.19.2.12.0.0.0.0.1.0.0.0.3.73.0", "tip": "jalova oddaja VT", "vrsta": "STANJE" }, { "naziv": "Oddana jalova energija MT", "opis": "24 urno stanje, R-, kVArh, T2", "oznaka": "R-_T2", "perioda": "24 h", "readingType": "32.0.4.1.19.2.12.0.0.0.0.2.0.0.0.3.73.0", "readingTypeBrezObracuna": "0.0.4.1.19.2.12.0.0.0.0.2.0.0.0.3.73.0", "readingTypeObracun": "8.0.4.1.19.2.12.0.0.0.0.2.0.0.0.3.73.0", "tip": "jalova oddaja MT", "vrsta": "STANJE" } ]'
    
    def __init__(self, token, meter_id): 
        self.meter_id = meter_id
        self.token = token


    def getMeterReadings(self, rType = None):
        
        url = self.define_request(rType)
        headers = {
            "accept": "application/json",
            "X-API-TOKEN": self.token
        }
        params = {

        }
        _LOGGER.debug(f"Connecting and getting meter data.")
        try:
            r = requests.get(url, headers=headers, params=params)
            r.raise_for_status()  # Raise an exception for HTTP errors

            # Check if the response has 'intervalBlocks' key
            if 'intervalBlocks' in r.json() and len(r.json()['intervalBlocks']) > 0:
                # Assuming that the presence of 'intervalBlocks' indicates success
                _LOGGER.debug(r.json())
                return r.json()['intervalBlocks']
            else:
                _LOGGER.debug(f"API call was not successful. Response content: {r.text}")
                return None

        except requests.exceptions.RequestException as e:
            _LOGGER.debug(f"Error making API call: {e}")
            return None


    def getData(self):

        cache = self.getCache()
        
        sensorReturn = {}
        
        if (cache == None ):
            _LOGGER.debug(f"No cache data!")
            return None
        else:

            #print (cache.get("15"))
            d15 = cache.get("15")[0]['intervalReadings'][self.get15MinOffset()]
            sensorReturn["15min_input"] = cache.get("15")[0]['intervalReadings'][self.get15MinOffset()]['value']
            
            sensorReturn.update(self.sensors_output(cache.get('meter')))
            

            #Test if mojElektro does have latest meter readings. A failsafe.
            curDate = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            machDate = datetime.strptime(cache.get("15")[0]['intervalReadings'][0]['timestamp'], "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")

            if (curDate != machDate):
                _LOGGER.debug("Not current date.")

            sum15MinPart = sum(float(item['value']) for item in cache.get("15")[0]['intervalReadings'][10:96])
            sum15Min = round(sum(float(item['value']) for item in cache.get("15")[0]['intervalReadings'][0:96]), 5)
                          
            sumET = round(float(sensorReturn["daily_input"]),5)
            
            
            if (sum15Min == sumET and sum15MinPart > 0 and curDate == machDate):
                self.cacheOK = True
                _LOGGER.debug(f"Meter data seems correct: {sum15Min} vs {sumET}. And date match.")
                
            elif (curDate != machDate):
                self.cacheOK = False
                _LOGGER.debug(f"Dates does not match: {curDate} and {machDate}")
            else:
                self.cacheOK = False
                _LOGGER.debug(f"Meter does not match: {sum15Min} vs {sumET}. Or dates {curDate} and {machDate}. A possible mojElektro fault.")

                        
            if self.cacheOK == True:
                self.cacheDate = datetime.today().date()
                _LOGGER.debug("CacheDate updated to today, every data is ok")

            return sensorReturn

    def getCache(self):
        
        if self.cache is None or self.cacheDate != datetime.today().date():
            _LOGGER.debug("Cache has no stored data. Refreshing from API...")
            

            #Connect to API

            meterReadings_15min = self.getMeterReadings('15min')
            meterReadings_daily = self.getMeterReadings()   


            
            if (meterReadings_15min == None or (meterReadings_daily == None)):
                _LOGGER.debug(f"No data recieved! Check user settings.")
                return None
            
            if ('intervalReadings' in meterReadings_15min[0]) and ('intervalReadings' in meterReadings_daily[0]) and ('intervalReadings' in meterReadings_daily[1]) and ('intervalReadings' in meterReadings_daily[2]):
                self.cache = {
                    "15": meterReadings_15min,
                    "meter": meterReadings_daily
                    
                }

            else:
                _LOGGER.debug("Key 'intervalReadings' not found in one of the meterReadings entries.")
        
        else:
    
            #Use Cached data
            _LOGGER.debug("Cache has stored data. Will use self.cache.")
            
        return self.cache
        
        
    def get15MinOffset(self):
        now = datetime.now()
        
        return int((now.hour * 60 + now.minute)/15)  



    def find_tag(self, tag_to_find, data_list, search):
        for item in data_list:
            if search == 1:
                if item["readingType"] == tag_to_find:
                    return item.get("oznaka")
            elif search == 2:        
                if item["oznaka"] == tag_to_find:
                    return item.get("readingType")

            elif search == 3:
                if item["oznaka"] == tag_to_find:
                    return item["sensor"]

        return None


    def define_request(self, rType = None):

        params = ''
        if rType == '15min':
            data = json.loads(self.setupTag15Array)
        else:
            data = json.loads(self.setupTagArray)
        for block in data:
            #construct setup
            tag = block.get("oznaka")
            
            #get readingTypes
            readingType = self.find_tag(tag, json.loads(self.readingTypeArray), 2)
            if readingType != None:
                #construct Url params:
                params = params + "&option=ReadingType%3D" + readingType

        if rType == '15min':
            current_date = datetime.now()
            date_from = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
            date_to = current_date.strftime("%Y-%m-%d")
            url = f'https://api.informatika.si/mojelektro/v1/meter-readings?usagePoint={self.meter_id}&startTime={date_from}&endTime={date_to}{params}'
            
        else:
            current_date = datetime.now()
            if current_date.day == 1:
                date_from = (current_date.replace(day=1) - timedelta(days=1)).replace(day=1).strftime("%Y-%m-%d")
            else:
                date_from = current_date.replace(day=1).strftime("%Y-%m-%d")
            date_to = current_date.strftime("%Y-%m-%d")
            
            url = f'https://api.informatika.si/mojelektro/v1/meter-readings?usagePoint={self.meter_id}&startTime={date_from}&endTime={date_to}{params}'
        
        return url

    def sensors_output(self, data):
        sensorReturn = {}

        for block in data:
            reading_type = block.get("readingType", "")
            
            #find tag for readingType
            tag = self.find_tag(reading_type, json.loads(self.readingTypeArray),1)
            sensor = self.find_tag(tag, json.loads(self.setupTagArray),3)

            
            blockLen = len(block.get("intervalReadings", []))
            #calculate montly energy
            valuemonth = float(block.get("intervalReadings")[blockLen-1]['value']) - float(block.get("intervalReadings")[0]['value'])
            

            #calculate daily energy
            value = float(block.get("intervalReadings")[blockLen-1]['value']) - float(block.get("intervalReadings")[blockLen-2]['value'])
                
            sensorReturn[sensor] = str(value)
            
            
            sensorMontly = sensor.replace("daily", "monthly")
            sensorReturn[sensorMontly] = str(valuemonth)
            
        
        return sensorReturn
