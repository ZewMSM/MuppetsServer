from io import BytesIO

from ZewSFS.Types import SFSObject


def compile_packet(packet: SFSObject) -> bytes:
    """
    This function compiles a packet into bytes.

    Args:
        packet (SFSObject): The packet to be compiled.

    Returns:
        bytes: The compiled packet in bytes.

    Raises:
        CompilePacketException: If there is an error in compiling the packet.
    """
    compiled_packet = packet.pack()
    if len(compiled_packet) < 65535:
        return b'\x80' + (len(compiled_packet)).to_bytes(2, "big") + compiled_packet
    else:
        return b'\x88' + (len(compiled_packet)).to_bytes(4, "big") + compiled_packet


def decompile_packet(packet: BytesIO) -> SFSObject:
    """
    This function decompiles a packet from bytes to an SFSObject.

    Args:
        packet (BytesIO): The packet in bytes to be decompiled.

    Returns:
        SFSObject: The decompiled packet as an SFSObject.
    """
    pkg = SFSObject.unpack(packet, None, True)
    return pkg.get('p')
