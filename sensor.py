"""Platform for ATEM sensor integration - SIMPLIFIED."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AtemDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ATEM sensors from a config entry."""
    # Récupération du coordinateur
    coordinator: AtemDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Création des 2 sensors uniquement
    sensors = [
        AtemProgramSensor(coordinator, entry),
        AtemPreviewSensor(coordinator, entry),
    ]
    
    # Ajout des entités
    async_add_entities(sensors, update_before_add=True)


class AtemProgramSensor(CoordinatorEntity, SensorEntity):
    """Sensor for ATEM program input."""
    
    def __init__(self, coordinator: AtemDataUpdateCoordinator, entry: ConfigEntry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_program"
        self._attr_name = "ATEM Program"
        self._attr_icon = "mdi:video-input-hdmi"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"ATEM {entry.data.get('host', 'Unknown')}",
            "manufacturer": "Blackmagic Design",
            "model": "ATEM Switcher",
        }
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and "program_name" in self.coordinator.data:
            return self.coordinator.data["program_name"]
        elif self.coordinator.data and "program" in self.coordinator.data:
            return self.coordinator.data["program"]
        return "Unknown"
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        attrs = {}
        if self.coordinator.data:
            if "program" in self.coordinator.data:
                attrs["input_number"] = self.coordinator.data["program"]
            if "model" in self.coordinator.data:
                attrs["atem_model"] = self.coordinator.data["model"]
        return attrs


class AtemPreviewSensor(CoordinatorEntity, SensorEntity):
    """Sensor for ATEM preview input."""
    
    def __init__(self, coordinator: AtemDataUpdateCoordinator, entry: ConfigEntry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_preview"
        self._attr_name = "ATEM Preview"
        self._attr_icon = "mdi:video-input-hdmi"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"ATEM {entry.data.get('host', 'Unknown')}",
            "manufacturer": "Blackmagic Design",
            "model": "ATEM Switcher",
        }
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and "preview_name" in self.coordinator.data:
            return self.coordinator.data["preview_name"]
        elif self.coordinator.data and "preview" in self.coordinator.data:
            return self.coordinator.data["preview"]
        return "Unknown"
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        attrs = {}
        if self.coordinator.data:
            if "preview" in self.coordinator.data:
                attrs["input_number"] = self.coordinator.data["preview"]
            if "available_inputs" in self.coordinator.data:
                attrs["available_inputs"] = list(self.coordinator.data["available_inputs"].values())
        return attrs