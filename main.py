# =================================================================================
# main.py - Microcontroller Acquisition Firmware
# Developed and structured with assistance from ChatGPT.
# =================================================================================
import utime
from machine import Pin, SPI
import config
from ads1220 import ADS1220

def run_acquisition():
    spi = SPI(config.SPI_BUS, baudrate=config.SPI_BAUDRATE, polarity=0, phase=1,
              sck=Pin(config.SPI_PINS["sck"]), mosi=Pin(config.SPI_PINS["mosi"]),
              miso=Pin(config.SPI_PINS["miso"]))

    active_channels = []
    for i in range(8):
        if config.CHANNEL_ACTIVE[i]:
            adc = ADS1220(spi, config.ADS_CS_PINS[i], config.ADS_DRDY_PINS[i], config.MODULE_NAMES[i])
            if adc.check_communication():
                active_channels.append({"adc": adc, "name": config.MODULE_NAMES[i], "idx": i})

    utime.sleep(config.STARTUP_DELAY_SEC)

    while True:
        results_low = {}
        # Phase 1: All Sensors (Module E at 50uA)
        for ch in active_channels:
            i = ch["idx"]
            curr = config.TIP_DUAL_CURRENTS[1] if ch["name"] == "E" else config.IDAC_STATIC_UA[i]
            
            ch["adc"].configure(gain=config.GAIN_LIST[i], pga_bypass=False, 
                               sample_rate_sps=config.ADS_SAMPLE_RATE_SPS, idac_ua=curr)
            
            if ch["name"] == "E":
                reg2 = ch["adc"]._read_reg(0x02)
                ch["adc"]._write_reg(0x02, reg2 & 0x3F)

        utime.sleep_ms(250)
        for ch in active_channels:
            ch["adc"].start_sync()
            if ch["adc"]._wait_for_drdy():
                results_low[ch["name"]] = ch["adc"].read_adc_raw()

        # Phase 2: TIP32C at 100uA
        tip_high = 0
        e_mod = next((c for c in active_channels if c["name"] == "E"), None)
        if e_mod:
            e_mod["adc"].configure(gain=config.GAIN_LIST[4], pga_bypass=False, 
                                  sample_rate_sps=config.ADS_SAMPLE_RATE_SPS, 
                                  idac_ua=config.TIP_DUAL_CURRENTS[0])
            
            reg2 = e_mod["adc"]._read_reg(0x02)
            e_mod["adc"]._write_reg(0x02, reg2 & 0x3F)
            
            utime.sleep_ms(150)
            e_mod["adc"].start_sync()
            if e_mod["adc"]._wait_for_drdy():
                tip_high = e_mod["adc"].read_adc_raw()

        out = "DATA"
        for name in "ABCDEFGH":
            if name not in results_low: continue
            raw1 = results_low[name]
            if name == "E":
                out += f"|E|{tip_high}|{raw1}"
            else:
                out += f"|{name}|{raw1}"
        print(out)
        utime.sleep(config.REPORT_INTERVAL_SEC)

if __name__ == "__main__":
    run_acquisition()