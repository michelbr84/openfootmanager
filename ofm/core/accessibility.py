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

"""Accessibility helpers for the Openfoot Manager UI.

Provides color-blind friendly themes, scalable UI calculations, and
keyboard navigation shortcut definitions. These are data-layer helpers
that the tkinter/ttkbootstrap UI consumes.
"""


# ---------------------------------------------------------------------------
# Color-blind friendly themes
# ---------------------------------------------------------------------------
# Each theme is a ttkbootstrap-compatible color dict that replaces the
# default palette with colors distinguishable under the given condition.
# Keys follow ttkbootstrap's color naming: primary, secondary, success,
# info, warning, danger, light, dark, bg, fg, selectbg, selectfg,
# inputbg, inputfg, border.

THEMES: dict[str, dict[str, str]] = {
    "protanopia": {
        # Red-blind: avoids red, uses blue/yellow contrast
        "primary": "#0077BB",
        "secondary": "#555555",
        "success": "#009988",
        "info": "#33BBEE",
        "warning": "#EE7733",
        "danger": "#CC3311",
        "light": "#F0F0F0",
        "dark": "#1A1A1A",
        "bg": "#FFFFFF",
        "fg": "#1A1A1A",
        "selectbg": "#0077BB",
        "selectfg": "#FFFFFF",
        "inputbg": "#FFFFFF",
        "inputfg": "#1A1A1A",
        "border": "#AAAAAA",
    },
    "deuteranopia": {
        # Green-blind: avoids green, uses blue/orange contrast
        "primary": "#004488",
        "secondary": "#666666",
        "success": "#DDAA33",
        "info": "#66CCEE",
        "warning": "#EE6677",
        "danger": "#AA3377",
        "light": "#F5F5F5",
        "dark": "#1A1A1A",
        "bg": "#FFFFFF",
        "fg": "#1A1A1A",
        "selectbg": "#004488",
        "selectfg": "#FFFFFF",
        "inputbg": "#FFFFFF",
        "inputfg": "#1A1A1A",
        "border": "#AAAAAA",
    },
    "tritanopia": {
        # Blue-blind: avoids blue, uses red/green contrast
        "primary": "#CC6677",
        "secondary": "#555555",
        "success": "#117733",
        "info": "#999933",
        "warning": "#CC6677",
        "danger": "#882255",
        "light": "#F0F0F0",
        "dark": "#1A1A1A",
        "bg": "#FFFFFF",
        "fg": "#1A1A1A",
        "selectbg": "#CC6677",
        "selectfg": "#FFFFFF",
        "inputbg": "#FFFFFF",
        "inputfg": "#1A1A1A",
        "border": "#AAAAAA",
    },
}


# ---------------------------------------------------------------------------
# Scalable UI calculations
# ---------------------------------------------------------------------------

class ScalableUI:
    """Provides scaling calculations for responsive UI layout.

    All methods are pure functions that compute values based on screen
    dimensions -- they do not interact with any UI toolkit directly.
    """

    # Reference resolution the UI was designed for
    BASE_WIDTH = 1920
    BASE_HEIGHT = 1080
    BASE_FONT_SIZE = 12

    # Minimum and maximum scale factors to keep the UI usable
    MIN_SCALE = 0.6
    MAX_SCALE = 2.5

    @classmethod
    def calculate_scale_factor(cls, screen_width: int, screen_height: int) -> float:
        """Calculate a scale factor relative to the base resolution.

        The factor is the geometric mean of the width and height ratios,
        clamped to a reasonable range.

        Args:
            screen_width: Current screen width in pixels.
            screen_height: Current screen height in pixels.

        Returns:
            A float scale factor (1.0 = base resolution).
        """
        w_ratio = screen_width / cls.BASE_WIDTH
        h_ratio = screen_height / cls.BASE_HEIGHT
        factor = (w_ratio * h_ratio) ** 0.5
        return max(cls.MIN_SCALE, min(cls.MAX_SCALE, round(factor, 3)))

    @classmethod
    def scale_font_size(cls, base_size: int, factor: float) -> int:
        """Scale a font size by the given factor.

        The result is always at least 8 to keep text readable.

        Args:
            base_size: The font size at 1.0 scale.
            factor: The scale factor from calculate_scale_factor().

        Returns:
            Scaled font size as an integer (minimum 8).
        """
        return max(8, round(base_size * factor))

    @classmethod
    def get_responsive_geometry(
        cls,
        screen_w: int,
        screen_h: int,
    ) -> tuple[int, int]:
        """Calculate the recommended application window size.

        The window fills 85% of the screen in each dimension, with a
        minimum of 800x600.

        Args:
            screen_w: Screen width in pixels.
            screen_h: Screen height in pixels.

        Returns:
            Tuple of (width, height) for the application window.
        """
        width = max(800, int(screen_w * 0.85))
        height = max(600, int(screen_h * 0.85))
        return width, height


# ---------------------------------------------------------------------------
# Keyboard navigation
# ---------------------------------------------------------------------------

class KeyboardNavigation:
    """Defines and manages keyboard shortcut mappings for the application.

    Shortcuts are stored as a dict mapping key-combo strings (e.g.
    "Ctrl+S") to action identifiers (e.g. "save_game"). The UI layer
    binds these combos to the corresponding callbacks.
    """

    SHORTCUTS: dict[str, str] = {
        "Ctrl+S": "save_game",
        "Ctrl+N": "new_game",
        "Ctrl+O": "load_game",
        "Ctrl+Q": "quit",
        "F5": "advance_day",
        "F6": "advance_week",
        "Ctrl+T": "training",
        "Ctrl+F": "formation",
        "Ctrl+M": "market",
        "Ctrl+L": "league_table",
        "Ctrl+P": "squad",
        "Ctrl+I": "inbox",
        "Ctrl+D": "dashboard",
        "Ctrl+H": "match_history",
        "Ctrl+E": "tactics",
        "Escape": "back",
        "F1": "help",
        "F11": "fullscreen_toggle",
    }

    @classmethod
    def get_shortcut(cls, action: str) -> str:
        """Look up the key combo for a given action.

        Args:
            action: The action identifier (e.g. "save_game").

        Returns:
            The key combo string (e.g. "Ctrl+S"), or an empty string if
            the action has no shortcut.
        """
        for combo, act in cls.SHORTCUTS.items():
            if act == action:
                return combo
        return ""

    @classmethod
    def get_all_shortcuts(cls) -> dict[str, str]:
        """Get a copy of the full shortcut mapping.

        Returns:
            Dict mapping key combos to action identifiers.
        """
        return dict(cls.SHORTCUTS)

    @classmethod
    def get_help_text(cls) -> str:
        """Generate a human-readable formatted list of all shortcuts.

        Returns:
            Multi-line string with each shortcut on its own line,
            formatted as "Key Combo  -  Action Description".
        """
        lines = ["Keyboard Shortcuts", "=" * 40]

        # Group shortcuts by category for readability
        categories = {
            "General": ["save_game", "new_game", "load_game", "quit", "help", "back", "fullscreen_toggle"],
            "Navigation": ["dashboard", "squad", "formation", "training", "market", "league_table", "inbox", "match_history", "tactics"],
            "Game Flow": ["advance_day", "advance_week"],
        }

        action_to_combo = {act: combo for combo, act in cls.SHORTCUTS.items()}

        for category, actions in categories.items():
            lines.append("")
            lines.append(f"  {category}")
            lines.append("  " + "-" * 38)
            for action in actions:
                combo = action_to_combo.get(action, "")
                if combo:
                    label = action.replace("_", " ").title()
                    lines.append(f"  {combo:<16} {label}")

        # Include any shortcuts not captured in the categories above
        categorized_actions = set()
        for actions in categories.values():
            categorized_actions.update(actions)

        uncategorized = [
            (combo, act) for combo, act in cls.SHORTCUTS.items()
            if act not in categorized_actions
        ]
        if uncategorized:
            lines.append("")
            lines.append("  Other")
            lines.append("  " + "-" * 38)
            for combo, action in uncategorized:
                label = action.replace("_", " ").title()
                lines.append(f"  {combo:<16} {label}")

        return "\n".join(lines)
