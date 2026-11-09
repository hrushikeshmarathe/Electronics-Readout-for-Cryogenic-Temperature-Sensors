# =================================================================================
# config.py - Hardware Settings & Pin Mappings
# Author -Hrushikesh.
# =================================================================================
CHANNEL_ACTIVE = [True, True, True, True, True, False, False, False] 
MODULE_NAMES = ["A", "B", "C", "D", "E", "F", "G", "H"]

# Reference Resistors and Gains
RREF_LIST = [2000, 5000, 5000, 10000, 5000, 100000, 100000, 100000] 
GAIN_LIST  = [16, 32, 4, 8, 1, 1, 1, 1] 

# Current Settings (uA)
IDAC_STATIC_UA = [500, 250, 250, 100, 0, 10, 10, 10]
TIP_DUAL_CURRENTS = [500, 250] # High/Low for TIP32C

# Timing and SPI
ADS_SAMPLE_RATE_SPS = 20 
SPI_BAUDRATE = 1000000 
SPI_BUS = 0
SPI_PINS = {"sck": 18, "mosi": 19, "miso": 16}

# Software Pin Mapping
ADS_CS_PINS   = [27, 22, 20, 7, 9, 11, 13, 15] 
ADS_DRDY_PINS = [28, 26, 21, 6, 8, 10, 12, 14]

STARTUP_DELAY_SEC = 2 
REPORT_INTERVAL_SEC = 5