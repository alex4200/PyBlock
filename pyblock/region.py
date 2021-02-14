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
from .tools import combine_dicts

L = logging.getLogger("pyblock")


# https://minecraft.gamepedia.com/Region_file_format

class Region:
    """
    Minecraft region
    """
    def __init__(self, path, x, z):
        """Makes a Region object from data, which is the region file content.

        Args:
            path (str): Path to the world
            x,z (int): Coordinates of the region
        """

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
        # Get the data of the chunk at the given coordinates
        nbt_data = self.chunk_data(*chunk_coords)
        if nbt_data is None:
            return []
        chunk = pyblock.chunk.Chunk(nbt_data)

        regx = self.x * 512
        regz = self.z * 512

        # Parse the chunk data and add the blocks to the dict
        locations = []
        for index, block in enumerate(chunk.stream_chunk()):
            if block.id == blockname:
                y = index // 256
                z = (index -y*256) // 16
                x = index - y * 256 - z * 16
                locations.append((x + 16*chunk.x + regx, y, z + 16*chunk.z + regz))
        return locations

    
    def list_blocks(self, list_chunks):
        """Returns a dict of blocks found in the list of chunks.

        Args:
            chunk_coords (list): List of chunk coordinates
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
            L.debug("Analyzing chunk %d/%d at %d/%d" % (index, n, chunk_coords[0], chunk_coords[1]))

            # Get the chunk instance
            nbt_data = self.chunk_data(*chunk_coords)
            if nbt_data:
                chunk = pyblock.chunk.Chunk(nbt_data)

            # Parse all blocks in the chunk
            for index, block in enumerate(chunk.stream_chunk()):
                y = index // 256
                w = index - y * 256
                z = w // 16
                x = w - z * 16

                # Sets the pixel in the map
                pymap.set_block(x + 16*chunk.x + regx, y, z + 16*chunk.z + regz, block)

        return pymap


    def update_chunks(self, chunks):
        """Updates the list of given chunks.

        Args:
            chunks: Dictionary of chunk coordinates, the values are lists of block locations 
                    within the chunk (content: (block, x, y, z))
        """
        # Dictionary of new chunks
        self.new_chunks = {}

        for chunk_coord, locations in chunks.items():

            # Copy the chunk
            write_chunk = self.copy_chunk(*chunk_coord)

            # Manipulate the block data within the new chunk
            for location in locations:
                write_chunk.set_block(*location)

            # Store the manipulated chunk
            self.new_chunks[chunk_coord] = write_chunk

        # Write the region to file
        self.write()

    def write(self):
        """Writes the new region to a file.
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
                off, sectors = self.chunk_location(chunk_x, chunk_z)
                if (chunk_x, chunk_z) not in self.new_chunks:
                    if (off, sectors) != (0,0):
                        # Copy the chunk data directly from the data
                        start = off * 4096
                        end = start + sectors * 4096
                        chunk_bytes += self.data[start:end]
                    else: 
                        # Chunk does not exist
                        sectors = 0
                else:
                    L.debug("Writing modified chunk at %d/%d" % (chunk_x, chunk_z))
                    to_add = self.new_chunks[(chunk_x, chunk_z)].get_data()
                    chunk_bytes += to_add
                    sectors = math.ceil(len(to_add) / 4096)

                # Add the offset to the locations header
                if sectors==0:
                    locations_header += bytes(4)
                else:
                    locations_header += sector_offset.to_bytes(3, 'big') + sectors.to_bytes(1, 'big')

                # Advance the index by the size of the current chunk
                sector_offset += sectors

        # Combine the final region data before written to file
        final = locations_header + timestamps + chunk_bytes
        assert len(final) % 4096 == 0 # just in case

        # Save to a file 
        L.info("Writing %s" % self.filename)
        with open(self.filename, 'wb') as f:
            f.write(final)

    def copy_chunk(self, chunk_x, chunk_z):
        """Returns a copy of the chunk that can be modified.

        Args:
            chunk_x: Chunk's X value
            chunk_z: Chunk's Z value
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

    def set_block(self, block, x, y, z):
        """
        """
        print("*** CHECK: region.set_block")
        self.new_region.set_block(block, x, y, z)      


    # X Copied from empty_region
    def save(self, file):
        """
        Returns the region as bytes with
        the anvil file format structure,
        aka the final ``.mca`` file.

        Parameters
        ----------
        file
            Either a path or a file object, if given region
            will be saved there.
        """
        # Store all the chunks data as zlib compressed nbt data
        # chunks_data = []
        # for chunk in self.chunks:
        #     if chunk is None:
        #         chunks_data.append(None)
        #         continue
        #     chunk_data = BytesIO()
        #     if isinstance(chunk, Chunk):
        #         nbt_data = nbt.NBTFile()
        #         nbt_data.tags.append(nbt.TAG_Int(name='DataVersion', value=chunk.version))
        #         nbt_data.tags.append(chunk.data)
        #     else:
        #         nbt_data = chunk.save()
        #     nbt_data.write_file(buffer=chunk_data)
        #     chunk_data.seek(0)
        #     chunk_data = zlib.compress(chunk_data.read())
        #     chunks_data.append(chunk_data)

        # # This is what is added after the location and timestamp header
        # chunks_bytes = bytes()
        # offsets = []
        # for chunk in chunks_data:
        #     if chunk is None:
        #         offsets.append(None)
        #         continue
        #     # 4 bytes are for length, b'\x02' is the compression type which is 2 since its using zlib
        #     to_add = (len(chunk)+1).to_bytes(4, 'big') + b'\x02' + chunk

        #     # offset in 4KiB sectors
        #     sector_offset = len(chunks_bytes) // 4096
        #     sector_count = math.ceil(len(to_add) / 4096)
        #     offsets.append((sector_offset, sector_count))

        #     # Padding to be a multiple of 4KiB long
        #     to_add += bytes(4096 - (len(to_add) % 4096))
        #     chunks_bytes += to_add

        # locations_header = bytes()
        # for offset in offsets:
        #     # None means the chunk is not an actual chunk in the region
        #     # and will be 4 null bytes, which represents non-generated chunks to minecraft
        #     if offset is None:
        #         locations_header += bytes(4)
        #     else:
        #         # offset is (sector offset, sector count)
        #         locations_header += (offset[0] + 2).to_bytes(3, 'big') + offset[1].to_bytes(1, 'big')

        # # Set them all as 0
        # timestamps_header = bytes(4096)

        # final = locations_header + timestamps_header + chunks_bytes

        # # Pad file to be a multiple of 4KiB in size
        # # as Minecraft only accepts region files that are like that
        # final += bytes(4096 - (len(final) % 4096))
        #assert len(final) % 4096 == 0 # just in case

        print("*** CHECK: region.save")

        final = self.data
        assert len(final) % 4096 == 0 # just in case
        print(f"Length of data: {len(final)}  ")

        # Save to a file 
        with open(self.filename, 'wb') as f:
            f.write(final)
        return final

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
        off = int.from_bytes(self.data[b_off : b_off + 3], byteorder='big')
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
        length = int.from_bytes(self.data[off:off + 4], byteorder='big')
        compression = self.data[off + 4] # 2 most of the time
        if compression == 1:
            raise GZipChunkData('GZip is not supported')
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
            with open(file, 'rb') as f:
                return cls(data=f.read())
        else:
            return cls(data=file.read())
