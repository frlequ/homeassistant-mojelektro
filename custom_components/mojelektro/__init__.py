from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data

    # Migrate existing entities to be grouped under a single device
    await migrate_existing_entities_to_device(hass, entry)

    # Forward the setup to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


async def migrate_existing_entities_to_device(hass: HomeAssistant, entry: ConfigEntry):
    """Migrate old entities without devices to a single device."""
    entity_registry = er.async_get(hass)
    meter_id = entry.data.get("meter_id")
    
    _LOGGER.info(f"Entity migration started for meter_id {meter_id}.")

    # Find all entities for this integration
    for entity_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        # If the entity doesn't have a device_id, we'll assign it to the new device
        if entity_entry.device_id is None:
            _LOGGER.debug(f"Migrating entity {entity_entry.entity_id} to new device.")




    
    _LOGGER.debug(f"Entity migration completed for integration {DOMAIN}.")
