"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import DEVICE_CLASS_ENERGY
from homeassistant.const import ENERGY_KILO_WATT_HOUR
from homeassistant.helpers.entity import Entity, generate_entity_id
from homeassistant.components.sensor import ENTITY_ID_FORMAT

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN, CONF_METER_ID

from random import randint
import logging

_LOGGER = logging.getLogger(__name__)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return
    
    meter_id = discovery_info[CONF_METER_ID]

    add_entities([Mojelektro("meter_input", hass, meter_id)])
    add_entities([Mojelektro("meter_input_peak", hass, meter_id)])
    add_entities([Mojelektro("meter_input_offpeak", hass, meter_id)])
    add_entities([Mojelektro("meter_output", hass, meter_id)])
    add_entities([Mojelektro("meter_output_peak", hass, meter_id)])
    add_entities([Mojelektro("meter_output_offpeak", hass, meter_id)])

    add_entities([Mojelektro("daily_input", hass, meter_id)])
    add_entities([Mojelektro("daily_input_peak", hass, meter_id)])
    add_entities([Mojelektro("daily_input_offpeak", hass, meter_id)])
    add_entities([Mojelektro("daily_output", hass, meter_id)])
    add_entities([Mojelektro("daily_output_peak", hass, meter_id)])
    add_entities([Mojelektro("daily_output_offpeak", hass, meter_id)])

    add_entities([Mojelektro("15min_output", hass, meter_id)])
    add_entities([Mojelektro("15min_input", hass, meter_id)])
    
    add_entities([Mojelektro("monthly_input", hass, meter_id)])
    add_entities([Mojelektro("monthly_input_peak", hass, meter_id)])
    add_entities([Mojelektro("monthly_input_offpeak", hass, meter_id)])



class Mojelektro(SensorEntity):
    """Representation of a sensor."""

    type = None

    def __init__(self, type, hass, meter_id) -> None:
        """Initialize the sensor."""
        super().__init__()

        self._state = None
        self.type = type
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, DOMAIN + "_" + type, hass=hass)
        self._unique_id = "{}-{}".format(meter_id, self.entity_id)
    
    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id
    
    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "MojElektro " + self.type

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return ENERGY_KILO_WATT_HOUR

    @property
    def state_class(self):
        """Return the state class."""
        return "total_increasing"

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_ENERGY
    
    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self.hass.data[DOMAIN].get(self.type)
