import ctypes
import ntypes

array_length = 8

def test_open_array_creation():
    oa = ntypes.OpenArray(ctypes.c_int, array_length)

    assert len(oa) == array_length
    for value in oa:
        assert value == 0

def test_open_array_creation_with_elements():
    ints = list(range(array_length))
    oa = ntypes.OpenArray(ctypes.c_int, elements=ints)

    assert len(oa) == array_length
    for list_value, array_value in zip(ints, oa):
        assert list_value == array_value
