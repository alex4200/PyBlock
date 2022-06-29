"""Example: Manipulating blocks.

This example shows how to read blocks from the world and how to set blocks.
"""

import pyblock


# Set your path to the minecraft world
PATH = "path/to//minecraft/saves/YourWorld"
PATH = "/Users/adietz/Library/Application Support/minecraft/saves/TestWorld"

# Create the editor
editor = pyblock.Editor(PATH)
editor.set_verbosity(2)

# Define an example block
diamond = pyblock.Block("diamond_block")

# Read blocks
x = 50
z = 50
for y in range(-64, 60):
	block = editor.get_block(x, y, z)
	print(f"Block at {x}/{y}/{z} is {block}")

# Set blocks in form of a cross
y = 100
for index in range(20):
	editor.set_block(diamond, x+index, y, z)
	editor.set_block(diamond, x-index, y, z)
	editor.set_block(diamond, x, y+index, z)
	editor.set_block(diamond, x, y-index, z)
	editor.set_block(diamond, x, y, z+index)
	editor.set_block(diamond, x, y, z-index)

# write the data to file
editor.done()