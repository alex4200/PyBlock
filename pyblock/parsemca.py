#!/usr/bin/env python3
"""
This package parses mca files.

The structure is expained here: https://minecraft.gamepedia.com/Region_file_format
"""
__author__ = "Alexander Dietz"
__license__ = "MIT"

import sys
import zlib
from pathlib import Path

from pyblock.chunk import Chunk


class MCA():
    """Parser for MCA files.
    """

    LEN_LOCATION = 4
    LEN_TIMESTAMP = 4
    CHUNK_LENGTH = 4096

    def __init__(self, filename, chunk_list, area, verbose):
        """Initialize this parser object.

        Args:
            filename (string): name of the mca file to parse
            chunk_list (list): list of chunks to analyze.
            area (list): min/max block coordinates to be analyzed.
            verbose (int): verbosity.
        """
        self.filename = filename
        self.data = Path(filename).read_bytes()

        # what chunks to analyze
        self.chunk_list = chunk_list

        # area to analyze
        self.area = area

        # verbosity
        self.verbose = verbose

        # extracting all the chunk data
        self.chunks = {}
        self.extract_locations()
        self.extract_timestamps()
        self.extract_chunkdata()

    def int(self, start, end):
        """Returns an integer from a range in the binary data, big-endian.
        """
        return int.from_bytes(self.data[start:end], byteorder='big', signed=False)

    def extract_locations(self):
        """Read all the 1024 location entries.
        These define where chunks are located in the regions files.

        See https://minecraft.gamepedia.com/Region_file_format
        """
        if self.verbose > 0:
            print("  Extracting locations ...")
        for location_number in range(1024):
            index = self.LEN_LOCATION * location_number
            location_offset = self.int(index, index+3)

            if location_offset > 0:
                chunk = Chunk(location_offset, self.area, self.verbose)
                self.chunks[location_number] = chunk

    def extract_timestamps(self):
        """Read all the 1024 timestamp entries.

        See https://minecraft.gamepedia.com/Region_file_format
        """
        if self.verbose > 0:
            print("  Extracting timestamps ...")
        for timestamp_number in range(1024):
            index = self.CHUNK_LENGTH + self.LEN_TIMESTAMP * timestamp_number
            timestamp = self.int(index, index+4)
            if timestamp_number in self.chunks:
                self.chunks[timestamp_number].set_timestamp(timestamp)

    def extract_chunkdata(self):
        """Read all the 1024 chunkdata entries.

        See https://minecraft.gamepedia.com/Region_file_format
        """
        if self.verbose > 0:
            print("  Extracting chunks ...")
        number_chunks = len(self.chunks.keys())
        counter = 0
        chunks_to_remove = []
        for number, chunk in self.chunks.items():
            counter += 1
            if self.verbose > 0:
                sys.stdout.write(f"\r    Extracting chunk {counter}/{number_chunks}")
                sys.stdout.flush()

            index = self.CHUNK_LENGTH * chunk.offset
            length = self.int(index, index+4)

            # compute indices
            i_begin = index+5
            i_end = i_begin + length - 1

            # get the compressed chunk data, uncompress it, and add it to chunk
            # see https://minecraft.gamepedia.com/Chunk_format
            zipdata = self.data[i_begin:i_end]
            chunkdata = zlib.decompress(zipdata)
            chunk.add_data(chunkdata)

            # check if chunk coordinates are to be kept
            if self.chunk_list != 'all':
                if chunk.get_coords() not in self.chunk_list:
                    chunks_to_remove.append(number)

        # Remove chunks not used
        if self.verbose > 0:
            print(f"  Ignoring {len(chunks_to_remove)} chunks.")
        for number in chunks_to_remove:
            del self.chunks[number]

    def number_chunks(self):
        """Returns the number of kept chunks.
        """
        return len(self.chunks)

    def extract_sum_blocks(self):
        """Returns a dict of all blocks from the list of kept chunks
        with key being the block type and the value the total number of blocks.
        """
        blocks = {}
        for number, chunk in self.chunks.items():
            if self.verbose > 1:
                sys.stdout.write(f"\r    Analyzing chunk {number}")
                sys.stdout.flush()
            chunk_blocks = chunk.get_blocks()
            for key, locs in chunk_blocks.items():
                value = len(locs)
                if key in blocks:
                    blocks[key] += value
                else:
                    blocks[key] = value
        return blocks

    def find_block_locations(self, block_name):
        """Returns a list with the locations of blocks of type 'block_name'.
        """
        locations = []
        for number, chunk in self.chunks.items():
            if self.verbose > 1:
                sys.stdout.write(f"\r    Analyzing chunk {number}")
                sys.stdout.flush()
            blocks = chunk.get_blocks()
            if block_name in blocks:
                locations.extend(blocks[block_name])
        return locations
    