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
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.components.sensor import ENTITY_ID_FORMAT
import os
import json

from .const import DOMAIN, CONF_TOKEN, CONF_METER_ID, CONF_DECIMAL
from .moj_elektro_api import MojElektroApi  # Ensure this matches the actual location and name
import logging
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up MojeElektro sensors dynamically from a config entry."""

    # Load version once during setup
    version = await hass.async_add_executor_job(_get_version)

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
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        'coordinator': coordinator,
        'version': version
    }

    # Corrected part: Directly iterate over keys of coordinator.data
    sensors = [
        MojElektroSensor(coordinator, entry.entry_id, measurement, meter_id, hass, version)
        for measurement in coordinator.data.keys()
    ]
    async_add_entities(sensors)


class MojElektroSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor from MojElektro."""

    def __init__(self, coordinator, entry_id, measurement_name, meter_id, hass, version):


        super().__init__(coordinator)

        # Store meter_id as an instance variable
        self.meter_id = meter_id
        self._version = version

        current_ids = hass.states.async_entity_ids()
        entity_id = generate_entity_id( ENTITY_ID_FORMAT, f"{DOMAIN}_{measurement_name.lower()}", current_ids )

        self._attr_unique_id = f"{meter_id}-{entity_id}"
        self._attr_name = f"Moj Elektro {measurement_name.replace('_', ' ')}"
        self.measurement_name = measurement_name
        self._last_known_state = None

        if self.measurement_name.startswith('casovni_blok'):
            # For casovni_blok sensors
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
    def device_info(self):
        """Return device information for grouping sensors under a device."""
        return {
            "identifiers": {(DOMAIN, self.meter_id)},  # Use the stored meter_id
            "name": "Moj Elektro",
            "manufacturer": "Moj Elektro",
            "model": {self.meter_id},  # Include meter_id in the model
            "sw_version": self._version,
            "entry_type": DeviceEntryType.SERVICE,  # Use enum instead of string
        }
        _LOGGER.debug(f"Setting up device info {self.meter_id} .")
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

def _get_version() -> str:
    """Get the version from the manifest.json"""
    manifest_path = os.path.join(os.path.dirname(__file__), 'manifest.json')
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        return manifest.get('version', 'Unknown')
