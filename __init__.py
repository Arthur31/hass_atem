"""The ATEM Switcher integration with services."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector

from .const import DOMAIN
from .coordinator import AtemDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

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
    
    # Enregistrer les services si pas déjà fait
    await async_setup_services(hass)
    
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
            # Désenregistrer les services
            for service_name in ["perform_cut", "set_program_input", "set_preview_input", "auto_transition"]:
                hass.services.async_remove(DOMAIN, service_name)
    
    return unload_ok


async def async_setup_services(hass: HomeAssistant) -> None:
    """Configure les services de l'intégration."""
    
    # Ne pas réenregistrer les services s'ils existent déjà
    if hass.services.has_service(DOMAIN, "perform_cut"):
        return
    
    async def get_coordinator() -> AtemDataUpdateCoordinator:
        """Get the first available coordinator."""
        if DOMAIN in hass.data and hass.data[DOMAIN]:
            # Retourne le premier coordinator disponible
            entry_id = next(iter(hass.data[DOMAIN]))
            return hass.data[DOMAIN][entry_id]
        raise ValueError("No ATEM coordinator available")
    
    async def handle_perform_cut(call: ServiceCall) -> None:
        """Gère le service perform_cut."""
        try:
            coordinator = await get_coordinator()
            if coordinator.switcher.connected:
                await hass.async_add_executor_job(
                    coordinator.switcher.execCutME,
                    0
                )
                # Forcer une mise à jour
                await coordinator.async_request_refresh()
                _LOGGER.info("Cut performed successfully")
            else:
                _LOGGER.error("Cannot perform cut: ATEM not connected")
        except Exception as e:
            _LOGGER.error(f"Error performing cut: {e}")
    
    async def handle_set_program_input(call: ServiceCall) -> None:
        """Gère le service set_program_input."""
        try:
            coordinator = await get_coordinator()
            
            # Récupérer l'input depuis les données du service
            input_value = call.data.get("input")
            
            # Si c'est une string, essayer de trouver le numéro correspondant
            if isinstance(input_value, str):
                # Chercher dans les inputs disponibles
                if coordinator.data and "available_inputs" in coordinator.data:
                    for num, name in coordinator.data["available_inputs"].items():
                        if name == input_value:
                            input_value = num
                            break
                else:
                    # Essayer de parser comme un nombre
                    try:
                        input_value = int(input_value)
                    except ValueError:
                        _LOGGER.error(f"Invalid input value: {input_value}")
                        return
            
            if coordinator.switcher.connected:
                await hass.async_add_executor_job(
                    coordinator.switcher.setProgramInputVideoSource,
                    0,  # M/E index
                    input_value
                )
                await coordinator.async_request_refresh()
                _LOGGER.info(f"Program input set to: {input_value}")
            else:
                _LOGGER.error("Cannot set program input: ATEM not connected")
        except Exception as e:
            _LOGGER.error(f"Error setting program input: {e}")
    
    async def handle_set_preview_input(call: ServiceCall) -> None:
        """Gère le service set_preview_input."""
        try:
            coordinator = await get_coordinator()
            
            # Récupérer l'input depuis les données du service
            input_value = call.data.get("input")
            
            # Si c'est une string, essayer de trouver le numéro correspondant
            if isinstance(input_value, str):
                # Chercher dans les inputs disponibles
                if coordinator.data and "available_inputs" in coordinator.data:
                    for num, name in coordinator.data["available_inputs"].items():
                        if name == input_value:
                            input_value = num
                            break
                else:
                    # Essayer de parser comme un nombre
                    try:
                        input_value = int(input_value)
                    except ValueError:
                        _LOGGER.error(f"Invalid input value: {input_value}")
                        return
            
            if coordinator.switcher.connected:
                await hass.async_add_executor_job(
                    coordinator.switcher.setPreviewInputVideoSource,
                    0,  # M/E index
                    input_value
                )
                await coordinator.async_request_refresh()
                _LOGGER.info(f"Preview input set to: {input_value}")
            else:
                _LOGGER.error("Cannot set preview input: ATEM not connected")
        except Exception as e:
            _LOGGER.error(f"Error setting preview input: {e}")
    
    async def handle_auto_transition(call: ServiceCall) -> None:
        """Gère le service auto_transition."""
        try:
            coordinator = await get_coordinator()
            if coordinator.switcher.connected:
                await hass.async_add_executor_job(
                    coordinator.switcher.execAutoME,
                    0  # M/E index
                )
                await coordinator.async_request_refresh()
                _LOGGER.info("Auto transition performed successfully")
            else:
                _LOGGER.error("Cannot perform auto transition: ATEM not connected")
        except Exception as e:
            _LOGGER.error(f"Error performing auto transition: {e}")
    
    # Enregistrer les services
    hass.services.async_register(
        DOMAIN, 
        "perform_cut", 
        handle_perform_cut,
        schema=vol.Schema({})
    )
    
    # Service avec paramètre input (nombre ou string)
    hass.services.async_register(
        DOMAIN,
        "set_program_input",
        handle_set_program_input,
        schema=vol.Schema({
            vol.Required("input"): cv.string
        })
    )
    
    hass.services.async_register(
        DOMAIN,
        "set_preview_input",
        handle_set_preview_input,
        schema=vol.Schema({
            vol.Required("input"): cv.string
        })
    )
    
    hass.services.async_register(
        DOMAIN,
        "auto_transition",
        handle_auto_transition,
        schema=vol.Schema({})
    )
    
    _LOGGER.info("ATEM services registered successfully")