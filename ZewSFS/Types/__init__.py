# localmodules:start
from .Bool import Bool
from .BoolArray import BoolArray
from .Byte import Byte
from .ByteArray import ByteArray
from .Double import Double
from .DoubleArray import DoubleArray
from .Float import Float
from .FloatArray import FloatArray
from .Int import Int
from .IntArray import IntArray
from .Long import Long
from .LongArray import LongArray
from .Null import Null
from .SFSArray import SFSArray
from .SFSObject import SFSObject
from .Short import Short
from .ShortArray import ShortArray
from .UtfString import UtfString
from .UtfStringArray import UtfStringArray
# localmodules:end

sfs2x_datatypes = {
    "null": Null,
    "bool": Bool,
    "byte": Byte,
    "short": Short,
    "int": Int,
    "long": Long,
    "float": Float,
    "double": Double,
    "utf_string": UtfString,
    "bool_array": BoolArray,
    "byte_array": ByteArray,
    "short_array": ShortArray,
    "int_array": IntArray,
    "long_array": LongArray,
    "float_array": FloatArray,
    "double_array": DoubleArray,
    "utf_string_array": UtfStringArray,
    "sfs_array": SFSArray,
    "sfs_object": SFSObject,
}


def _sfs_type_name(val):
    return getattr(val, "get_type", lambda: type(val).__name__.lower())()


def _sfs_value(val):
    return getattr(val, "get_value", lambda: val)()


def stringify_object(offset, object, output):
    object_values = object.get_value()
    for a in object_values.keys():
        val = object_values[a]
        tname = _sfs_type_name(val)
        if tname == "sfs_object":
            output += (
                "\t" * offset
                + "("
                + list(sfs2x_datatypes.keys())[18]
                + ") "
                + a
                + ":\n"
            )
            output = stringify_object(offset + 1, val, output)
        elif tname == "sfs_array":
            output += (
                "\t" * offset
                + "("
                + list(sfs2x_datatypes.keys())[17]
                + ") "
                + a
                + ":\n"
            )
            output = stringify_array(offset + 1, val, output)
        else:
            output += (
                "\t" * offset
                + "("
                + tname
                + ") "
                + a
                + ": "
                + str(_sfs_value(val))
                + "\n"
            )
    return output


def stringify_array(offset, array, output):
    array_value = array.get_value()
    for a in range(len(array_value)):
        val = array_value[a]
        tname = _sfs_type_name(val)
        if tname == "sfs_object":
            output += "\t" * offset + "(" + list(sfs2x_datatypes.keys())[18] + ")\n"
            output = stringify_object(offset + 1, val, output)
        elif tname == "sfs_array":
            output += "\t" * offset + "(" + list(sfs2x_datatypes.keys())[17] + ")\n"
            output = stringify_array(offset + 1, val, output)
        else:
            output += (
                "\t" * offset
                + "("
                + tname
                + ") "
                + str(_sfs_value(val))
                + "\n"
            )
    return output
