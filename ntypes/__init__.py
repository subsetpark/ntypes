from __future__ import absolute_import

import os
from ctypes import CDLL, POINTER, Array, Structure, byref, c_bool, c_long
from fnmatch import fnmatch

# Value types

ArrayLength = c_long

n_bool = c_bool

# Wrapper classes


class Object(Structure):
    pass


class _OpenArrayBase(list):
    """
    A constructor for openArray arguments to Nim procedures. Realized within
    Nim as a pointer to the beginning of an array, followed by the array's
    length as an integer.
    """

    def __init__(self, elements=None):
        super(_OpenArrayBase, self).__init__()

        if elements is not None:
            for element in elements:
                self.append(element)

    def array(self):
        array_type = self.element_type * len(self)
        array = array_type()

        for i, element in enumerate(self):
            array[i] = element

        return array


def OpenArray(element_type):
    """
    Declare an OpenArray type.

    >>> import ctypes
    >>> int_open_array_class = OpenArray(ctypes.c_int)
    >>> print(int_open_array_class.__name__)
    c_intOpenArray
    >>> issubclass(int_open_array_class, _OpenArrayBase)
    True
    >>> int_open_array = int_open_array_class()
    >>> type(int_open_array) == int_open_array_class
    True
    >>> int_open_array.append(1)
    >>> int_open_array.append(2)
    >>> print(int_open_array[0])
    1
    >>> array = int_open_array.array()
    >>> print(len(array))
    2
    """
    class_name = "{}OpenArray".format(element_type.__name__)
    attrs = {"element_type": element_type}
    return type(class_name, (_OpenArrayBase, ), attrs)


class NimArgs(list):
    """
    Constructor for an argument list for a Nim procedure.

    >>> import ctypes
    >>> int_open_array = OpenArray(ctypes.c_int)()
    >>> int_open_array.append(1)
    >>> int_open_array.append(2)
    >>> args = NimArgs(int_open_array)
    >>> len(args)
    2
    >>> len(args._proc_args())
    1
    >>> print(args)
    Arguments: [@[1, 2]]
    >>> proc_arg = args.get_proc_arg(0)
    >>> proc_arg[0]
    1
    >>> proc_arg[1]
    2
    """

    def __init__(self, *elements):
        super(NimArgs, self).__init__()

        self.obj_map = {}

        for element in elements:
            self.append(element)

    def append(self, element):
        """
        Append an object representing a Nim openArray, object, or value.
        """
        if isinstance(element, _OpenArrayBase):
            return self.extend([element.array(), ArrayLength(len(element))])
        elif isinstance(element, Object):
            return super(NimArgs, self).append(byref(element))
        else:
            return super(NimArgs, self).append(element)

    def _proc_args(self):
        values = []
        skip = False
        for element in self:
            if skip:
                skip = False
                continue

            values.append(element)

            if isinstance(element, Array):
                skip = True
        return values

    def get_proc_arg(self, idx):
        """
        Index into the argument of values that would be passed to the Nim FFI.
        """
        return self._proc_args()[idx]

    def __repr__(self):
        strs = []
        for element in self._proc_args():
            if isinstance(element, Array):
                strs.append("@[{}]".format(", ".join(
                    repr(e) for e in element)))
            else:
                strs.append(repr(element))
        return "Arguments: [{}]".format(", ".join(strs))


class NimArgTypes(list):
    """
    Constructor for an argument type list for a Nim procedure.

    >>> import ctypes
    >>> arg_types = NimArgTypes()
    >>> arg_types.append(ctypes.c_int)
    >>> print(len(arg_types))
    1
    >>> print(arg_types[0].__name__)
    c_int
    >>> int_open_array_class = OpenArray(ctypes.c_int)
    >>> int_open_array = int_open_array_class()
    >>> arg_types.append(int_open_array_class)
    >>> print(len(arg_types))
    3
    """

    def __init__(self, *element_types):
        super(NimArgTypes, self).__init__()

        for element_type in element_types:
            self.append(element_type)

    def append(self, element_type):
        """
        Append a class or c type representing a Nim type.
        """
        if issubclass(element_type, _OpenArrayBase):
            return self.extend(
                [POINTER(element_type.element_type), ArrayLength])
        elif issubclass(element_type, Object):
            return super(NimArgTypes, self).append(POINTER(element_type))
        else:
            return super(NimArgTypes, self).append(element_type)


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


if __name__ == "__main__":
    import doctest
    doctest.testmod()
