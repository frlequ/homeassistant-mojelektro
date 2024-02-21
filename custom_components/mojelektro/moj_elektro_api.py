import requests
from datetime import datetime, timedelta
import json
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import asyncio

import aiohttp
from aiohttp import ClientSession
import logging

from .const import CONF_DECIMAL, SETUP_TAG_15_ARRAY, SETUP_TAG_ARRAY, READING_TYPE_ARRAY


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
                    return (
                        data.get("intervalBlocks") if "intervalBlocks" in data else None
                    )
                else:
                    _LOGGER.error(
                        f"HTTP error {response.status} when getting meter readings."
                    )
                return None
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error making API call: {e}")
            return None

    async def getData(self):
        """Get or update cache."""

        # Update only at quaterly hour or on empty last_data

        current_minute = datetime.now().minute
        if self.last_data is None or current_minute in [0, 15, 30, 45]:

            # Update Cache

            cache = await self.getCache()

            sensor_return = {}

            if cache is None:
                _LOGGER.debug("Data not recieved! Returning empty data.")
            else:
                # validate

                self.validateData(cache)

                # organize sensors

                sensor_return.update(
                    self.sensors_output(cache.get("15"), json.loads(SETUP_TAG_15_ARRAY))
                )
                sensor_return.update(
                    self.sensors_output(cache.get("meter"), json.loads(SETUP_TAG_ARRAY))
                )
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

            meter_readings_15min = await self.getMeterReadings("15min")
            meter_readings_daily = await self.getMeterReadings()

            if meter_readings_15min is None or meter_readings_daily is None:
                _LOGGER.error("No data received! Check user settings.")
                return None
            self.cache = {}
            # Ensure the results are lists or have a length before attempting to access them

            if isinstance(meter_readings_15min, list) and meter_readings_15min:
                self.cache.update({"15": meter_readings_15min})
            else:
                # return empty list

                self.cache.update({"15": []})
                _LOGGER.debug(
                    "15 min intervals are empty. Possible Mojelektro fault. Will continue with empty list."
                )
            if (
                isinstance(meter_readings_daily, list)
                and len(meter_readings_daily) >= 3
                and all(
                    "intervalReadings" in reading
                    for reading in meter_readings_daily[:3]
                )
            ):
                self.cache.update({"meter": meter_readings_daily})
            else:
                _LOGGER.debug(
                    "Key 'intervalReadings' not found in one of the meterReadings entries."
                )
        else:
            _LOGGER.debug("Cache has stored data. Will use self.cache.")
        return self.cache

    def get15MinOffset(self):
        """Get 15min index."""
        now = datetime.now()
        return int((now.hour * 60 + now.minute) / 15)

    def find_tag(self, tag_to_find, data_list, search):
        """Hulahop."""
        if search == 4:
            for index, interval_block in enumerate(data_list):
                if interval_block.get("readingType") == tag_to_find:
                    return index
            return -1
        else:

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

    def define_request(self, rType=None):
        """Define url and request parameters."""
        params = ""
        if rType == "15min":
            data = json.loads(SETUP_TAG_15_ARRAY)
        else:
            data = json.loads(SETUP_TAG_ARRAY)
        for block in data:
            # construct setup

            tag = block.get("oznaka")

            # get readingTypes

            readingType = self.find_tag(tag, json.loads(READING_TYPE_ARRAY), 2)
            if readingType != None:
                # construct Url params:

                params = params + "&option=ReadingType%3D" + readingType
        current_date = datetime.now()
        self.date_to = current_date.strftime("%Y-%m-%d")
        if rType == "15min":
            self.date_from = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
            url = f"https://api.informatika.si/mojelektro/v1/meter-readings?usagePoint={self.meter_id}&startTime={self.date_from}&endTime={self.date_to}{params}"
        else:
            if current_date.day == 1:
                self.date_from = (
                    (current_date.replace(day=1) - timedelta(days=1))
                    .replace(day=1)
                    .strftime("%Y-%m-%d")
                )
            else:
                self.date_from = current_date.replace(day=1).strftime("%Y-%m-%d")
            url = f"https://api.informatika.si/mojelektro/v1/meter-readings?usagePoint={self.meter_id}&startTime={self.date_from}&endTime={self.date_to}{params}"
        return url

    def sensors_output(self, data, setup):
        """Organize sensors and calculate values."""
        sensor_output = {}

        if not data:
            # return 0 instead od unavailable

            for item in json.loads(SETUP_TAG_15_ARRAY):
                sensor_output[item["sensor"]] = "0.0"
        else:
            for block in data:
                reading_type = block.get("readingType", "")

                # find tag for readingType

                tag = self.find_tag(reading_type, json.loads(READING_TYPE_ARRAY), 1)
                sensor = self.find_tag(tag, setup, 3)

                if sensor.split("_")[0] == "15min":

                    value = block.get("intervalReadings")[self.get15MinOffset()][
                        "value"
                    ]
                    sensor_output[sensor] = str(value)
                else:
                    blockLen = len(block.get("intervalReadings", []))

                    # calculate monthly energy

                    valuemonth = float(
                        block.get("intervalReadings")[blockLen - 1]["value"]
                    ) - float(block.get("intervalReadings")[0]["value"])

                    # calculate daily energy

                    value = float(
                        block.get("intervalReadings")[blockLen - 1]["value"]
                    ) - float(block.get("intervalReadings")[blockLen - 2]["value"])

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
            # Check data against itself. This is nessesary as Mojelektro can parse wrong data.

            cur_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            match_date = datetime.strptime(
                cache.get("15")[0]["intervalReadings"][0]["timestamp"],
                "%Y-%m-%dT%H:%M:%S%z",
            ).strftime("%Y-%m-%d")

            # Ugly way get 15min

            index = self.find_tag(
                "32.0.2.4.1.2.12.0.0.0.0.0.0.0.0.0.3.72.0", cache.get("15"), 4
            )
            sum_15min_part = sum(
                float(item["value"])
                for item in cache.get("15")[index]["intervalReadings"][10:96]
            )
            sum_15min = round(
                sum(
                    float(item["value"])
                    for item in cache.get("15")[index]["intervalReadings"][0:96]
                ),
                self.decimal,
            )

            # Ugly way get daily

            index = self.find_tag(
                "32.0.4.1.1.2.12.0.0.0.0.0.0.0.0.3.72.0", cache.get("meter"), 4
            )
            blockLen = len(cache.get("meter")[index]["intervalReadings"])

            sum_et = round(
                float(
                    cache.get("meter")[index]["intervalReadings"][blockLen - 1]["value"]
                )
                - float(
                    cache.get("meter")[index]["intervalReadings"][blockLen - 2]["value"]
                ),
                self.decimal,
            )

            if sum_15min == sum_et and sum_15min_part > 0 and cur_date == match_date:
                self.cacheOK = True
                _LOGGER.debug(
                    "15min and daily meter data seems correct: %s (15min) vs daily %s (daily). Dates also match.",
                    sum_15min,
                    sum_et,
                )
            elif cur_date != match_date:
                self.cacheOK = False
                _LOGGER.debug(
                    "Dates do not match: %s and %s. Possible Mojelektro fault.",
                    cur_date,
                    match_date,
                )
            else:
                self.cacheOK = False
                _LOGGER.debug(
                    "15min and daily meter data does not match: %s (15min) vs %s (daily). Or dates %s and %s. Possible Mojelektro fault.",
                    sum_15min,
                    sum_et,
                    cur_date,
                    match_date,
                )
        if self.cacheOK:
            self.cache_date = datetime.today().date()
            _LOGGER.debug(
                "cache_date updated to today. Data seems correct. Updating sensors..."
            )
