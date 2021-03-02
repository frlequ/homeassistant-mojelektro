import logging
import voluptuous as vol
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval

from .moj_elektro_api import MojElektroApi

"""Example Load Platform integration."""
DOMAIN = 'mojelektro'

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=15)

CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'
CONF_METER_ID = 'meter_id'

ACCOUNT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_METER_ID): cv.string
    }
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: ACCOUNT_SCHEMA}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    """Your controller/hub specific code."""
    # Data that you want to share with your platforms
    hass.data[DOMAIN] = {  }

    conf = config.get(DOMAIN)

    api = MojElektroApi(conf.get(CONF_USERNAME), conf.get(CONF_PASSWORD), conf.get(CONF_METER_ID))
    
    hass.helpers.discovery.load_platform('sensor', DOMAIN, conf, config)

    def refresh(event_time):
        """Refresh"""
        _LOGGER.debug("Refreshing...")
        hass.data[DOMAIN] = api.getData()

    track_time_interval(hass, refresh, SCAN_INTERVAL)

    return True
