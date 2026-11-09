# =================================================================================
# ads1220.py
#
# MicroPython driver for the Texas Instruments ADS1220 24-bit ADC.
# Note: Base register mappings and SPI routines adapted from rdagger/micropython-ads1220 
# (https://github.com/rdagger/micropython-ads1220)[cite: 8]. Developed, debugged, and modified 
# with assistance from ChatGPT for multi-channel cryogenic sensor telemetry.
# =================================================================================
from machine import Pin, SPI
import utime
import ustruct

# ADS1220 Commands
CMD_RESET = 0x06
CMD_START_SYNC = 0x08
CMD_POWERDOWN = 0x02
CMD_WREG = 0x40
CMD_RREG = 0x20
CMD_RDATA = 0x10

# Config Register Addresses
REG_CONFIG_0 = 0x00
REG_CONFIG_1 = 0x01
REG_CONFIG_2 = 0x02
REG_CONFIG_3 = 0x03

class ADS1220:
    def __init__(self, spi, cs_pin, drdy_pin, name="ADS1220"):
        self.spi = spi
        self.cs = Pin(cs_pin, Pin.OUT, value=1)
        self.drdy = Pin(drdy_pin, Pin.IN, Pin.PULL_UP)
        self.name = name
        self.reset()

    def _select(self):
        self.cs.value(0)
        utime.sleep_us(5)

    def _deselect(self):
        self.cs.value(1)
        utime.sleep_us(5)

    def _wait_for_drdy(self, timeout_ms=500):
        start = utime.ticks_ms()
        while self.drdy.value() == 1:
            if utime.ticks_diff(utime.ticks_ms(), start) > timeout_ms:
                return False
        return True

    def _send_command(self, cmd):
        self._select()
        self.spi.write(bytes([cmd]))
        self._deselect()

    def _write_reg(self, reg, value):
        cmd = CMD_WREG | (reg << 2)
        self._select()
        self.spi.write(bytes([cmd, value]))
        self._deselect()

    def _read_reg(self, reg):
        cmd = CMD_RREG | (reg << 2)
        self._select()
        self.spi.write(bytes([cmd]))
        response = self.spi.read(1)
        self._deselect()
        return response[0]

    def reset(self):
        self._send_command(CMD_RESET)
        utime.sleep_ms(2)

    def start_sync(self):
        self._send_command(CMD_START_SYNC)

    def power_down(self):
        self._send_command(CMD_POWERDOWN)

    def read_adc_raw(self):
        self._select()
        raw_data = self.spi.read(3)
        self._deselect()
        
        if raw_data is None:
            return None

        value_24bit = (raw_data[0] << 16) | (raw_data[1] << 8) | raw_data[2]
        if (value_24bit & 0x800000):
            value_24bit -= 0x1000000

        return value_24bit

    def configure(self, gain, pga_bypass, sample_rate_sps, idac_ua):
        mux_setting = 0b0000 
        gain_map = {1: 0b000, 2: 0b001, 4: 0b010, 8: 0b011, 16: 0b100, 32: 0b101, 64: 0b110, 128: 0b111}
        gain_setting = gain_map.get(gain, 0b010)

        pga_bypass_bit = 0b0
        if pga_bypass:
            if gain not in [1, 2, 4]:
                gain_setting = gain_map[4]
            pga_bypass_bit = 0b1
        
        reg0 = (mux_setting << 4) | (gain_setting << 1) | pga_bypass_bit
        self._write_reg(REG_CONFIG_0, reg0)

        rate_map = {20: 0b000, 45: 0b001, 90: 0b010, 175: 0b011, 330: 0b100, 600: 0b101, 1000: 0b110}
        dr_setting = rate_map.get(sample_rate_sps, 0b000)
        mode_setting = 0b00
        cm_setting = 0b1

        reg1 = (dr_setting << 5) | (mode_setting << 3) | (cm_setting << 2)
        self._write_reg(REG_CONFIG_1, reg1)

        vref_setting = 0b01
        fir_setting = 0b01
        idac_map = {0: 0b000, 10: 0b001, 50: 0b010, 100: 0b011, 250: 0b100, 500: 0b101, 1000: 0b110, 1500: 0b111}
        idac_setting = idac_map.get(idac_ua, 0b000)

        reg2 = (vref_setting << 6) | (fir_setting << 4) | idac_setting
        self._write_reg(REG_CONFIG_2, reg2)

        i1mux_setting = 0b100
        i2mux_setting = 0b000

        reg3 = (i1mux_setting << 5) | (i2mux_setting << 2)
        self._write_reg(REG_CONFIG_3, reg3)

    def check_communication(self):
        try:
            original_value = self._read_reg(REG_CONFIG_2)
            test_value = original_value ^ 0x0A
            self._write_reg(REG_CONFIG_2, test_value)
            read_back = self._read_reg(REG_CONFIG_2)
            self._write_reg(REG_CONFIG_2, original_value)
            return test_value == read_back
        except Exception:
            return False