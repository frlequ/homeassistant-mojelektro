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
from .moj_elektro_api import MojElektroApi  # Ensure this matches the actual location and name
import logging
from datetime import timedelta

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
        if self.measurement_name.startswith('casovniBlok'):
            # For casovniBlok sensors
            self._attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
            self._attr_unit_of_measurement = "kW"  # Direct string to avoid any confusion
            self._attr_device_class = SensorDeviceClass.POWER  # Use POWER device class for power sensors
            self._attr_icon = "mdi:flash"
        else:
            # For other sensors
            self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
            self._attr_unit_of_measurement = "kWh"  # Direct string to avoid any confusion
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            self._attr_icon = "mdi:transmission-tower"

    @property
    def state(self):
        """Return the state of the sensor."""
        data = self.coordinator.data.get(self.measurement_name)
        if data is not None:
            try:
                return float(data)
            except ValueError:
                return None
        return None