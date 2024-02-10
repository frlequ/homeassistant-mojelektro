from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval
from datetime import datetime, timedelta
from .const import DOMAIN
import logging


_LOGGER = logging.getLogger(__name__)



async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "sensor"))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


# async def async_setup(hass: HomeAssistant, config: dict):
    # return True

# # async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    # # hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data
    # # await hass.config_entries.async_forward_entry_setup(entry, "sensor")

    # # async def refresh_data(time):
        # # """Refresh data only at specific minutes."""
        # # minute = datetime.now().minute
        # # if minute in [0, 15, 30, 45]:
            # # coordinator = hass.data[DOMAIN][entry.entry_id]['coordinator']
            # # await coordinator.async_request_refresh()

    # # # Schedule data refresh
    # # async_track_time_interval(hass, refresh_data, timedelta(seconds=120))

    # # return True
    

# async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    # # Ensure the data structure for this entry is properly initialized
    # if DOMAIN not in hass.data:
        # hass.data[DOMAIN] = {}
    # hass.data[DOMAIN][entry.entry_id] = {
        # 'data': dict(entry.data),  # Store a mutable copy of entry data
    # }

    # hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "sensor"))

    # # Assume coordinator is initialized here and added to hass.data

    # async def conditionally_refresh_data(_):
        # """Refresh data only if current minute is 0, 15, 30, or 45."""
        # current_minute = datetime.now().minute
        # if current_minute in [0, 15, 30, 45]:
            # _LOGGER.debug("Current minute (%s) matches the condition, refreshing data...", current_minute)
            # coordinator = hass.data[DOMAIN][entry.entry_id]['coordinator']
            # await coordinator.async_request_refresh()
        # else:
            # _LOGGER.debug("Current minute (%s) does not match the condition, skipping data refresh.", current_minute)

    # # Set up a timer to check the condition every 120 seconds
    # async_track_time_interval(hass, conditionally_refresh_data, timedelta(seconds=120))

    # return True




# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    # await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    # hass.data[DOMAIN].pop(entry.entry_id)
    # return True