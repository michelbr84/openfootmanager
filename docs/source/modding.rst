Modding Guide
=============

OpenFoot Manager supports mods through the ModLoader framework.

Creating a Mod
--------------

1. Create a folder in ``ofm/mods/`` with your mod name
2. Add a ``mod.json`` file with this structure::

    {
        "name": "My Custom Mod",
        "version": "1.0.0",
        "author": "Your Name",
        "description": "What the mod does",
        "type": "database",
        "data": {
            "clubs": [],
            "players": []
        }
    }

Mod Types
---------

- ``database`` — Add or modify clubs and players
- ``roster`` — Custom squad assignments
- ``tactics`` — Tactical presets
- ``graphics`` — Custom themes

Loading Mods
------------

Access the Community Hub from the main menu, go to the Mods tab,
and click "Load Mod" to apply a discovered mod.

Exporting/Importing
-------------------

Use the Export DB / Import DB buttons in the Community Hub to
share entire database snapshots as JSON files.
