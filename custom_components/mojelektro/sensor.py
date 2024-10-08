from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.const import (
    UnitOfEnergy,
    UnitOfPower,
)


from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from homeassistant.helpers.entity import generate_entity_id
from homeassistant.components.sensor import ENTITY_ID_FORMAT

from .const import DOMAIN, CONF_TOKEN, CONF_METER_ID, CONF_DECIMAL
from .const import SETUP_TAG_15_ARRAY, SETUP_TAG_ARRAY, READING_TYPE_ARRAY
from .moj_elektro_api import MojElektroApi  # Ensure this matches the actual location and name
import logging
from datetime import timedelta

import json

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up MojeElektro sensors dynamically from a config entry."""


    token = entry.data[CONF_TOKEN]
    meter_id = entry.data[CONF_METER_ID]
    decimal = entry.data.get(CONF_DECIMAL)
    session = async_get_clientsession(hass)


    api = MojElektroApi(token, meter_id, decimal, session)

    # Initialize the update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="mojelektro_sensor",
        update_method=api.getData,
        update_interval=timedelta(seconds=30),  # Adjust as necessary
    )

    # Fetch initial data
    await coordinator.async_refresh()

    # Store coordinator for reference in sensor entities
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Corrected part: Directly iterate over keys of coordinator.data
    sensors = [
        MojElektroSensor(coordinator, entry.entry_id, measurement, meter_id, hass)
        for measurement in coordinator.data.keys()
    ]
    async_add_entities(sensors)


class MojElektroSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor from MojElektro."""

    def __init__(self, coordinator, entry_id, measurement_name, meter_id, hass):


        super().__init__(coordinator)

        current_ids = hass.states.async_entity_ids()
        entity_id = generate_entity_id( ENTITY_ID_FORMAT, f"{DOMAIN}_{measurement_name.lower()}", current_ids )

        self._attr_unique_id = f"{meter_id}-{entity_id}"
        self._attr_name = f"Moj Elektro {measurement_name.replace('_', ' ')}"
        self.measurement_name = measurement_name
        self._last_known_state = None
        
        self._attr_unit_of_measurement = self.get_unit_of_measurement(measurement_name)
        self._attr_native_unit_of_measurement = self.to_native_unit_of_measurement(self._attr_unit_of_measurement)

        if self.measurement_name.startswith('casovni_blok'):
            # For casovni_blok sensors
            self._attr_device_class = SensorDeviceClass.POWER  # Use POWER device class for power sensors
            self._attr_icon = "mdi:flash"
        else:
            # For other sensors
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            self._attr_icon = "mdi:transmission-tower"

    def to_native_unit_of_measurement(self, unit_of_measurement):
        if unit_of_measurement == "kW":
            return UnitOfPower.KILO_WATT
        elif unit_of_measurement == "kWh":
            return UnitOfEnergy.KILO_WATT_HOUR
        else:
            _LOGGER.debug("missing conversion to native_unit_of_measurement for '%s'.", unit_of_measurement)
            return None

    def get_unit_of_measurement(self, measurement_name):
        oznaka = self.get_oznaka(measurement_name)
        
        if oznaka == None:
            if measurement_name.startswith('casovni_blok'):
                return "kW"
            else:
                return "kWh"

        for item in json.loads(READING_TYPE_ARRAY):
            if item.get("oznaka") == oznaka:
                return item.get("enota")

    def get_oznaka(self, measurement_name):
        for item in json.loads(SETUP_TAG_15_ARRAY):
            if item.get("sensor") == measurement_name:
                return item.get("oznaka")

        for item in json.loads(SETUP_TAG_ARRAY):
            if item.get("sensor") == measurement_name:
                return item.get("oznaka")

        _LOGGER.debug("oznaka for measurement '%s' not found.", measurement_name)
        return None

    @property
    def state(self):
        """Return the state of the sensor."""
        data = self.coordinator.data.get(self.measurement_name)
        if data is not None:
            try:
                # Store the current data as the last known good state
                self._last_known_state = float(data)
                return self._last_known_state
            except ValueError:
                pass
        
        # If data is None or invalid, return the last known good state for casovni_blok sensors
        if self.measurement_name.startswith('casovni_blok'):
            return self._last_known_state
            
        return None
