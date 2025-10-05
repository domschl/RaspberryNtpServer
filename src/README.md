# Simple 4x20 LCD display for Raspberry Pi NTP Server

The display shows current NTP time and date, the PPS signal locking state, Stratum level, the offset to the NTP time, the number of satellites that are currently used, and, if no PPS lock is available, alternatively the address of the time server used.

If you see an address of some time server, PPS lock is not (yet) working.

Note: the main script `chronotron.py` defines a `start_time` and an `end_time`, used to switch on the LCD backlight (at `start_time`) and switch it off at (`end_time`). If you want permanent backlight, simply set `start_time` and `end_time` to `None`.

## Hardware requirements

- Display: HD44780 2004 LCD Display 4x20 characters with I2C interface (address 0x27 is assumed by the code), use for example:
  - Adafruit [LCD 4x20](https://www.adafruit.com/product/198) and [I2C Adapter](https://www.adafruit.com/product/292), description: (https://learn.adafruit.com/i2c-spi-lcd-backpack). Advantage: Stemma QT adapter (QWIIC) that can be also added to [Raspberry PI](https://www.adafruit.com/product/4463#:~:text=The%20SparkFun%20Qwiic%20or%20Stemma%20QT%20SHIM%20for,QT%20or%20Qwiic%29%20connector%20to%20your%20Raspberry%20Pi.) for clean cabling.
  - Amazon kit [sunfounder kit](https://www.amazon.com/SunFounder-Serial-Module-Arduino-Mega2560/dp/B01GPUMP9C)
  - AliExpress kit [TZT Five Star](https://de.aliexpress.com/item/1005001679675215.html

Make sure that I2C is enable on your Raspberry PI.

<img src="https://github.com/domschl/RaspberryNtpServer/blob/main/images/gps-with-pps-and-i2c-lcd.jpg" width="600" />

Connect the LCD Display the GND, 5V and SDA and SCL pins or the Raspberry PI.

> **Note:** Raspberry PI uses 3.3V logic, and the LCD Display is connected to 5V. This _should_ not be a problem, since the lcd just receives from Raspberry PI. If you want to be on the safe side, either try to power the LCD with **3.3V**, or use a **logic-level-converter**.

> **Note:** if your display uses a different address than `0x27`, 
or if you are using a very old Raspberry that still uses `sm_bus=0`, you need to adapt:

```python
lcd = LcdDisplay(sm_bus=1, i2c_addr=0x27, cols=20, rows=4)
```

Old Raspis use `sm_bus=0`.

> **Note:** if the LCD screen looks inverted or too faint, or no output is visible at all, use the potentiometer on the adapter-board to adjust the contrast.

## Software requirements

> **Note:** Standard Raspberry Pi OS (tested with 'Bookworm') is recommended and used below

This project uses `python3-gps` and `python3-smbus` (already available on some distributions).

### Python dependencies

Install the python GPS library and smbus, if they are not already installed on your system:

```bash
sudo apt install python3-gps python3-smbus
```

Note: Previous versions of this software relied on `gps-py3`, which was not included in Raspberry Pi OS python libraries and therefore required a venv. This is no longer required. See [PR9](https://github.com/domschl/RaspberryNtpServer/pull/19) for more details on the changes. If you previously used a venv, you might need to update your systemd service file and remove the venv directories.

Note: Trixie requires update to the new dependencies, otherwise GPS satellite status is broken!

## Installation of chronotron software

0. Clone the repository

```bash
git clone https://github.com/domschl/RaspberryNtpServer
cd RaspberryNtpServer/src
```

2. Copy the python files to `/opt/chronotron`:

```bash
mkdir /opt/chronotron
chown -R $USER:$USER /opt/chronotron
# Now copy:
cp button.py chronotron.py i2c_lcd.py /opt/chronotron
```

2. Install the systemd service

```bash
sudo cp chronotron.service /etc/systemd/system
```

Enable the systemd server `chronotron` with:

```bash
sudo systemctl enable chronotron
sudo systemctl start chronotron
```

Check, if everthing works:

```bash
sudo systemctl status chronotron
```

If everything worked, the output should be something like:

```
chronotron.service - Display chrony statistics on 4x20 LCD
     Loaded: loaded (/etc/systemd/system/chronotron.service; enabled; preset: disabled)
     Active: active (running) since Tue 2022-10-25 14:44:17 CEST; 2 months 15 days ago
   Main PID: 370 (chronotron.py)
      Tasks: 2 (limit: 3921)
        CPU: 3d 5h 34min 24.354s
     CGroup: /system.slice/chronotron.service
             └─370 /usr/bin/python /opt/chronotron/chronotron.py

Dec 21 09:38:37 chronotron systemd[1]: Started chronotron.service - Display chrony statistics on 4x20 LCD.
Dec 21 09:38:37 chronotron chronotron.py[2628]: INFO:Chronotron:Chronotron version 2.0.0 starting
Dec 21 09:38:37 chronotron chronotron.py[2628]: INFO:Chronotron:Chrony aquired lock to time source
Dec 21 09:38:37 chronotron chronotron.py[2628]: INFO:Chronotron:Chrony receiving time source from PPS
Dec 21 09:38:37 chronotron chronotron.py[2628]: INFO:Chronotron:Chrony stratum level changed to 1
Dec 21 09:38:37 chronotron chronotron.py[2628]: INFO:Chronotron:Chrony locked to high precision GPS PPS signal
```

## Notes on the display-information

<img src="https://github.com/domschl/RaspberryNtpServer/blob/main/images/ntp-lcd-notes.jpg" align="right" width="600" />

1. Time and date according to NTP
2. The current stratum level is displayed as `S[1]` for stratum level 1. 
3. Shows the output of `chronyc tracking`, entry `system time`, the time difference to the NTP reference (see below for further information).
4. `L[ ]` no lock, `L[*]` lock. A lock (`*`) indicates that time synchronisation is established, either via remote NTP servers or GPS + PPS
5. `PPS` signales that the lock is active using GPS and PPS, the server is in high-precision stratum 1 mode. If instead a hostname is displayed, then PPS is NOT active, and the network is used for time synchronisation, resulting in lower precision.
6. **New** `F[n]`, `n` is the GPS fix type: '-': unknown, 1: no fix, 2: 2D fix, 3: 3D fix.
7. **New** `nn/mm`, nn: used satellites, mm: total seen satellites, including unused ones.
8. Shows output of `chronyc sources`, the last column, "adjusted offset", of the currently active source, which is the estimated error (see below for further information)

### Further information and references

#### `chronyc tracking`

Marked with >>>nnnn.nnnn<<< is the information displayed at (2).
Here, the system is 0.000000100 seconds faster than NTP ref.

```
chronyc tracking
# sample output:
Reference ID    : 50505300 (PPS)
Stratum         : 1
Ref time (UTC)  : Tue Jul 11 07:22:07 2023
System time     : >>>0.000000100<<< seconds fast of NTP time
Last offset     : +0.000000030 seconds
RMS offset      : 0.000010080 seconds
Frequency       : 10.392 ppm fast
Residual freq   : -0.006 ppm
Skew            : 0.005 ppm
Root delay      : 0.000000001 seconds
Root dispersion : 0.000384213 seconds
Update interval : 16.0 seconds
Leap status     : Normal
```

#### `chronyc sources`

Marked with `>>>nnn<<<` is the information displayed at (6).
Here the estimated error of the PPS signal is 591ns

```
chronyc sources -v
# sample output with explanation (-v paramenter):
  .-- Source mode  '^' = server, '=' = peer, '#' = local clock.
 / .- Source state '*' = current best, '+' = combined, '-' = not combined,
| /             'x' = may be in error, '~' = too variable, '?' = unusable.
||                                                 .- xxxx [ yyyy ] +/- zzzz
||      Reachability register (octal) -.           |  xxxx = adjusted offset,
||      Log2(Polling interval) --.      |          |  yyyy = measured offset,
||                                \     |          |  zzzz = estimated error.
||                                 |    |           \
MS Name/IP address         Stratum Poll Reach LastRx Last sample               
===============================================================================
#? GPS                           0   4     0   780    +43ms[  +43ms] +/-  200ms
#* PPS                           0   4     0   782   +186ns[ +217ns] +/-  >>>591ns<<<
^? 2003:2:2:140:194:25:134:>     2  10   377   340   +141us[ +141us] +/-   17ms
^? time.ontobi.com               2  10   377   264   +139us[ +139us] +/-   13ms
^? bblock.dev                    2  10   377   631   +209us[ +209us] +/-   12ms
^? time01.nevondo.com            2  10   377   721   +181us[ +181us] +/-   28ms
^? static.33.250.47.78.clie>     3  10   377  1168   -191us[ -213us] +/-   15ms```
```

#### References

- <https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/configuring_basic_system_settings/using-chrony_configuring-basic-system-settings>
- [chronyc documentation](https://github.com/mlichvar/chrony/blob/master/doc/chronyc.adoc)

## Notes:

The `chronotron.py` systemd service checks periodically `chronyc` for NTP statistics (`chronyc` must be in the path!), and uses `gpsd` for the GPS statistics (number of satellites).

- `button.py` is currently not used.
- `i2c_lcd.py` is a buffered driver for the LCD display.
- `chronotron.service` is the systemd service file.

## History

- 2025-10-05: Update of dependencies, Trixie support (thanks [rglidden](https://github.com/rglidden))
