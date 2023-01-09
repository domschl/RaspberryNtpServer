#!/usr/bin/python

import time
import datetime
import subprocess
import gpsd

from i2c_lcd import LcdDisplay

# from button import Button


def get_sats(host="localhost"):
    n = 0
    try:
        gpsd.connect(host)
        n = gpsd.get_current().sats_valid
        ss = "00" + str(n)
        return "[" + ss[-2:] + "]"
    except:
        pass
    return "[--]"


def exec(cmd):
    ret = []
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1
    )
    for line in p.stdout:
        ret.append(line.decode("utf-8").strip())
    p.wait()
    if p.returncode != 0:
        cm = ""
        for c in cmd:
            cm = cm + c + " "
        print("Warning: " + cm + "failed: " + str(p.returncode))
    return ret


def ntp_offset():
    cmd = ["chronyc", "tracking"]
    ret = exec(cmd)
    for line in ret:
        pars = line.split(":", 1)
        if len(pars) == 2:
            if pars[0].strip() == "System time":
                sub_pars = pars[1].strip().split(" ")
                if len(sub_pars) > 2:
                    val = float(sub_pars[0])
                    if "slow" == sub_pars[2]:
                        val = -1.0 * val
                    return "NTP: {:+12.9f}sec".format(val)
    return None


def get_src():
    cmd = ["chronyc", "sources"]
    ret = exec(cmd)
    pps_locked = "-"
    locked = "-"
    src = "--"
    dev = "--"
    for line in ret:
        if "#* PPS" in line:
            locked = "*"
            src = "PPS"
            # #* PPS0                          0   4   377    22   +271ns[ +385ns] +
            try:
                dev = line[50:59].strip()
            except:
                dev = "--"
        else:
            if "^*" in line:
                try:
                    src = line[3:33].strip()
                except:
                    src = "--"
                locked = "*"
                try:
                    dev = line[50:59].strip()
                except:
                    dev = "--"
    srcstr = f"L[{locked}] {src}"
    devstr = dev
    return (srcstr, devstr)


def main_loop():
    last_time = ""
    last_offset = ""
    select_state = 0
    select_states = 2
    trigger_time = 0
    main_state = 0
    main_states = 2

    def select_button():
        nonlocal select_state
        nonlocal select_states
        nonlocal trigger_time
        trigger_time = time.time()
        select_state = (select_state + 1) % select_states

    def main_button():
        nonlocal main_state
        nonlocal main_states
        nonlocal trigger_time
        trigger_time = time.time()
        main_state = (main_state + 1) % main_states

    # bt = Button([(27, "blue", select_button), (22, "black", main_button)])

    lcd = LcdDisplay()
    while True:
        time_str = time.strftime("%Y-%m-%d  %H:%M:%S")
        if time_str != last_time:
            h = datetime.datetime.now().hour
            if (h > 20 or h < 7) and time.time() - trigger_time > 10:
                lcd.set_backlight(False)
            else:
                lcd.set_backlight(True)
            last_time = time_str
            if select_state == 0:
                lcd.print_row(0, time_str)
            else:
                if time.time() - trigger_time > 10:
                    select_state = 0
                lcd.print_row(0, "Select 1")
            offs = ntp_offset()
            if offs is not None and offs != last_offset:
                last_offset = offs
                lcd.print_row(1, offs)
            sats = get_sats()
            source_str, dev_str = get_src()
            sat_str = f"SATS {sats}    {dev_str.rjust(7,' ')}"
            lcd.print_row(2, source_str)
            lcd.print_row(3, sat_str)
        time.sleep(0.05)


main_loop()
