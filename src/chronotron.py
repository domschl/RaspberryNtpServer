#!/usr/bin/python

import time
from datetime import datetime
import subprocess
import gps  # from python3-gps  # pyright:ignore[reportMissingTypeStubs]
import logging
import threading
from typing import Any, cast

from i2c_lcd import LcdDisplay
# from button import Button

#------- CONFIGURATION PARAMETERS -----------------------
# start_time and end_time switch the display off during night-time.
# Set both to None for always-on
start_time:str|None = "07:00"
end_time:str|None = "21:00"
# I2C address of the display, usually between 0x20 (Adafruit default) and 0x27 (all others)
i2c_address_display:int = 0x27
# Set to True for Adafruit I2C adapter which uses MCP23008 chip. Enables Adafruit specific connections
# Set to False for all others which use PCF8574 
adafruit_i2c_hardware:bool = False
# Display time as UTC
display_utc_time:bool = False
# LCD display update timing: False: default, slow according to spec,
# True: update faster, low latency, exceeds specs. Set to False on display problems!
lcd_latency_overdrive:bool = True
# ---------------------------------------------------------

# Global Variables for GPS data from background thread
gps_lock: threading.Lock = threading.Lock()
gps_mode: int|None = None
gps_sats_used: int|None = None
gps_sats: int|None = None

def is_current_time_in_interval(start_time_str:str, end_time_str:str):
    # Get the current local time
    current_time = datetime.now().time()
    # Parse start and end times from strings
    start_time = datetime.strptime(start_time_str, "%H:%M").time()
    end_time = datetime.strptime(end_time_str, "%H:%M").time()
    # Check if the interval spans across midnight
    if start_time > end_time:
        return current_time >= start_time or current_time < end_time
    else:
        return start_time <= current_time <= end_time


def exec_cmd(log:logging.Logger, cmd:list[str]) -> list[str]:
    ret:list[str] = []
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1
    )
    if p.stdout is None:
        log.error(f"Failed to execute {cmd}")
        return []
    for line in p.stdout:
        ret.append(line.decode("utf-8").strip())
    _ = p.wait()
    if p.returncode != 0:
        cm = ""
        for c in cmd:
            cm = cm + c + " "
        print("Warning: " + cm + "failed: " + str(p.returncode))
    return ret


def get_statistics(log:logging.Logger, _host:str="localhost") -> dict[str, Any]:  # pyright:ignore[reportExplicitAny]
    # Get number of active satellites from gpsd
    n = 0
    stats: dict[str, Any] = {}  # pyright:ignore[reportExplicitAny]
    with gps_lock:
        stats["mode"] = gps_mode
        stats["sats"] = gps_sats
        stats["sats_used"] = gps_sats_used

    # Get chrony tracking information
    cmd = ["chronyc", "tracking"]
    ret = exec_cmd(log, cmd)
    stats["stratum"] = None
    stats["system_time_offset"] = None
    for line in ret:
        pars = line.split(":", 1)
        if len(pars) == 2:
            parm = pars[0].strip()
            if parm == "System time":
                sub_pars = pars[1].strip().split(" ")
                if len(sub_pars) > 2:
                    val = float(sub_pars[0])
                    if "slow" == sub_pars[2]:
                        val = -1.0 * val
                    stats["system_time_offset"] = val
            elif parm == "Stratum":
                try:
                    n = int(pars[1])
                    stats["stratum"] = n
                except:
                    stats["stratum"] = None

    # Get current time source
    cmd = ["chronyc", "sources"]
    ret = exec_cmd(log, cmd)
    stats["is_locked"] = False
    stats["is_pps"] = False
    stats["source"] = None
    stats["adjusted_offset"] = None
    for line in ret:
        if "#* PPS" in line:
            stats["is_locked"] = True
            stats["is_pps"] = True
            stats["source"] = "PPS"
            # #* PPS0                          0   4   377    22   +271ns[ +385ns] +
            try:
                stats["adjusted_offset"] = line[50:59].strip()
            except:
                pass
        else:
            if "^*" in line:
                stats["is_locked"] = True
                stats["is_pps"] = False
                try:
                    stats["source"] = line[3:33].strip()
                except:
                    pass
                try:
                    stats["adjusted_offset"] = line[50:59].strip()
                except:
                    pass

    return stats


def main_loop():
    last_time = ""
    last_offset = ""
    select_state = 0
    select_states = 2
    trigger_time = 0
    main_state = 0
    main_states = 2
    old_lock = False
    old_pps = False
    old_stratum = None
    old_src = None
    global start_time
    global end_time
    global i2c_address_display
    global adafruit_i2c_hardware
    global display_utc_time
    global lcd_latency_overdrive

    version = "2.0.0"

    # Time interval for backlight, set to None for permanent backlight:

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("Chronotron")
    log.setLevel("INFO")
    log.info(f"Chronotron version {version} starting")

    def select_button():  # pyright:ignore[reportUnusedFunction]
        nonlocal select_state
        nonlocal select_states
        nonlocal trigger_time
        trigger_time = time.time()
        select_state = (select_state + 1) % select_states

    def main_button():  # pyright:ignore[reportUnusedFunction]
        nonlocal main_state
        nonlocal main_states
        nonlocal trigger_time
        trigger_time = time.time()
        main_state = (main_state + 1) % main_states

    # bt = Button([(27, "blue", select_button), (22, "black", main_button)])

    # See beginning of file for configuration of i2c parameters
    lcd = LcdDisplay(sm_bus=1, i2c_addr=i2c_address_display, cols=20, rows=4, ada=adafruit_i2c_hardware, fast_lcd=lcd_latency_overdrive)
    if lcd.active is False:
        log.error("Failed to open display, exiting...")
        exit(-1)

    while True:
        if display_utc_time is True:
            time_str: str = time.strftime("%Y-%m-%d  %H:%M:%S", time.gmtime())
        else:
            time_str = time.strftime("%Y-%m-%d  %H:%M:%S")
        if time_str != last_time:
            if (
                start_time is None
                or end_time is None
                or is_current_time_in_interval(start_time, end_time)
                or start_time == end_time
            ):
                lcd.set_backlight(True)
            else:
                lcd.set_backlight(False)
            last_time = time_str
            stats = get_statistics(log)

            if stats["is_locked"] != old_lock:
                old_lock:bool = cast(bool, stats["is_locked"])
                if old_lock is True:
                    log.info("Chrony aquired lock to time source")

            if old_src != stats["source"]:
                old_src:str|None = cast(str|None, stats["source"])
                if old_src is None:
                    src = "None"
                else:
                    src = old_src
                log.info(f"Chrony receiving time source from {src}")

            if old_stratum != stats["stratum"]:
                old_stratum:str|None = cast(str|None, stats["stratum"])
                if old_stratum is None:
                    strat:str = "?"
                else:
                    strat = old_stratum
                log.info(f"Chrony stratum level changed to {strat}")

            if old_pps != stats["is_pps"]:
                old_pps:bool = cast(bool, stats["is_pps"])
                if old_pps is True:
                    log.info("Chrony locked to high precision GPS PPS signal")
                else:
                    log.info("Chrony lost PPS signal")

            # if select_state == 0:
            #     lcd.print_row(0, time_str)
            # else:
            #     if time.time() - trigger_time > 10:
            #         select_state = 0
            #     lcd.print_row(0, "Select 1")

            offset:str|None = cast(str|None, stats["system_time_offset"])
            offs = "            "
            if offset is not None:
                if stats["stratum"] is None:
                    offs = "S[?]"
                else:
                    offs = f"S[{stats['stratum']}]"
                offs += " {:+12.9f}sec".format(offset)
                if offs != last_offset:
                    last_offset = offs

            if stats["sats"] is None:
                sats = "--"
            else:
                sats = f"{stats['sats']:02}"
            if stats["sats_used"] is None:
                sats_used = "--"
            else:
                sats_used = f"{stats['sats_used']:02}"
            if stats["mode"] is None:
                mode = "-"
            else:
                mode = f"{stats['mode']:01}"
            if stats["is_locked"]:
                source_str = "L[*] "
            else:
                source_str = "L[ ] "
            if stats["source"] is None:
                source_str += "                    "
            else:
                source_str += cast(str, stats["source"])
            if stats["adjusted_offset"] is None:
                dev_str = "       "
            else:
                dev_str = f"{stats['adjusted_offset']:>7}"
            last_str = f"F[{mode}] {sats_used}/{sats}   {dev_str}"  
            lcd.print_row(0, time_str)
            lcd.print_row(1, offs)
            lcd.print_row(2, source_str)
            lcd.print_row(3, last_str)
        time.sleep(0.05)

def gps_client():
    global gps_mode
    global gps_sats
    global gps_sats_used
    session:gps.gps = gps.gps(mode=gps.WATCH_ENABLE)
    try:
        while 0 == session.read():
            if not (gps.MODE_SET & session.valid):
                continue
            with gps_lock:
                gps_mode = session.fix.mode
                gps_sats = len(session.satellites)  # pyright:ignore[reportUnknownArgumentType, reportUnknownMemberType]
                gps_sats_used = session.satellites_used
    finally:
        session.close()


gps_thread = threading.Thread(target = gps_client)
gps_thread.daemon = True
gps_thread.start()

main_loop()
