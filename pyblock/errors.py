#!/usr/bin/env python3
"""Defines Exceptions."""
__author__ = "Alexander Dietz"
__license__ = "MIT"


class OutOfBoundsCoordinates(ValueError):
    """Exception used for when coordinates are out of bounds"""


class ChunkNotFound(Exception):
    """Exception used for when a chunk was not found"""


class EmptySectionAlreadyExists(Exception):
    """
    Exception used for when trying to add an `EmptySection` to an `EmptyChunk`
    and the chunk already has a section with the same Y
    """


class GZipChunkData(Exception):
    """Exception used when trying to get chunk data compressed in gzip"""
