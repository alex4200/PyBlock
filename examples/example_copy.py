"""Example: Copying areas of blocks.

This example shows how to copy a 3-dimensional area to another place.
It also shows how to repeadedly copy the same area 5 times.
"""

import json

import pyblock


# Set your path to the minecraft world
PATH = "path/to//minecraft/saves/YourWorld"

# Create the editor
editor = pyblock.Editor(PATH)
editor.set_verbosity(2)

# Define the lower edge of the source area
source = (49, 61, 30)

# Define the lower edge of the destination area
dest = (49, 64, 30)

# Define the 3-dimensional size to be copied
size = (5, 3, 5)

# In this example the source is copied 5 times in vertical direction
# with an interval of 3 blocks.
# Can be used to create a tall house from a template.
# To copy an area only once just use 'editor.copy_blocks(source, dest, size)'
rep = []
for r in range(5):
    rep.append((0, r * 3, 0))
editor.copy_blocks(source, dest, size, rep)

# This code snippet looks at the entities (sign entities) to set the sign content
# (In case you want to create a tall house which has signs)
for key, entities in editor.entities.items():
    for entity in entities:
        etage = (entity["y"].value - 65) / 3 + 1
        entity["Text1"].value = json.dumps({"text": f"Etage {etage:.0f}"})
        print(entity["Text1"].value)

# Finally, write the changes to files
editor.done()
