"""The ATEM Switcher integration - SIMPLIFIED."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AtemDataUpdateCoordinator

# Plateformes supportées
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure l'intégration à partir d'une entrée de configuration."""
    
    # Crée une instance du coordinateur de données
    coordinator = AtemDataUpdateCoordinator(hass, entry)
    
    # Effectue la première mise à jour des données et configure les événements
    await coordinator.async_config_entry_first_refresh()
    
    # Stocke l'instance du coordinateur
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    
    # Transfère la configuration aux plateformes
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge une entrée de configuration."""
    # Décharger les plateformes
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Récupérer et arrêter le coordinator
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_shutdown()
        
        # Nettoyer les données
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Si c'était la dernière instance, nettoyer complètement
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    
    return unload_ok