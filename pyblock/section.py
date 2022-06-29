#!/usr/bin/env python3
"""Defines a minecraft section."""
__author__ = "Alexander Dietz"
__license__ = "MIT"
# pylint: disable=C0103,W1202,E1120,R0913,R0914,E0401,W1203,R1732,W1514,R0912,R0903,R0902,R0911,W1201

import array
from struct import Struct

from nbt import nbt
import pyblock


# dirty mixin to change q to Q
# This is important as the "Long_Array" in nbt uses "q" (signed long long)
# instead of "Q" (unsigned long long).
# see also https://docs.python.org/3.8/library/array.html
def _update_fmt(self, length):
    self.fmt = Struct(f'>{length}Q')
nbt.TAG_Long_Array.update_fmt = _update_fmt


class Section:
    """
    Defines a section.

    This is where the blocks are actually stored, in a 16³ sized array.
    To save up some space, `None` is used instead of the air block object,
    and will be replaced with `self.air` when needed

    Args:
        y (int): The y index of the section
        air (Block): An air block
        section (nbt.TAG_Compound): A section in nbt format
    """

    def __init__(self, ylevel: int, nbt_section: nbt.TAG_Compound):
        """Initializes the empty section.

        Args:
            y: The y level of the section
        """
        # Stores the ylevel (not actually used internally)
        self.ylevel = ylevel

        # Block that will be used when None
        self.air = pyblock.Block("air")

        # The section in NBT format
        self.nbt_section = nbt_section

        # Read the blocks from this section
        self.read_blocks()

    def read_blocks(self):
        """
        Returns the list of all Blocks in the current section.
        """
        #states = self.section["block_states"]
        palette = self.nbt_section["block_states"]["palette"]
        #map_palette = [p["Name"].value for p in palette]

        # The whole section consists of one block only
        if len(palette) == 1:
            block = pyblock.Block(compound=palette[0])
            self.blocks = [block] * 4096
            return

        # Get the actual data
        index = 0
        datas = self.nbt_section["block_states"]["data"]

        # Number of bits required to describe the content in a 16x16x16 section.
        # This is the bit length of the different items beloning to this section, 4 minimum.
        bits = max((len(palette) - 1).bit_length(), 4)

        # The bit mask to extract the values for the blocks from the binary data
        bits_mask = 2 ** bits - 1

        # We start at index 0 all the time, so state is always equal to zero
        state = 0

        # Each item in 'data' is 64 bits long, as it is a LONG
        data_len = 64

        # Get the first LONG data piece
        data = datas[0]

        # Prepare the empty list of all blocks
        self.blocks = []
        while index < 4096:
            # Check the data length. If it is less than the bits, then use the next LONG
            if data_len < bits:

                # Take the next LONG value as the new data value
                state += 1
                new_data = datas[state]
                if new_data < 0:
                    new_data += 2 ** 64
                data = new_data
                data_len = 64

            # Get the ID for the next block by ANDing the data and the bit mask
            palette_id = data & bits_mask

            # Add the block to the list
            self.blocks.append(pyblock.Block(compound=palette[palette_id]))

            # Increase the index
            index += 1

            # Move the data by the given bits, and update the remaining data length
            data >>= bits
            data_len -= bits

    def get_block(self, index: int) -> pyblock.Block:
        """Returns the block at the given index.

        Args:
            index: Index of the block inside the section.
        """
        return self.blocks[index] or self.air

    def set_block(self, block: pyblock.Block, index: int):
        """
        Sets the block at given section index.

        Args:
            block: Block to set
            index: Index of the block inside the section.
        """
        #print(f"Setting {index} to {block}")
        self.blocks[index] = block

    #@staticmethod
    def get_palette(self) -> nbt.TAG_Compound:
        """
        Generates and returns the nbt palette. Required for 'blockstates' and the complete NBT.
        """
        # Create a set of sorted unique Blocks
        palette = list(set(self.blocks))
        palette.sort(key=lambda x: x.__repr__())

        # Create the new palette
        new_palette = nbt.TAG_List(name="palette", type=nbt.TAG_Compound)

        # Add all unique blocks to the palette
        for block in palette:
            new_palette.tags.append(block.compound)
        return new_palette

    @staticmethod
    def print_palette(palette):
        """Only for debugging: Prints out the content of a 'palette'."""
        for index, entry in enumerate(palette):
            name = entry.id
            props = ""
            for k,v in entry.properties.items():
                props += f"  {k}={v}"
            print(f"  {index:02d}: {name:30s}  {props}")

    #@staticmethod
    def blockstates(self, nbt_palette: nbt.TAG_Compound) -> array.array:
        """
        Returns a list of each block's index in the palette.
        This is used in the BlockStates tag of the section.

        Args:
            nbt_palette: The nbt palette to use to index the blocks
        """
        # Extract the list of blocks from the palette
        palette = [pyblock.Block(compound=entry) for entry in nbt_palette]
        #self.print_palette(palette)

        # Get the number of bits from the size of the palette.
        # min is 4 bits, max is the number of bits required to represent the length of the palette
        bits = max((len(palette) - 1).bit_length(), 4)

        # Prepare the array of unsigned long long
        # see https://docs.python.org/3.8/library/array.html
        states = array.array("Q")

        def bin_append(a, b, length):
            """Helper function used in `blockstates`."""
            return (a << length) | b

        # Start constructing the bitmap
        current = 0
        current_len = 0
        for block in self.blocks:
            index = palette.index(block)

            # If it's more than 64 bits then add current value to list
            # and begin a new value. No bit overflow.
            if current_len + bits > 64:
                # add value to byte
                states.append(current)

                current = 0
                current_len = 0

                current = bin_append(index, current, length=current_len)
                current_len += bits
            else:
                current = bin_append(index, current, length=current_len)
                current_len += bits
        states.append(current)
        return states

    def get_nbt(self) -> nbt.TAG_Compound:
        """Returns the nbt tag of this section."""
        # # Need to recreate section "ylevel" and replace this section in this chunk
        #     # Get the current section and define a Section with it
        #     section = self.sections[y]
        #     mysection = pyblock.Section(y, section)

            # # Just a check
            # assert y == section["Y"].value

        # Read the biomes information
        biomes = self.nbt_section["biomes"]

        # Read the list of blocks (4096 for a section)
        #blocks = mysection.list_blocks()

        # Set the new blocks
        #for index, newblock in newblocks:
        #    #print(f"{index=}   block={newblock}")
        #    blocks[index] = newblock

        # Get the new palette and the new data (i.e. blockstates)
        new_palette = self.get_palette()
        #self.print_palette(new_palette)
        new_data = self.blockstates(new_palette)

        # Create a new nbt section
        new_section = nbt.TAG_Compound()

        # Add the y level to the section and the biomes (both unchanged)
        new_section.tags.append(nbt.TAG_Byte(name="Y", value=self.ylevel))
        new_section.tags.append(biomes)

        # Create the block_states compound
        new_block_states = nbt.TAG_Compound(name="block_states")

        # Add the palette to the block states
        new_block_states.tags.append(new_palette)

        # store the data to the block_states
        if len(new_palette) > 1:
            nbt_data = nbt.TAG_Long_Array(name="data")
            nbt_data.value = new_data  # copy data for now
            new_block_states.tags.append(nbt_data)

        # Add the block states to the section
        new_section.tags.append(new_block_states)

        return new_section

        ## Replace with new section
        #self.sections[y] = new_section
