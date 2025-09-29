"""ATEM Data Update Coordinator with real-time events - Simplified."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict

import PyATEMMax
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Intervalle de polling de secours
SCAN_INTERVAL = timedelta(seconds=30)


class AtemDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching ATEM data with real-time events."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize ATEM coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.entry = entry
        self.atem_ip = entry.data["host"]
        self.switcher = PyATEMMax.ATEMMax()
        self._event_registered = False
        self._reconnect_task = None
        
    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh and setup event listeners."""
        # Enregistrer les événements avant la première connexion
        await self._async_setup_events()
        
        # Tenter la première connexion
        await self._async_connect()
        
        # Faire la première récupération de données
        await super().async_config_entry_first_refresh()

    async def _async_setup_events(self) -> None:
        """Setup event listeners for real-time updates."""
        if not self._event_registered:
            try:
                # Enregistrer le callback pour les événements
                await self.hass.async_add_executor_job(
                    self.switcher.registerEvent,
                    self.switcher.atem.events.receive,
                    self._on_receive_sync
                )
                self._event_registered = True
                _LOGGER.info("ATEM event listeners registered successfully")
            except Exception as err:
                _LOGGER.error(f"Failed to register ATEM events: {err}")

    def _on_receive_sync(self, params: Dict[Any, Any]) -> None:
        """Sync callback for ATEM events - bridge to async."""
        # Cette fonction est appelée dans un thread, on doit la rendre async-safe
        asyncio.run_coroutine_threadsafe(
            self._on_receive_async(params),
            self.hass.loop
        )

    async def _on_receive_async(self, params: Dict[Any, Any]) -> None:
        """Async handler for ATEM events."""
        try:
            cmd = params.get('cmd')
            
            # Log pour debug
            _LOGGER.debug(f"Received ATEM event: {cmd} - {params.get('cmdName', '')}")
            
            # Mettre à jour les données immédiatement selon l'événement
            update_needed = False
            
            if cmd in ["PrgI", "PrvI", "_ver", "InPr"]:
                update_needed = True
            
            # Si une mise à jour est nécessaire, récupérer les données et notifier
            if update_needed:
                data = await self._async_get_data()
                if data:
                    self.async_set_updated_data(data)
                    
        except Exception as err:
            _LOGGER.error(f"Error handling ATEM event: {err}")

    async def _async_connect(self) -> None:
        """Connect to ATEM switcher."""
        try:
            # Se connecter au switcher
            connected = await self.hass.async_add_executor_job(
                self.switcher.connect,
                self.atem_ip
            )
            
            if not connected:
                # Attendre la connexion
                connected = await self.hass.async_add_executor_job(
                    self.switcher.waitForConnection,
                    5.0,
                    False
                )
            
            if connected:
                _LOGGER.info(f"Connected to ATEM at {self.atem_ip}: {self.switcher.atemModel}")
                # Attendre un peu pour que les données soient disponibles
                await asyncio.sleep(1)
            else:
                raise UpdateFailed(f"Failed to connect to ATEM at {self.atem_ip}")
                
        except Exception as err:
            _LOGGER.error(f"Connection error: {err}")
            raise ConfigEntryNotReady(f"Could not connect to ATEM: {err}")

    async def _async_ensure_connected(self) -> bool:
        """Ensure we're connected to the ATEM."""
        if not self.switcher.connected:
            try:
                await self._async_connect()
            except Exception:
                return False
        return self.switcher.connected

    async def _async_get_data(self) -> dict:
        """Get current data from ATEM - VERSION SIMPLE."""
        try:
            data = {}
            
            if self.switcher.connected:
                # Program input - direct access
                try:
                    program = str(self.switcher.programInput[0].videoSource)
                    data["program"] = program
                    _LOGGER.debug(f"Program: {program}")
                except Exception as e:
                    _LOGGER.error(f"Error reading program: {e}")
                    data["program"] = "Unknown"
                
                # Preview input - direct access
                try:
                    preview = str(self.switcher.previewInput[0].videoSource)
                    data["preview"] = preview
                    _LOGGER.debug(f"Preview: {preview}")
                except Exception as e:
                    _LOGGER.error(f"Error reading preview: {e}")
                    data["preview"] = "Unknown"
            else:
                data["program"] = "Disconnected"
                data["preview"] = "Disconnected"
            
            return data
            
        except Exception as err:
            _LOGGER.error(f"Error getting ATEM data: {err}")
            return {"program": "Error", "preview": "Error"}

    async def _async_update_data(self) -> dict:
        """Update data - called by the polling interval as fallback."""
        # S'assurer qu'on est connecté
        if not await self._async_ensure_connected():
            # Essayer de se reconnecter
            if not self._reconnect_task or self._reconnect_task.done():
                self._reconnect_task = self.hass.async_create_task(
                    self._async_reconnect()
                )
            return {"program": "Disconnected", "preview": "Disconnected"}
        
        # Récupérer les données
        return await self._async_get_data()

    async def _async_reconnect(self) -> None:
        """Background task to reconnect to ATEM."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(5)
                await self._async_connect()
                if self.switcher.connected:
                    _LOGGER.info("Reconnected to ATEM successfully")
                    # Forcer une mise à jour après reconnexion
                    data = await self._async_get_data()
                    if data:
                        self.async_set_updated_data(data)
                    return
            except Exception as err:
                _LOGGER.warning(f"Reconnection attempt {attempt + 1} failed: {err}")
        
        _LOGGER.error("Failed to reconnect to ATEM after multiple attempts")

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and close connections."""
        try:
            # Annuler la tâche de reconnexion si elle existe
            if self._reconnect_task and not self._reconnect_task.done():
                self._reconnect_task.cancel()
            
            # Déconnecter du switcher
            if self.switcher.connected:
                await self.hass.async_add_executor_job(
                    self.switcher.disconnect
                )
            _LOGGER.info("ATEM coordinator shutdown complete")
        except Exception as err:
            _LOGGER.error(f"Error during shutdown: {err}")