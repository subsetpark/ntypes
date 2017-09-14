from __future__ import absolute_import
from ctypes import POINTER, Structure, c_bool, pointer, c_long
from fnmatch import fnmatch

import os
from ctypes import CDLL

# Value types

ArrayLength = c_long

n_bool = c_bool

# Wrapper classes


class Object(Structure):
    pass


class OpenArray(object):
    """
    A constructor for openArray arguments to Nim procedures. Realized within
    Nim as a pointer to the beginning of an array, followed by the array's
    length as an integer.
    """

    def __init__(self, element_type, array_length=None, elements=None):
        if array_length is None and elements is None:
            raise ValueError("array_length or elements is required.")

        self.array_length = array_length or len(elements)
        self.element_type = element_type
        self.array_type = self.element_type * self.array_length
        self.array = self.array_type()

        if elements is not None:
            self.populate(elements)

    def __setitem__(self, idx, item):
        return self.array.__setitem__(idx, item)

    def __getitem__(self, idx):
        return self.array.__getitem__(idx)

    def __len__(self):
        return self.array.__len__()

    def __iter__(self):
        return iter(self.array)

    def populate(self, elements):
        for i, element in enumerate(elements):
            self.array[i] = element


class NimArgTypes(object):
    """
    Constructor for an argument type list for a Nim procedure.
    """

    def __init__(self):
        self.arg_types = []

    def add_open_array(self, element_type):
        if isinstance(element_type, OpenArray):
            self.arg_types.extend(
                [POINTER(element_type.object_type), ArrayLength])
        else:
            self.arg_types.extend([POINTER(element_type), ArrayLength])

    def add_object(self, object_type):
        self.arg_types.append(POINTER(object_type))

    def __iter__(self):
        return self.arg_types.__iter__()


class NimArgs(object):
    """
    Constructor for an argument list for a Nim procedure.
    """

    def __init__(self):
        self.args = []

    def add(self, element):
        if isinstance(element, OpenArray):
            return self.args.extend([element, ArrayLength(len(element))])
        elif isinstance(element, Object):
            return self.args.append(pointer(element))
        else:
            return self.args.add(element)

    def __iter__(self):
        return self.args.__iter__()


def NDLL(path, libname, ext="so"):
    """
    Get the appropriate library filename and load it with ctypes.
    """
    dir_list = os.listdir(path)
    matching_names = [
        fn for fn in dir_list if fnmatch(fn, "{}*.{}".format(libname, ext))
    ]
    if not matching_names:
        raise RuntimeError("{} shared object not found. (Found: {})".format(
            libname, dir_list))
    filename = min(matching_names, key=lambda fn: len(fn))

    return CDLL(os.path.join(path, filename))
