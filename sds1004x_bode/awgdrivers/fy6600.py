'''
Created on November 20, 2019

@author: Dundarave

Driver for FeelTech FY6600 AWG.
'''

import serial
import time
from .base_awg import BaseAWG
from . import constants
from .exceptions import UnknownChannelError

# Port settings constants
BAUD_RATE = 115200
BITS = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOP_BITS = serial.STOPBITS_ONE
TIMEOUT = 5

# FY6600 Data packet ends with just a single LF (\n) character
EOL = '\x0A'
# Channels validation tuple
CHANNELS = (0, 1, 2)
CHANNELS_ERROR = "Channel can be 1 or 2."
# FY6600 requires some delay between commands. 0.5 seconds seems to work, .25 seconds is iffy. Your unit might need more.
SLEEP_TIME = 0.5

# Output impedance of the AWG
R_IN = 50.0


class FY6600(BaseAWG):
    '''
    FY6600 function generator driver.
    '''
    SHORT_NAME = "fy6600"

    def __init__(self, port: str = "", baud_rate: int = BAUD_RATE, timeout: int = TIMEOUT, log_debug: bool = False):
        """baud_rate parameter is ignored."""
        super().__init__(log_debug=log_debug)
        self.printdebug("init")
        self.port = port
        self.ser = None
        self.timeout = timeout
        self.channel_on = [False, False]
        self.r_load = [50, 50]
        self.v_out_coeff = [1, 1]

    def _connect(self):
        self.ser = serial.Serial(self.port, BAUD_RATE, BITS, PARITY, STOP_BITS, timeout=self.timeout)

    def disconnect(self):
        self.printdebug("disconnect")
        self.ser.close()

    def _send_command(self, cmd):
        cmd = (cmd + EOL).encode()
        self.ser.write(cmd)
        time.sleep(SLEEP_TIME)

    def initialize(self):
        self.printdebug("initialize")
        self.channel_on = [False, False]
        self._connect()
        self.enable_output(None, False)

    def get_id(self) -> str:
        self._send_command("UID")
        ans = self.ser.read_until("\r\n".encode("utf8"), size=None).decode("utf8")
        return ans.strip()

    def enable_output(self, channel: int = None, on: bool = False):
        """
        Turns channels output on or off.
        The channel is defined by channel variable. If channel is None, both channels are set.

        Commands:
            WMN1 means main wave output set to on
            WMN0 means main wave output set to off
            WFN1 means second channel wave output set to on
            WFN0 means second channel wave output set to off

        Separate commands are thus needed to set the channels for the FY6600.
        """
        self.printdebug(f"enable_output(channel: {channel}, on:{on})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is not None and channel != 0:
            self.channel_on[channel - 1] = on
        else:
            self.channel_on = [on, on]

        ch1 = "1" if self.channel_on[0] else "0"
        ch2 = "1" if self.channel_on[1] else "0"

        # The fy6600 uses separate commands to enable each channel.
        cmd = "WMN%s" % (ch1)
        self._send_command(cmd)
        cmd = "WFN%s" % (ch2)
        self._send_command(cmd)

    def set_frequency(self, channel: int, freq: float):
        """
        Sets frequency on the selected channel.

        Command examples:
            WMF00000000000001 equals 1 uHz on channel 1
            WMF00000001000000 equals 1 Hz on channel 1
            WMF00001000000000 equals 1 kHz on channel 1
            WFF00000000000001 equals 1 uHz on channel 2
            and so on.
        """
        self.printdebug(f"set_frequency(channel: {channel}, freq:{freq})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        freq_str = "%.2f" % freq
        freq_str = freq_str.replace(".", "")
        freq_str = freq_str + "0000"

        # Channel 1
        if channel in (0, 1) or channel is None:
            cmd = "WMF%s" % freq_str
            self._send_command(cmd)

        # Channel 2
        if channel in (0, 2):
            cmd = "WFF%s" % freq_str
            self._send_command(cmd)

    def set_phase(self, channel: int, phase: float):
        """
        Sends the phase setting command to the generator.
        The phase is set on channel 2 only.

        Commands:
            WMP100.0 is 100.0 degrees on Channel 1
            WFP4.9 is 4.9 degrees on Channel 2. We are only setting phase on channel 2 here.
        """
        self.printdebug(f"set_phase(channel: {channel}, phase: {phase}), but forced on channel 2")
        if phase < 0:
            phase += 360

        cmd = "WFP%s" % (phase)
        self._send_command(cmd)

    def set_wave_type(self, channel: int, wave_type: int):
        """
        Sets wave type of the selected channel.

        Commands:
            WMW00 for Sine wave channel 1
            WFW00 for Sine wave channel 2
        Both commands are "hard-coded".
        """
        self.printdebug(f"set_wave_type(channel: {channel}, wavetype:{wave_type}), but forcing sine wave")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)
        if wave_type not in constants.WAVE_TYPES:
            raise ValueError("Incorrect wave type.")

        # Channel 1
        if channel in (0, 1) or channel is None:
            cmd = "WMW00"
            self._send_command(cmd)

        # Channel 2
        if channel in (0, 2) or channel is None:
            cmd = "WFW00"
            self._send_command(cmd)

    def set_amplitude(self, channel: int, amplitude: float):
        """
        Sets amplitude of the selected channel.

        Commands:
            WMA0.44 for 0.44 volts Channel 1
            WFA9.87 for 9.87 volts Channel 2
        """
        self.printdebug(f"set_amplitude(channel: {channel}, amplitude:{amplitude})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        """
        Adjust the output amplitude to obtain the requested amplitude
        on the defined load impedance.
        """
        amplitude = amplitude / self.v_out_coeff[channel - 1]
        amp_str = "%.3f" % amplitude

        # Channel 1
        if channel in (0, 1) or channel is None:
            cmd = "WMA%s" % amp_str
            self._send_command(cmd)

        # Channel 2
        if channel in (0, 2) or channel is None:
            cmd = "WFA%s" % amp_str
            self._send_command(cmd)

    def set_offset(self, channel: int, offset: float):
        """
        Sets DC offset of the selected channel.

        Command examples:
        WMO0.33 sets channel 1 offset to 0.33 volts
        WFO-3.33sets channel 2 offset to -3.33 volts
        """
        self.printdebug(f"set_offset(channel: {channel}, offset:{offset})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)
        # Adjust the offset to the defined load impedance
        offset = offset / self.v_out_coeff[channel - 1]

        # Channel 1
        if channel in (0, 1) or channel is None:
            cmd = "WMO%s" % offset
            self._send_command(cmd)

        # Channel 2
        if channel in (0, 2) or channel is None:
            cmd = "WFO%s" % offset
            self._send_command(cmd)

    def set_load_impedance(self, channel: int, z: float):
        """
        Sets load impedance connected to each channel. Default value is 50 Ohm.
        """
        self.printdebug(f"set_load_impedance(channel: {channel}, impedance:{z})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        self.r_load[channel - 1] = z

        """
        Vout coefficient defines how the requestd amplitude must be increased
        in order to obtain the requested amplitude on the defined load.
        If the load is Hi-Z, the amplitude must not be increased.
        If the load is 50 Ohm, the amplitude has to be double of the requested
        value, because of the voltage divider between the output impedance
        and the load impedance.
        """
        if z == constants.HI_Z:
            v_out_coeff = 1
        else:
            v_out_coeff = z / (z + R_IN)
        self.v_out_coeff[channel - 1] = v_out_coeff


if __name__ == '__main__':
    print("This module shouldn't be run. Run awg_tests.py or bode.py instead.")
