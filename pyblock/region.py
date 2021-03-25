import time
import math
from typing import Tuple, Union, BinaryIO
from nbt import nbt
import zlib
from io import BytesIO
import logging

import pyblock
from . import chunk, empty_chunk
from . import empty_section
from .errors import GZipChunkData
from .block import Block
from .tools import combine_dicts, index_to_coord

L = logging.getLogger("pyblock")


# https://minecraft.gamepedia.com/Region_file_format


class Region:
    """
    Minecraft region
    """

    def __init__(self, path, x, z):
        """Makes a Region object from data, which is the region file content.

        Args:
            path (str): Path to the world folder
            x,z (int): Coordinates of the region
        """
        self.path = path
        self.filename = str(path) + f"/r.{x}.{z}.mca"
        with open(self.filename, "rb") as f:
            self.data = f.read()

        self.x = x
        self.z = z

    def list_blocks_from_chunk(self, chunk_coords):
        """Returns a list of all blocks for the given chunk coordinates.

        Args:
            chunk_coords (list): List of chunk coordinates
        """
        # Get the data of the chunk at the given coordinates
        nbt_data = self.chunk_data(*chunk_coords)
        if nbt_data is None:
            return {}
        chunk = pyblock.chunk.Chunk(nbt_data)

        # Parse the chunk data and add the blocks to the dict
        blocks = {}
        for block in chunk.stream_chunk():
            if block.id in blocks:
                blocks[block.id] += 1
            else:
                blocks[block.id] = 1
        return blocks

    def find_blocks_from_chunk(self, chunk_coords, blockname):
        """Returns a list of all block coordinates for the given chunk coordinates.

        Args:
            chunk_coords (list): List of chunk coordinates
            blockname (str): Name of the block.
        """
        L.debug(
            f"Finding blocks for chunk {chunk_coords[0]}/{chunk_coords[1]} "
            f"in region {self.x}/{self.z}."
        )

        # Get the data of the chunk at the given coordinates
        nbt_data = self.chunk_data(*chunk_coords)
        if nbt_data is None:
            return []
        chunk = pyblock.chunk.Chunk(nbt_data)

        # Absolute coordinates of the chunk
        base_x = self.x * 512 + 16 * chunk_coords[0]
        base_z = self.z * 512 + 16 * chunk_coords[1]

        # Parse the chunk data and store the coordintes of a matching block
        locations = []
        for index, block in enumerate(chunk.stream_chunk()):
            if block.id == blockname:
                x, y, z = index_to_coord(index)
                locations.append((x + base_x, y, z + base_z))
        return locations

    def list_blocks(self, list_chunks):
        """Returns a dict of blocks found in the list of chunks.

        Args:
            list_chunks (list): List of chunk coordinates
        """
        blocks = {}
        for chunk_coord in list_chunks:
            blocks_chunk = self.list_blocks_from_chunk(chunk_coord)
            blocks = combine_dicts(blocks, blocks_chunk)
        return blocks

    def find_blocks(self, list_chunks, block):
        """Returns a list of absolute coordinates of the given block type within the list of chunks

        Args:
            list_chunk (list): List of chunk coordinates
            block (str): Name of the block
        """
        locations = []
        for chunk_coord in list_chunks:
            locations.extend(self.find_blocks_from_chunk(chunk_coord, block))
        return locations

    def set_blocks_for_map(self, pymap, list_chunks):
        """Add blocks to a McMap.

        Args:
            pymap (PyMap): Map for all levels
            list_chunk (list): List of chunk coordinates
        """
        regx = self.x * 512
        regz = self.z * 512
        n = len(list_chunks)
        for index, chunk_coords in enumerate(list_chunks):
            L.debug(
                "Analyzing chunk %d/%d at %d/%d"
                % (index, n, chunk_coords[0], chunk_coords[1])
            )

            # Get the chunk instance
            nbt_data = self.chunk_data(*chunk_coords)
            if nbt_data:
                chunk = pyblock.chunk.Chunk(nbt_data)
            else:
                L.error(
                    "No chunk found! Probably this part has never been rendered before!"
                )

            # Parse all blocks in the chunk
            for index, block in enumerate(chunk.stream_chunk()):
                x, y, z = index_to_coord(index)
                pymap.set_block(x + 16 * chunk.x, y, z + 16 * chunk.z, block)

        return pymap

    def update_chunks(self, chunks):
        """Returns a dictionary with updated chunk bytes (value) for a given chunk coordinate (key).

        Args:
            chunks: Dictionary with keys being chunk coordinates,
                    and values being a list with relative block coordinates
                    with elements (block, x, y, z).
        """
        # Dictionary of new chunks
        new_chunks = {}

        for chunk_coord, locations in chunks.items():
            L.debug(f"Updating chunk {chunk_coord[0]}/{chunk_coord[1]}")

            # Copy the chunk
            write_chunk = self.copy_chunk(*chunk_coord)

            # Manipulate the block data within the new chunk
            for location in locations:
                write_chunk.set_block(*location)

            # Store the manipulated chunk
            new_chunks[chunk_coord] = write_chunk.get_data()

        return new_chunks

    def write(self, chunks_to_update):
        """Writes the new region to a file.
        Used for editing a chunk

        Args:
            chunks_to_update (dict): Dictionary containing data for chunks to be changed.
        """
        # Create the final data structure for the file
        locations_header = bytes()
        timestamps = bytes(4096)
        chunk_bytes = bytes()

        # A list of two-pairs that denote the location of the chunk and its size
        offsets = []

        # An index denoting the location of the current chunk
        sector_offset = 2

        # Loop over all chunks inside the region
        for chunk_z in range(32):
            for chunk_x in range(32):
                chunk_coord = (chunk_x, chunk_z)

                # Get the chunk location
                off, sectors = self.chunk_location(*chunk_coord)

                if chunk_coord not in chunks_to_update:
                    # Use existing data without change
                    if (off, sectors) != (0, 0):
                        # Copy the chunk data directly from the data
                        start = off * 4096
                        end = start + sectors * 4096
                        chunk_bytes += self.data[start:end]
                    else:
                        # Chunk does not exist
                        sectors = 0
                else:
                    # Use updated data (either modified or copied)
                    L.debug("Writing modified chunk at %d/%d" % (chunk_x, chunk_z))
                    to_add = chunks_to_update[chunk_coord]
                    if to_add != 0:
                        chunk_bytes += to_add
                        sectors = math.ceil(len(to_add) / 4096)
                    else:
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
        L.info("Writing %s" % self.filename)
        with open(self.filename, "wb") as f:
            f.write(final)

    def read_chunks_to_copy(self, chunks_to_copy, world_source):
        """Returns a dictionary containing the chunk bytes (values) of chunks to be copied (with
        coordinates as key).

        Args:
            chunks_to_copy (dict): Dictionary containing the region and coordinates of the
                                   source and destination chunks.
            world_source (string): Path of the world where the chunks are copied from.
        """

        copy_chunks = {}
        for chunk_coord, source_item in chunks_to_copy.items():
            # Get source information
            sr = source_item["source_region"]
            sc = source_item["source_chunk"]

            # Read source region and get location of source chunk
            source_region = Region(world_source, *sr)
            off, sectors = source_region.chunk_location(*sc)

            # Copy the chunk data directly from the data
            if (off, sectors) != (0, 0):
                start = off * 4096
                end = start + sectors * 4096
                chunk_bytes = source_region.data[start:end]
            else:
                chunk_bytes = 0

            copy_chunks[chunk_coord] = chunk_bytes

        return copy_chunks

    def copy_chunks(self, chunks_to_copy):
        """Copies and Writes a new region to a file, with the given chunks to be replaced.
        Used from mcmain.py to copy chunks.

        Args:
            chunks_to_copy (dict): Keys are chunks to be replaces, value is the source-region/chunk
        """
        # Create the final data structure for the file
        locations_header = bytes()
        timestamps = bytes(4096)
        chunk_bytes = bytes()

        # A list of two-pairs that denote the location of the chunk and its size
        offsets = []

        # An index denoting the location of the current chunk
        sector_offset = 2

        # Loop over all chunks inside the region
        for chunk_z in range(32):
            for chunk_x in range(32):
                chunk_coord = (chunk_x, chunk_z)
                if chunk_coord in chunks_to_copy.keys():
                    # Here we copy a chunk
                    L.debug(
                        f"Copying to {chunk_x}/{chunk_z} in region {self.x}/{self.z}"
                    )
                    source_item = chunks_to_copy[chunk_coord]
                    sr = source_item["source_region"]
                    sc = source_item["source_chunk"]
                    L.debug(
                        f"Copying from %d/%d  %d/%d   to  %d/%d  %d/%d",
                        sr[0],
                        sr[1],
                        sc[0],
                        sc[1],
                        self.x,
                        self.z,
                        chunk_x,
                        chunk_z,
                    )

                    # Read source region and get location of source chunk
                    source_region = Region(self.path, *sr)
                    off, sectors = source_region.chunk_location(*sc)

                    # Copy the chunk data directly from the data
                    if (off, sectors) != (0, 0):
                        start = off * 4096
                        end = start + sectors * 4096
                        chunk_bytes += source_region.data[start:end]
                    else:
                        sectors = 0
                else:
                    # Copy from self
                    off, sectors = self.chunk_location(chunk_x, chunk_z)

                    # Copy the chunk data directly from the data
                    if (off, sectors) != (0, 0):
                        start = off * 4096
                        end = start + sectors * 4096
                        chunk_bytes += self.data[start:end]
                    else:
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
        L.info("Writing %s" % self.filename)
        with open(self.filename, "wb") as f:
            f.write(final)

    def copy_chunk(self, chunk_x, chunk_z):
        """Returns a modifiable copy of a chunk.
        Used in update_chunks.

        Args:
            chunk_x (int): Chunk's X value
            chunk_z (int): Chunk's Z value
        """
        # Get the chunk data
        nbt_data = self.chunk_data(chunk_x, chunk_z)
        if nbt_data:
            rchunk = chunk.Chunk(nbt_data)
        else:
            raise ValueError("Empty Chunk found, what the hell?")

        # Create writable chunk
        new_chunk = empty_chunk.EmptyChunk(chunk_x, chunk_z)

        # Loop over all the vertical sections
        for y in range(16):
            # Get the list of blocks in a section
            section_blocks = list(rchunk.stream_blocks(section=y))

            # Create a new writable section
            new_section = empty_section.EmptySection(y)

            # Add the blocks to the section and to the chunk
            new_section.blocks = section_blocks
            new_chunk.add_section(new_section)

        return new_chunk

    def get_locations(self):
        return self.data[:4096]

    def get_timestamps(self):
        return self.data[4096:8192]

    @staticmethod
    def header_offset(chunk_x, chunk_z):
        """
        Returns the byte offset for given chunk in the header

        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value
        """
        return 4 * (chunk_x % 32 + chunk_z % 32 * 32)

    def chunk_location(self, chunk_x, chunk_z):
        """
        Returns the chunk offset in the 4KiB sectors from the start of the file,
        and the length of the chunk in sectors of 4KiB

        Will return ``(0, 0)`` if chunk hasn't been generated yet

        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value
        """
        b_off = self.header_offset(chunk_x, chunk_z)
        off = int.from_bytes(self.data[b_off : b_off + 3], byteorder="big")
        sectors = self.data[b_off + 3]
        return (off, sectors)

    def chunk_data(self, chunk_x, chunk_z):
        """
        Returns the NBT data for a chunk

        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value

        Raises
        ------
        anvil.GZipChunkData
            If the chunk's compression is gzip
        """
        off = self.chunk_location(chunk_x, chunk_z)
        # (0, 0) means it hasn't generated yet, aka it doesn't exist yet
        if off == (0, 0):
            return
        off = off[0] * 4096
        length = int.from_bytes(self.data[off : off + 4], byteorder="big")
        compression = self.data[off + 4]  # 2 most of the time
        if compression == 1:
            raise GZipChunkData("GZip is not supported")
        compressed_data = self.data[off + 5 : off + 5 + length - 1]
        return nbt.NBTFile(buffer=BytesIO(zlib.decompress(compressed_data)))

    def get_chunk(self, chunk_x, chunk_z):
        """
        Returns the chunk at given coordinates,
        same as doing ``Chunk.from_region(region, chunk_x, chunk_z)``

        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value


        :rtype: :class:`anvil.Chunk`
        """
        return anvil.Chunk.from_region(self, chunk_x, chunk_z)

    @classmethod
    def from_file(cls, file):
        """
        Creates a new region with the data from reading the given file

        Parameters
        ----------
        file
            Either a file path or a file object
        """
        if isinstance(file, str):
            with open(file, "rb") as f:
                return cls(data=f.read())
        else:
            return cls(data=file.read())
