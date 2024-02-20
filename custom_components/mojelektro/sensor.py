from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.const import (
    ENERGY_KILO_WATT_HOUR,
    DEVICE_CLASS_ENERGY,
)


from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from homeassistant.helpers.entity import Entity, generate_entity_id
from homeassistant.components.sensor import ENTITY_ID_FORMAT

from .const import DOMAIN, CONF_TOKEN, CONF_METER_ID, CONF_DECIMAL
from .moj_elektro_api import (
    MojElektroApi,
)  # Ensure this matches the actual location and name
import logging
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
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
    # hass.data[DOMAIN][entry.entry_id]['coordinator'] = coordinator

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
        entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, f"{DOMAIN}_{measurement_name.lower()}", current_ids
        )

        self._attr_unique_id = f"{meter_id}-{entity_id}"
        self._attr_name = f"Moj Elektro {measurement_name.replace('_', ' ')}"
        self.measurement_name = measurement_name
        self._attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR
        self._attr_unit_of_measurement = "kWh"  # Direct string to avoid any confusion
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = "mdi:transmission-tower"
        self._attr_device_class = SensorDeviceClass.ENERGY

    @property
    def state(self):
        """Return the state of the sensor."""
        data = self.coordinator.data.get(self.measurement_name)
        return float(data) if data is not None else None
