import requests
from datetime import datetime, timedelta
import logging
import json

_LOGGER = logging.getLogger(__name__)


class MojElektroApi:
    
    
    r_15min = '&option=ReadingType%3D32.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.72.0'
    r_daily = '&option=ReadingType%3D32.0.4.1.1.2.12.0.0.0.0.1.0.0.0.3.72.0&option=ReadingType%3D32.0.4.1.1.2.12.0.0.0.0.2.0.0.0.3.72.0&option=ReadingType%3D32.0.4.1.1.2.12.0.0.0.0.0.0.0.0.3.72.0'
    
    meter_id = None
    token = None
    date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    date_to = datetime.now().strftime("%Y-%m-%d")
    
    
    
    cache = None
    cacheDate = None
    cacheOK = False


    
    def __init__(self, token, meter_id): 
        self.meter_id = meter_id
        self.token = token


    def getMeterReadings(self, rType = None):
        

        if (rType == '15min'):
            self.readingType = self.r_15min
            self.date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            self.readingType = self.r_daily
            self.date_from = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            
        
        
        url = f'https://api.informatika.si/mojelektro/v1/meter-readings?usagePoint={self.meter_id}&startTime={self.date_from}&endTime={self.date_to}{self.readingType}'
        headers = {
            "accept": "application/json",
            "X-API-TOKEN": self.token
        }
        params = {

        }
        _LOGGER.debug(f"Connecting and getting meter data for day: {self.date_from} - {self.date_to}")
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


            d15 = cache.get("15")[self.get15MinOffset()]
            sensorReturn["15min_input"] = d15['value']


            sensorReturn["meter_input_peak"] = float(cache.get("VT")[int(len(cache.get("VT")))-1]['value'])
            sensorReturn["meter_input_offpeak"] = float(cache.get("MT")[int(len(cache.get("MT")))-1]['value'])
            sensorReturn["meter_input"] = float(cache.get("ET")[int(len(cache.get("ET")))-1]['value'])


            sensorReturn["daily_input_peak"] = float(cache.get("VT")[int(len(cache.get("VT")))-1]['value']) - float(cache.get("VT")[int(len(cache.get("VT")))-2]['value'])
            sensorReturn["daily_input_offpeak"] = float(cache.get("MT")[int(len(cache.get("MT")))-1]['value']) - float(cache.get("MT")[int(len(cache.get("MT")))-2]['value'])
            sensorReturn["daily_input"] = float(cache.get("ET")[int(len(cache.get("ET")))-1]['value']) - float(cache.get("ET")[int(len(cache.get("ET")))-2]['value'])
            
            sensorReturn["monthly_input_peak"] = float(cache.get("VT")[int(len(cache.get("VT")))-1]['value']) - float(cache.get("VT")[0]['value'])
            sensorReturn["monthly_input_offpeak"] = float(cache.get("MT")[int(len(cache.get("MT")))-1]['value']) - float(cache.get("MT")[0]['value'])
            sensorReturn["monthly_input"] = float(cache.get("ET")[int(len(cache.get("ET")))-1]['value']) - float(cache.get("ET")[0]['value'])


            #Test if mojElektro does have latest meter readings. A failsafe.
            curDate = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            machDate = datetime.strptime(cache.get("15")[0]['timestamp'], "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")

            if (curDate != machDate):
                _LOGGER.debug("Not current date.")

            sum15MinPart = sum(float(item['value']) for item in cache.get("15")[10:96])
            sum15Min = round(sum(float(item['value']) for item in cache.get("15")[0:96]), 5)
                          
            sumET = round(sensorReturn["daily_input"],5)
            
            
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
                    "15": meterReadings_15min[0]['intervalReadings'],
                    "VT": meterReadings_daily[2]['intervalReadings'],
                    "ET": meterReadings_daily[1]['intervalReadings'],
                    "MT": meterReadings_daily[0]['intervalReadings'],

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


