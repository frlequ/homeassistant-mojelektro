from datetime import datetime, timedelta, date
import json
import aiohttp
import logging
from dateutil import parser

from .const import SETUP_TAG_15_ARRAY, SETUP_TAG_ARRAY, READING_TYPE_ARRAY, SETUP_TAG_BLOCKS_ARRAY

_LOGGER = logging.getLogger(__name__)

class MojElektroApi:
    """Class to interact with the MojElektro API."""


    def __init__(self, token, meter_id, decimal, session):
        self.token = token
        self.meter_id = meter_id
        self.decimal = int(decimal) if decimal is not None else 4
        self.session = session
        self.cache = None
        self.cache_date = None
        self.cacheOK = False
        self.last_data = None
        self.first_load = None


    async def validate_token(self):
        """Validate the token by using the getMeterReadings method."""
        try:
            validate = await self.getData()
            return validate is not None
        except Exception as e:
            _LOGGER.error(f"Error during token validation: {e}")
            return False


    async def getMeterReadings(self, rType=None):
        """Primary API calls."""

        url = self.define_request(rType)
        headers = {"accept": "application/json", "X-API-TOKEN": self.token}
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug(data)
                    return data.get('intervalBlocks') if 'intervalBlocks' in data else None
                else:
                    _LOGGER.error(f"HTTP error {response.status} when getting meter readings.")
                    return None
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error making API call: {e}")
            return None


    async def getData(self):
        """Get or update cache."""

        # Update only at quaterly hour or on empty last_data
        current_minute = datetime.now().minute
        if self.last_data is None or current_minute in [0, 15, 30, 45]:

            #Update Cache
            cache = await self.getCache()

            sensor_return = {}

            if cache is None:
                _LOGGER.debug("Data not recieved! Returning empty data.")

            else:
                #validate
                self.validateData(cache)

                #organize sensors
                sensor_return.update(self.sensors_output(cache.get('15'), json.loads(SETUP_TAG_15_ARRAY)))
                sensor_return.update(self.sensors_output(cache.get('meter'), json.loads(SETUP_TAG_ARRAY)))
                
                #calc consumption by blocks
                sensor_return.update(self.consumption_by_block(cache.get('15'), json.loads(SETUP_TAG_BLOCKS_ARRAY)))
                
                # Fetch časovni blok values
                casovni_blok = await self.get_casovni_blok()
                sensor_return.update(casovni_blok)


            self.last_data = sensor_return
            return sensor_return
        else:
            _LOGGER.debug("Not time to update, returning last good data.")
            return self.last_data


    async def getCache(self):
        """Update cache from API if nessesary"""
        if self.cache is None or self.cache_date != datetime.today().date():
            _LOGGER.debug("Cache has no pre-stored data. Refreshing from API...")

            # Connect to API asynchronously
            meter_readings_15min = await self.getMeterReadings('15min')
            meter_readings_daily = await self.getMeterReadings()


            if meter_readings_15min is None or meter_readings_daily is None:
                _LOGGER.error("No data received! Check user settings.")
                return None


            self.cache = {}
            # Ensure the results are lists or have a length before attempting to access them
            if (isinstance(meter_readings_15min, list) and meter_readings_15min):
                self.cache.update({"15": meter_readings_15min })
            else:
                #return empty list
                self.cache.update({"15": [] })
                _LOGGER.debug("15 min intervals are empty. Possible Mojelektro fault. Will continue with empty list.")

            if (isinstance(meter_readings_daily, list) and len(meter_readings_daily) >= 3 and all('intervalReadings' in reading for reading in meter_readings_daily[:3])):
                self.cache.update({"meter": meter_readings_daily })
            else:
                _LOGGER.debug("Key 'intervalReadings' not found in one of the meterReadings entries.")

        else:
            _LOGGER.debug("Cache has stored data. Will use self.cache.")
        return self.cache


    def get15MinOffset(self):
        """Get 15min index."""
        now = datetime.now()
        return int((now.hour * 60 + now.minute)/15)


    def find_tag(self, tag_to_find, data_list, search):
        """Hulahop."""
        if search == 4:
            return self._find_by_reading_type(tag_to_find, data_list)
        elif search == 1:
            return self._find_by_key(data_list, "readingType", tag_to_find, "oznaka")
        elif search == 2:
            return self._find_by_key(data_list, "oznaka", tag_to_find, "readingType")
        elif search == 3:
            return self._find_by_key(data_list, "oznaka", tag_to_find, "sensor")
        return None

    def _find_by_reading_type(self, tag_to_find, data_list):
        for index, interval_block in enumerate(data_list):
            if interval_block.get("readingType") == tag_to_find:
                return index
        return -1

    def _find_by_key(self, data_list, search_key, tag_to_find, return_key):
        for item in data_list:
            if item.get(search_key) == tag_to_find:
                return item.get(return_key)
        return None



    def define_request(self, rType = None):
        """Define url and request parameters."""
        params = ''
        if rType == '15min':
            data = json.loads(SETUP_TAG_15_ARRAY)
        else:
            data = json.loads(SETUP_TAG_ARRAY)
        for block in data:
            #construct setup
            tag = block.get("oznaka")

            #get readingTypes
            readingType = self.find_tag(tag, json.loads(READING_TYPE_ARRAY), 2)
            if readingType != None:
                #construct Url params:
                params = params + "&option=ReadingType%3D" + readingType

        current_date = datetime.now()
        self.date_to = current_date.strftime("%Y-%m-%d")
        if rType == '15min':
            self.date_from = (current_date - timedelta(days=2)).strftime("%Y-%m-%d")
            self.date_to = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
            url = f'https://api.informatika.si/mojelektro/v1/meter-readings?usagePoint={self.meter_id}&startTime={self.date_from}&endTime={self.date_to}{params}'
        else:
            if current_date.day == 1:
                self.date_from = (current_date.replace(day=1) - timedelta(days=1)).replace(day=1).strftime("%Y-%m-%d")
            else:
                self.date_from = current_date.replace(day=1).strftime("%Y-%m-%d")
            url = f'https://api.informatika.si/mojelektro/v1/meter-readings?usagePoint={self.meter_id}&startTime={self.date_from}&endTime={self.date_to}{params}'
        return url


    def sensors_output(self, data, setup):
        """Organize sensors and calculate values."""
        sensor_output = {}

        if not data:
            #return 0 instead od unavailable
            for item in json.loads(SETUP_TAG_15_ARRAY):
                sensor_output[item["sensor"]] = "0.0"

        else:
            for block in data:
                reading_type = block.get("readingType", "")

                #find tag for readingType
                tag = self.find_tag(reading_type, json.loads(READING_TYPE_ARRAY),1)
                sensor = self.find_tag(tag, setup,3)

                if sensor.split("_")[0] == "15min":

                    value = block.get("intervalReadings")[self.get15MinOffset()]['value']
                    sensor_output[sensor] = str(round(float(value), self.decimal))

                else:
                    blockLen = len(block.get("intervalReadings", []))

                    #calculate monthly energy
                    valuemonth = float(block.get("intervalReadings")[blockLen-1]['value']) - float(block.get("intervalReadings")[0]['value'])

                    #calculate daily energy
                    value = float(block.get("intervalReadings")[blockLen-1]['value']) - float(block.get("intervalReadings")[blockLen-2]['value'])

                    sensor_output[sensor] = str(round(value, self.decimal))
                    sensorMontly = sensor.replace("daily", "monthly")    
                    sensor_output[sensorMontly] = str(round(valuemonth, self.decimal))
                    
        return sensor_output


    def validateData(self, data):
        """Validate data from Mojelektro."""

        cache = data


        if not cache.get("15") or not cache.get("meter"):
            self.cacheOK = False
        else:
            #Check data against itself. This is nessesary as Mojelektro can parse wrong data.
            cur_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
            match_date = datetime.strptime(cache.get("15")[0]['intervalReadings'][0]['timestamp'], "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")

            #Ugly way get 15min
            index = self.find_tag("32.0.2.4.1.2.12.0.0.0.0.0.0.0.0.0.3.72.0", cache.get("15"), 4)
            sum_15min_part = sum(float(item['value']) for item in cache.get("15")[index]['intervalReadings'][10:96])
            sum_15min = round(sum(float(item['value']) for item in cache.get("15")[index]['intervalReadings'][0:96]), self.decimal)


            #Ugly way get daily
            index = self.find_tag("32.0.4.1.1.2.12.0.0.0.0.0.0.0.0.3.72.0", cache.get("meter"), 4)
            blockLen = len(cache.get("meter")[index]['intervalReadings'])


            sum_et = round(float(cache.get("meter")[index]['intervalReadings'][blockLen-1]['value']) - float(cache.get("meter")[index]['intervalReadings'][blockLen-2]['value']), self.decimal)


            if sum_15min == sum_et and sum_15min_part > 0 and cur_date == match_date:
                self.cacheOK = True
                _LOGGER.debug("15min and daily meter data seems correct: %s (15min) vs daily %s (daily). Dates also match.", sum_15min, sum_et)
            elif cur_date != match_date:
                self.cacheOK = False
                _LOGGER.debug("Dates do not match: %s and %s. Possible Mojelektro fault.", cur_date, match_date)
            else:
                self.cacheOK = False
                _LOGGER.debug("15min and daily meter data does not match: %s (15min) vs %s (daily). Or dates %s and %s. Possible Mojelektro fault.", sum_15min, sum_et, cur_date, match_date)

        if self.cacheOK:
            self.cache_date = datetime.today().date()
            _LOGGER.debug("cache_date updated to today. Data seems correct. Updating sensors...")


    async def get_casovni_blok(self):
        """Get the 'casovni blok' values where 'veljavnost' is true and 'vrsta' is 'OMTO'."""
        url = f'https://api.informatika.si/mojelektro/v1/merilno-mesto/{self.meter_id}'
        headers = {"accept": "application/json", "X-API-TOKEN": self.token}

        try:
            response = await self._fetch_data(url, headers)
            if response:
                gsrn_omto = self._extract_gsrn_omto(response.get('merilneTocke', []))
                if gsrn_omto:
                    gsrn_data = await self._fetch_gsrn_data(gsrn_omto, headers)
                    if gsrn_data:
                        return self._extract_casovni_bloki(gsrn_data.get('dogovorjeneMoci', []))
                    else:
                        _LOGGER.error("Failed to fetch GSRN data.")
                else:
                    _LOGGER.error("No 'gsrn' found with 'vrsta' as 'OMTO'.")
            else:
                _LOGGER.error("Failed to fetch initial data.")
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error making API call: {e}")

        return {}

    async def _fetch_data(self, url, headers):
        """Fetch data from the given URL."""
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            _LOGGER.error(f"HTTP error {response.status} when getting data from {url}.")
            return None

    def _extract_gsrn_omto(self, merilna_mesta):
        """Extract GSRN value where 'vrsta' is 'OMTO'."""
        for mesto in merilna_mesta:
            if mesto.get('vrsta') == 'OMTO':
                return mesto.get('gsrn')
        return None

    async def _fetch_gsrn_data(self, gsrn_omto, headers):
        """Fetch GSRN data."""
        url_gsrn = f'https://api.informatika.si/mojelektro/v1/merilna-tocka/{gsrn_omto}'
        return await self._fetch_data(url_gsrn, headers)

    def _extract_casovni_bloki(self, dogovorjene_moci):
        """Extract 'casovni bloki' from 'dogovorjene moci'."""
        current_date = datetime.now()
        
        for moca in dogovorjene_moci:
            # Parse and convert the datetimes to naive datetimes
            datum_od = datetime.strptime(moca.get('datumOd'), "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
            datum_do = datetime.strptime(moca.get('datumDo'), "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
            
            # Check if the current date is within the validity period and veljavnost is true
            if moca.get('veljavnost') and datum_od <= current_date <= datum_do:
                return {f'casovni_blok_{i}': moca.get(f'casovniBlok{i}', 'N/A') for i in range(1, 6)}

        return {}
        
        
    # Calculate consumption by block
    def consumption_by_block(self, data, blocks):
        # Initialize variables to store summed values
        blocks_sums = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        # Specify the readingType
        reading_type = "32.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.72.0"

        for block in data:
            if block.get("readingType") == reading_type:
                # Extract intervalReadings from the block
                interval_readings = block.get("intervalReadings", [])
                _LOGGER.debug(f"interval_readings: {interval_readings} ")
                for reading in interval_readings:
                    timestamp = reading["timestamp"]
                    value = float(reading["value"])
                    
                    # Determine the block based on timestamp
                    block_num = self.calculate_tariff(timestamp)

                    # Sum the value into the corresponding block
                    blocks_sums[block_num] += value

        # Map block sums to sensor names
        result = {}
        for mapping in blocks:
            oznaka = mapping["oznaka"]
            sensor = mapping["sensor"]

            # Extract block number from 'oznaka' (e.g., "blok_1" -> 1)
            block_num = int(oznaka.split("_")[1])
            result[sensor] = round(blocks_sums[block_num], self.decimal)

        return result
        
    def calculate_easter(self, year):
        """Calculate Easter Sunday for a given year."""
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)

    def get_easter_saturday_monday(self, year):
        """Calculate Easter Saturday and Easter Monday for a given year."""
        easter_sunday = self.calculate_easter(year)
        easter_saturday = easter_sunday - timedelta(days=1)
        easter_monday = easter_sunday + timedelta(days=1)
        return easter_saturday, easter_monday

    def is_weekend_or_holiday(self, date):
        """Check if the date is a weekend or a public holiday in Slovenia."""
        # Check if it's Saturday or Sunday (weekend)
        if date.weekday() in [5, 6]:
            return True
        
        # List of fixed public holidays in Slovenia
        public_holidays = [
            (1, 1),    # New Year's Day
            (1, 2),    # New Year's Day
            (2, 8),    # Preseren Day
            (4, 27),   # Resistance Day
            (5, 1),    # Labour Day
            (5, 2),    # Labour Day
            (6, 25),   # Statehood Day
            (8, 15),   # Assumption Day
            (10, 31),  # National Reformation Day
            (11, 1),   # All Saints' Day
            (12, 25),  # Christmas
            (12, 26),  # Independence and Unity Day
        ]
        
        # Calculate Easter Saturday and Easter Monday for the year of the given date
        easter_saturday, easter_monday = self.get_easter_saturday_monday(date.year)
        
        # Add Easter Saturday and Easter Monday to the list of public holidays
        public_holidays.append((easter_saturday.month, easter_saturday.day))
        public_holidays.append((easter_monday.month, easter_monday.day))
        
        # Check if the date matches any public holiday
        if (date.month, date.day) in public_holidays:
            print("hollyday")
            return True

        return False


    def calculate_tariff(self, timestamp):

        
        date = parser.parse(timestamp) - timedelta(minutes=15)

        
        month = date.month
        hour = date.hour
        is_high_season = month in [11, 12, 1, 2]
        weekend_or_holiday = self.is_weekend_or_holiday(date)

        # Define tariff rates in a more structured form
        # (hour_range, high_season_rate, low_season_rate)
        tariffs = [
            ((0, 5), (3, 4), (5, 4)),  # Early morning
            ((6, 6), (2, 3), (4, 3)),  # 6 AM
            ((7, 13), (1, 2), (3, 2)),  # Morning to early afternoon
            ((14, 15), (2, 3), (4, 3)),  # Early afternoon
            ((16, 19), (1, 2), (3, 2)),  # Late afternoon to early evening
            ((20, 21), (2, 3), (4, 3)),  # Evening
            ((22, 23), (3, 4), (5, 4)),  # Late evening
        ]

        for time_range, high_season_tariff, low_season_tariff in tariffs:
            start, end = time_range
            if start <= hour <= end:
                if is_high_season and not weekend_or_holiday:
                    return high_season_tariff[0]
                elif not is_high_season and weekend_or_holiday:
                    return low_season_tariff[0]
                else:
                    return high_season_tariff[1] if is_high_season else low_season_tariff[1]
        
        # Default tariff if none of the conditions above are met
        return 0
