#      Openfoot Manager - A free and open source soccer management simulation
#      Copyright (C) 2020-2025  Pedrenrique G. Guimarães
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
Localization framework for OpenFoot Manager.

Provides a ``LocaleManager`` that resolves string keys to translated text,
with fallback to English when a key is missing in the active locale.
"""
import json
from pathlib import Path

# Default English strings
DEFAULT_LOCALE = "en"

STRINGS = {
    "en": {
        "app_title": "OpenFoot Manager",
        "new_game": "New Game",
        "load_game": "Load Game",
        "save_game": "Save Game",
        "settings": "Settings",
        "debug_mode": "Debug Mode",
        "back": "Back",
        "cancel": "Cancel",
        "apply": "Apply",
        "save": "Save",
        "formation": "Formation",
        "training": "Training",
        "finances": "Finances",
        "transfers": "Transfer Market",
        "league": "League Table",
        "championship": "Championship",
        "stats": "Stats Explorer",
        "player_profile": "Player Profile",
        "team_explorer": "Team Explorer",
        "match_sim": "Match Simulation",
        "visualizer": "Match Visualizer",
        "edit": "Edit",
        "team_formation": "Team Formation",
        "youth_academy": "Youth Academy",
        "press_conference": "Press Conference",
        # Match commentary
        "goal": "GOAL!",
        "yellow_card": "Yellow Card",
        "red_card": "Red Card",
        "substitution": "Substitution",
        "half_time": "Half Time",
        "full_time": "Full Time",
        # Dashboard
        "upcoming_fixtures": "Upcoming Fixtures",
        "recent_results": "Recent Results",
        "league_position": "League Position",
        "balance": "Balance",
    },
    "pt-BR": {
        "app_title": "OpenFoot Manager",
        "new_game": "Novo Jogo",
        "load_game": "Carregar Jogo",
        "save_game": "Salvar Jogo",
        "settings": "Configurações",
        "debug_mode": "Modo Debug",
        "back": "Voltar",
        "cancel": "Cancelar",
        "apply": "Aplicar",
        "save": "Salvar",
        "formation": "Formação",
        "training": "Treinamento",
        "finances": "Finanças",
        "transfers": "Mercado de Transferências",
        "league": "Tabela do Campeonato",
        "championship": "Campeonato",
        "stats": "Explorador de Estatísticas",
        "player_profile": "Perfil do Jogador",
        "team_explorer": "Explorador de Times",
        "match_sim": "Simulação de Partida",
        "visualizer": "Visualizador de Partida",
        "edit": "Editar",
        "team_formation": "Formação do Time",
        "youth_academy": "Base",
        "press_conference": "Coletiva de Imprensa",
        "goal": "GOL!",
        "yellow_card": "Cartão Amarelo",
        "red_card": "Cartão Vermelho",
        "substitution": "Substituição",
        "half_time": "Intervalo",
        "full_time": "Fim de Jogo",
        "upcoming_fixtures": "Próximos Jogos",
        "recent_results": "Resultados Recentes",
        "league_position": "Posição no Campeonato",
        "balance": "Saldo",
    },
    "es": {
        "app_title": "OpenFoot Manager",
        "new_game": "Nuevo Juego",
        "load_game": "Cargar Juego",
        "save_game": "Guardar Juego",
        "settings": "Configuración",
        "debug_mode": "Modo Depuración",
        "back": "Volver",
        "cancel": "Cancelar",
        "apply": "Aplicar",
        "save": "Guardar",
        "formation": "Formación",
        "training": "Entrenamiento",
        "finances": "Finanzas",
        "transfers": "Mercado de Fichajes",
        "league": "Tabla de Liga",
        "championship": "Campeonato",
        "stats": "Explorador de Estadísticas",
        "player_profile": "Perfil del Jugador",
        "team_explorer": "Explorador de Equipos",
        "match_sim": "Simulación de Partido",
        "visualizer": "Visualizador de Partido",
        "edit": "Editar",
        "team_formation": "Formación del Equipo",
        "youth_academy": "Cantera",
        "press_conference": "Rueda de Prensa",
        "goal": "¡GOL!",
        "yellow_card": "Tarjeta Amarilla",
        "red_card": "Tarjeta Roja",
        "substitution": "Sustitución",
        "half_time": "Descanso",
        "full_time": "Final del Partido",
        "upcoming_fixtures": "Próximos Partidos",
        "recent_results": "Resultados Recientes",
        "league_position": "Posición en Liga",
        "balance": "Saldo",
    },
}


class LocaleManager:
    """Manages locale selection and string resolution with English fallback."""

    def __init__(self, locale: str = DEFAULT_LOCALE):
        self.current_locale: str = locale
        self.custom_strings: dict = {}

    def set_locale(self, locale: str) -> None:
        """Change the active locale.

        Raises ``ValueError`` if the locale is not available in either
        the built-in ``STRINGS`` dict or ``custom_strings``.
        """
        if locale not in STRINGS and locale not in self.custom_strings:
            raise ValueError(
                f"Locale '{locale}' is not available. "
                f"Available: {self.get_available_locales()}"
            )
        self.current_locale = locale

    def get(self, key: str) -> str:
        """Return the translated string for *key* in the current locale.

        Resolution order:
        1. Custom strings for the current locale.
        2. Built-in strings for the current locale.
        3. Built-in English strings (fallback).
        4. The raw key itself if nothing is found.
        """
        # Try custom strings first
        custom_locale = self.custom_strings.get(self.current_locale, {})
        if key in custom_locale:
            return custom_locale[key]

        # Try built-in strings for the current locale
        builtin_locale = STRINGS.get(self.current_locale, {})
        if key in builtin_locale:
            return builtin_locale[key]

        # Fallback to English
        english = STRINGS.get(DEFAULT_LOCALE, {})
        if key in english:
            return english[key]

        # Last resort: return the key itself
        return key

    def get_available_locales(self) -> list[str]:
        """Return a sorted list of all available locale codes."""
        locales = set(STRINGS.keys())
        locales.update(self.custom_strings.keys())
        return sorted(locales)

    def load_custom_locale(self, path: Path) -> None:
        """Load a custom locale from a JSON file.

        The JSON file should have the structure::

            {
                "locale": "fr",
                "strings": {
                    "app_title": "OpenFoot Manager",
                    "new_game": "Nouvelle Partie",
                    ...
                }
            }

        The loaded strings are merged into ``custom_strings`` under the
        locale code found in the file.
        """
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        locale_code = data.get("locale", "custom")
        strings = data.get("strings", {})
        self.custom_strings[locale_code] = strings

    def export_locale_template(self, path: Path) -> None:
        """Export the English string table as a JSON template.

        This gives translators a starting point: they fill in their own
        translations and change the ``"locale"`` field.
        """
        template = {
            "locale": "xx",
            "strings": dict(STRINGS[DEFAULT_LOCALE]),
        }
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(template, fp, indent=2, ensure_ascii=False)
