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
start = [995, pyblock.tools.MIN_Y, 995]
end = [1005, pyblock.tools.MAX_Y, 1005]

# Define the block you want to look for
block = pyblock.Block("diamond_ore")

# Get and print the locations of the block in the specified aree
locations = editor.find_blocks(start, end, block)
print(locations)

# You can also specify a block with specific properties
block = pyblock.Block(
    "warped_button", properties={"face": "floor", "facing": "north", "powered": "false"}
)

# Find the locations of the block with the exact same properties
locations = editor.find_blocks(start, end, block, exact=True)
print(f"Exact find name block: {locations}")
