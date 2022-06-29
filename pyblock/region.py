#!/usr/bin/env python3
"""Defines a minecraft region."""
__author__ = "Alexander Dietz"
__license__ = "MIT"
# pylint: disable=C0103,W1202,E1120,R0913,R0914,E0401,W1203,R1732,W1514,R0912,R0903,R0902,R0911,W1201


import math
import zlib
from io import BytesIO
import logging

from nbt import nbt

import pyblock
from .tools import CHUNKS_REGION


L = logging.getLogger("pyblock")


class Region:
    """
    Defines a Minecraft region
    """

    def __init__(self, path: str, region_coords: list):
        """Creates a Region object from a region file.

        Args:
            path: Path to the world folder.
            xr, zr: Region coordinates of the region.
        """
        self.path = path
        self.x, self.z = region_coords

        self.x_chunk = self.x * CHUNKS_REGION
        self.z_chunk = self.z * CHUNKS_REGION

        self.filename = str(path) + f"/r.{self.x}.{self.z}.mca"
        with open(self.filename, "rb") as f:
            self.data = f.read()

    def chunk_data(self, chunk_x: int, chunk_z: int) -> nbt.NBTFile:
        """
        Returns the NBT data for the given chunk if it exists.

        Args:
            chunk_x: Chunk's X value
            chunk_z: Chunk's Z value

        Raises
            anvil.GZipChunkData: If the chunk's compression is gzip
        """
        offs = self.chunk_location(chunk_x, chunk_z)
        # (0, 0) means it hasn't generated yet, aka it doesn't exist yet
        if offs == (0, 0):
            L.warning(f"Chunk {chunk_x}/{chunk_z} has not been generated yet.")
            return None

        off = offs[0] * 4096
        length = int.from_bytes(self.data[off : off + 4], byteorder="big")
        compression = self.data[off + 4]  # 2 most of the time
        if compression == 1:
            raise ValueError("GZip is not supported")
        compressed_data = self.data[off + 5 : off + 5 + length - 1]
        return nbt.NBTFile(buffer=BytesIO(zlib.decompress(compressed_data)))

    def read_chunk(self, chunk_coords: list) -> pyblock.Chunk:
        """Reads a chunk at the given coordinates."""
        # Get the data of the chunk at the given coordinates
        try:
            nbt_data = self.chunk_data(*chunk_coords)
        except zlib.error:
            return {}

        # Read the chunk from the nbt data
        return pyblock.Chunk(nbt_data)

    # NEW
    def get_chunk(self, chunk_coord: list) -> pyblock.Chunk:
        """Returns the given chunk from this region.

        Args:
            chunk_coord: relative coordinates of the chunk in this region.
        """
        nbt_data = self.chunk_data(*chunk_coord)
        if nbt_data:
            this_chunk = pyblock.Chunk(nbt_data)
        else:
            raise ValueError("Empty Chunk found, what the hell?")
        return this_chunk

    def write(self, chunks_to_update: dict):
        """Writes the new region to a file.
        Used for editing a chunk

        Args:
            chunks_to_update: Dictionary containing data for chunks to be changed.
        """
        # Create the final data structure for the file
        locations_header = bytes()
        timestamps = bytes(4096)
        chunk_bytes = bytes()

        # An index denoting the location of the current chunk
        sector_offset = 2

        # Loop over all chunks inside the region
        for chunk_z in range(32):
            for chunk_x in range(32):
                chunk_coord = (chunk_x, chunk_z)

                # Get the chunk location
                off, sectors = self.chunk_location(*chunk_coord)

                if chunk_coord in chunks_to_update:
                    # Use updated data (either modified or copied)
                    L.debug(f"Writing modified chunk at {chunk_x}/{chunk_z}")
                    to_add = chunks_to_update[chunk_coord]
                    if to_add != 0:
                        chunk_bytes += to_add
                        sectors = math.ceil(len(to_add) / 4096)
                    else:
                        sectors = 0

                else:
                    # Use existing data without change
                    if (off, sectors) != (0, 0):
                        # Copy the chunk data directly from the data
                        start = off * 4096
                        end = start + sectors * 4096
                        chunk_bytes += self.data[start:end]
                    else:
                        # Chunk does not exist
                        sectors = 0

                # Add the offset to the locations header
                if sectors == 0:
                    locations_header += bytes(4)
                else:
                    locations_header += sector_offset.to_bytes(
                        3, "big"
                    ) + sectors.to_bytes(1, "big")

                # Advance the index by the size of the current chunk
                sector_offset += sectors

        # Combine the final region data before written to file
        final = locations_header + timestamps + chunk_bytes
        assert len(final) % 4096 == 0  # just in case

        # Save to a file
        L.info(f"Writing {self.filename}")
        with open(self.filename, "wb") as f:
            f.write(final)

    @staticmethod
    def header_offset(chunk_x: int, chunk_z: int) -> int:
        """
        Returns the byte offset for the given chunk in the header

        Args:
            chunk_x: Chunk's X value
            chunk_z: Chunk's Z value
        """
        return 4 * (chunk_x % 32 + chunk_z % 32 * 32)

    def chunk_location(self, chunk_x: int, chunk_z: int) -> list:
        """
        Returns the chunk offset in the 4KiB sectors from the start of the file,
        and the length of the chunk in sectors of 4KiB.
        Used in "write".

        Will return `(0, 0)` if chunk hasn't been generated yet

        Args:
            chunk_x: Chunk's X value
            chunk_z: Chunk's Z value
        """
        b_off = self.header_offset(chunk_x, chunk_z)
        off = int.from_bytes(self.data[b_off : b_off + 3], byteorder="big")
        sectors = self.data[b_off + 3]
        return (off, sectors)
