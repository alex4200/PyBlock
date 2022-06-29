#!/usr/bin/env python3
"""Defines a minecraft chunk."""
__author__ = "Alexander Dietz"
__license__ = "MIT"
# pylint: disable=C0103,W1202,E1120,R0913,R0914,E0401

import zlib
from io import BytesIO

from nbt import nbt

import pyblock
from .tools import MIN_SECTION, MAX_SECTION


class Chunk:
    """
    Defines a Minecraft chunk.
    """

    def __init__(self, nbt_data: nbt.NBTFile):
        """Creates a chunk object.

        Args:
            nbt_data: NBT data file
        """
        self.nbt_data = nbt_data
        self.version = nbt_data["DataVersion"].value
        self.sections = {}
        self.x = nbt_data["xPos"].value
        self.z = nbt_data["zPos"].value

        # extract the secions by y value
        for section in nbt_data["sections"]:
            if section:
                y = section["Y"].value
                self.sections[y] = section

    def get_section(self, y: int) -> nbt.TAG_Compound:
        """
        Returns the section at given y index.

        Args:
            y: Index for the y-coordinate of the section

        Raises:
            anvil.OutOfBoundsCoordinates if y outside of allowed range.
        """
        if y < MIN_SECTION or y > MAX_SECTION:
            raise pyblock.OutOfBoundsCoordinates(
                f"Y ({y!r}) must be in range {MIN_SECTION} to {MAX_SECTION}"
            )
        return pyblock.Section(y, self.sections[y])
        #return self.sections[y]

    # NEW
    def set_section(self, ylevel: int, section: nbt.TAG_Compound):
        """Sets a new section at the given y level.

        Args:
            ylevel: ylevel of the section
            section: the new section
        """
        self.sections[ylevel] = section

    @staticmethod
    def print_palette(palette):
        """Only for debugging: Prints out the content of a 'palette'."""
        for index, entry in enumerate(palette):
            name = entry["Name"].value
            props = ""
            if "Properties" in entry:
                for k,v in entry["Properties"].items():
                    props += f"  {k}={v}"
            print(f"  {index:02d}: {name:30s}  {props}")



    def get_nbt(self, entities_to_update) -> nbt.NBTFile:
        """
        Converts the chunk data to `NBTFile` format. Copies all non-section data.
        """
        # Create the root NBT object with all other information
        root = nbt.NBTFile()
        root.tags.extend(
            [
                nbt.TAG_Int(name="DataVersion", value=self.version),
                nbt.TAG_Int(name="xPos", value=self.x),
                nbt.TAG_Int(name="zPos", value=self.z),
                nbt.TAG_String(name="Status", value="full"),
                self.nbt_data["LastUpdate"],
                self.nbt_data["Heightmaps"],
                self.nbt_data["fluid_ticks"],
                self.nbt_data["block_ticks"],
                self.nbt_data["InhabitedTime"],
                self.nbt_data["PostProcessing"],
                self.nbt_data["structures"],
            ]
        )

        entities = nbt.TAG_List(name="block_entities", type=nbt.TAG_Compound)
        # Copy existing entities to chunk
        for entity in self.nbt_data["block_entities"]:
            # TODO: overwritten entities in destination area should be removed
            entities.tags.append(entity)
            # Copy new entities to chunk
        for entity in entities_to_update:
            entities.tags.append(entity)
        root.tags.append(entities)

        # Add the sections
        sections = nbt.TAG_List(name="sections", type=nbt.TAG_Compound)
        for section in list(self.sections.values()):
            if section:
                sections.tags.append(section)
        root.tags.append(sections)
        return root

    def get_bytes(self, entities_to_update) -> bytes:
        """New added method to get the actual 4096-sized data bytes to be added.
        Data extracted from the region save method.
        """
        chunk_data = BytesIO()

        # Get the chunk data as NBT data and write it to 'chunk_data'
        nbt_data = self.get_nbt(entities_to_update)
        nbt_data.write_file(buffer=chunk_data)

        # Compress the data
        chunk_data.seek(0)
        chunk_data = zlib.compress(chunk_data.read())

        # Create the byte block
        bytes_data = (len(chunk_data) + 1).to_bytes(4, "big") + b"\x02" + chunk_data

        # Padding to be a multiple of 4KiB long
        bytes_data += bytes(4096 - (len(bytes_data) % 4096))
        assert len(bytes_data) % 4096 == 0

        return bytes_data
