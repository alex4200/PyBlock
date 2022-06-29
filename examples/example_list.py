"""Example: Finding blocks.

This example shows how to copy a 3-dimensional area to another place.
It also shows how to repeadedly copy the same area 5 times.
"""

import pyblock


# Set your path to the minecraft world
PATH = "path/to//minecraft/saves/YourWorld"

# Create the editor
editor = pyblock.Editor(PATH)
editor.set_verbosity(2)

# Define the lower and upper 3-dimensional point for the area to be searched
start = [-5, pyblock.tools.MIN_Y, 0]
end = [20, pyblock.tools.MAX_Y, 20]

# List all the blocks in the specified area
blocks = editor.list_blocks(start, end)
print(blocks)
