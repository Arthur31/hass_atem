import logging
import voluptuous as vol
from homeassistant import config_entries
import PyATEMMax
import subprocess  # Pour la récupération de l'adresse MAC

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class CannotConnect(Exception):
    """Erreur pour indiquer que la connexion a échoué."""

class AtemSwitcherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Gère le flux initié par l'utilisateur."""
        errors = {}

        if user_input is not None:
            try:
                # Tente de valider la connexion avec l'appareil
                # On passe la FONCTION et ses ARGUMENTS à l'executor
                await self.hass.async_add_executor_job(
                    self._validate_connection, user_input["host"]
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as ex:
                _LOGGER.exception("Une erreur inconnue est survenue: %s", ex)
                errors["base"] = "unknown"
            else:
                # La connexion est réussie, on peut continuer
                # NOTE: La récupération de l'adresse MAC est complexe et dépend de l'OS.
                # Pour l'instant, nous utiliserons l'adresse IP comme identifiant unique
                # pour simplifier, même si ce n'est pas l'idéal.
                unique_id = user_input["host"]
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input["host"],
                    data=user_input,
                )

        # Affiche le formulaire initial ou le ré-affiche avec les erreurs
        data_schema = vol.Schema({
            vol.Required("host", default=user_input.get("host", "") if user_input else ""): str,
        })
        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    def _validate_connection(self, host: str) -> None:
        """Valide que nous pouvons nous connecter à l'ATEM.
           Cette fonction est conçue pour être exécutée dans un thread executor.
        """
        _LOGGER.info("Validation de la connexion à l'ATEM sur %s", host)
        switcher = PyATEMMax.ATEMMax()
        try:
            switcher.connect(host)
            # On attend la connexion pendant 2 secondes maximum
            if not switcher.waitForConnection(timeout=15):
                _LOGGER.error("Timeout lors de la connexion à l'ATEM.")
                raise CannotConnect
            
            _LOGGER.info("Connexion à l'ATEM réussie. Modèle: %s", switcher.atemModel)

        except Exception as e:
            _LOGGER.error("Échec de la connexion à l'ATEM: %s", e)
            raise CannotConnect from e
        finally:
            # Il est crucial de se déconnecter après la validation
            if switcher.connected:
                switcher.disconnect()
                _LOGGER.info("Déconnecté de l'ATEM après validation.")

    # La fonction _get_mac_address est complexe à implémenter de manière multi-plateforme.
    # Nous la laissons de côté pour le moment pour nous concentrer sur la logique principale.
    
    
    
# import logging
# import voluptuous as vol
# from homeassistant import config_entries
# import PyATEMMax
# import subprocess

# from .const import DOMAIN

# _LOGGER = logging.getLogger(__name__)

# class CannotConnect(Exception):
#     """Erreur pour indiquer que la connexion a échoué."""

# class AtemSwitcherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
#     VERSION = 1

#     async def async_step_user(self, user_input=None):
#         """Gère le flux initié par l'utilisateur."""
#         errors = {}

#         if user_input is None:
#             # Affiche le formulaire initial
#             data_schema = vol.Schema({
#                 vol.Required("host"): str,
#             })
#             return self.async_show_form(
#                 step_id="user", data_schema=data_schema, errors=errors
#             )
        
#         if user_input is not None:
#             _LOGGER.info("user_input is not None ")
#             _LOGGER.error("user_input is not None ")
#             try:
#                 # Tente de valider la connexion avec l'appareil
#                 # C'est une opération bloquante, donc elle doit être exécutée dans l'executor
#                 # await self.hass.async_add_executor_job(
#                 #     self._validate_connection(user_input["host"])
#                 # )
#                 await self.hass.async_add_executor_job(self._validate_connection, user_input["host"])
#             except CannotConnect:
#                 errors["base"] = "cannot_connect"
#             except Exception as ex:
#                 _LOGGER.exception("An error occurred in the main loop: %s", ex)
#                 errors["base"] = "unknown"
#             else:
#                 # La connexion est réussie, obtenir l'adresse MAC pour l'unique_id
#                 mac_address = await self.hass.async_add_executor_job(
#                     self._get_mac_address, user_input["host"]
#                 )

#                 if not mac_address:
#                     errors["base"] = "cannot_get_mac"
#                 else:
#                     await self.async_set_unique_id(mac_address)
#                     self._abort_if_unique_id_configured()

#                     return self.async_create_entry(
#                         title=user_input["host"],
#                         data=user_input,
#                     )
        
#         # Ré-affiche le formulaire avec les erreurs si nécessaire
#         data_schema = vol.Schema({
#             vol.Required("host", default=user_input.get("host", "")): str,
#         })
#         return self.async_show_form(
#             step_id="user", data_schema=data_schema, errors=errors
#         )

#     def _validate_connection(self, host: str) -> None:
#         """Valide que nous pouvons nous connecter à l'ATEM.
#            Cette fonction est conçue pour être exécutée dans un thread executor.
#         """
#         _LOGGER.info("Validation de la connexion à l'ATEM sur %s", host)
#         switcher = PyATEMMax.ATEMMax()
#         try:
#             switcher.connect(host)
#             # On attend la connexion pendant 2 secondes maximum
#             if not switcher.waitForConnection(timeout=2):
#                 _LOGGER.error("Timeout lors de la connexion à l'ATEM.")
#                 raise CannotConnect
            
#             _LOGGER.info("Connexion à l'ATEM réussie. Modèle: %s", switcher.atemModel)

#         except Exception as e:
#             _LOGGER.error("Échec de la connexion à l'ATEM: %s", e)
#             raise CannotConnect from e
#         finally:
#             # Il est crucial de se déconnecter après la validation
#             if switcher.connected:
#                 switcher.disconnect()
#                 _LOGGER.info("Déconnecté de l'ATEM après validation.")

#     # La fonction _get_mac_address est complexe à implémenter de manière multi-plateforme.
#     # Nous la laissons de côté pour le moment pour nous concentrer sur la logique principale.


#     # # Méthode d'aide pour le code bloquant
#     # def _validate_connection(self, host):
#     #     """Valide que nous pouvons nous connecter à l'ATEM."""
#     #     _LOGGER.info("_validate_connection")
#     #     # Ici, on utiliserait PyATEMMax pour se connecter.
#     #     # Si la connexion échoue, la bibliothèque lèvera une exception.
#     #     # Pour cet exemple, nous simulons une vérification.
#     #     import PyATEMMax
#     #     switcher = PyATEMMax.ATEMMax()
#     #     switcher.connect(host)
#     #     maxRetry = 0
#     #     while (maxRetry < 10) :
#     #         _LOGGER.info("rety: %s", maxRetry)
#     #         maxRetry = maxRetry + 1
#     #         if switcher.connected: # Timeout de 2 secondes
#     #             switcher.disconnect()
#     #             pass # Simule une connexion réussie
#     #         # raise CannotConnect
#     #         await asyncio.sleep(2)
#     #     raise CannotConnect
