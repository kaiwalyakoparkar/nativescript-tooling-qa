"""
Device type enum.
"""
from aenum import IntEnum


class DeviceType(IntEnum):
    _init_ = 'value string'

    EMU = 1, 'emulator'
    SIM = 2, 'simulator'
    ANDROID = 3, 'android device'
    IOS = 4, 'ios device'

    def __str__(self):
        return self.string
