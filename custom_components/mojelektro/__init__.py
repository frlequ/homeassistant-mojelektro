from __future__ import annotations
import logging
import voluptuous as vol

from datetime import datetime, timedelta

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval

from .moj_elektro_api import MojElektroApi

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

"""Example Load Platform integration."""
DOMAIN = 'mojelektro'



_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)

CONF_TOKEN = 'token'
CONF_METER_ID = 'meter_id'

ACCOUNT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOKEN): cv.string,
        vol.Required(CONF_METER_ID): cv.string
    }
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: ACCOUNT_SCHEMA}, extra=vol.ALLOW_EXTRA)

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Your controller/hub specific code."""
    # Data that you want to share with your platforms
    hass.data[DOMAIN] = {  }

    conf = config.get(DOMAIN)

    api = MojElektroApi(conf.get(CONF_TOKEN), conf.get(CONF_METER_ID))
    
    hass.helpers.discovery.load_platform('sensor', DOMAIN, conf, config)

    def refresh(event_time):
        """Refresh"""
        _LOGGER.debug("Trying to refresh cache...")
        
        
        minute = datetime.now().minute;
        if minute == 00 or minute == 15 or minute == 30 or minute == 45:
            _LOGGER.debug("Refreshing cache initiated...")
            hass.data[DOMAIN] = api.getData()
        else:

            _LOGGER.debug("Refreshing cache failed. Will try again in 30 seconds.")
            
    track_time_interval(hass, refresh, SCAN_INTERVAL)

    return True
