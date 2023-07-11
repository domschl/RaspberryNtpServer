# Simple 4x20 LCD display for Raspberry Pi NTP Server

The display shows current NTP time and date, the PPS signal locking state, the offset to the NTP time, the number of satellites that are currently used, and, if no PPS lock is available, alternatively the address of the time server used.

If you see an address of some time server, PPS lock is not (yet) working.

Note: Review [this line](https://github.com/domschl/RaspberryNtpServer/blob/c42218ec63e34c5db5b6ec6da0f1ef79b525e863/src/chronotron.py#L119) which switches off the backlight during night-time.

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
or if you are using a very old Raspberry that still uses `sm_bus=0`, you need to adapt [this line](https://github.com/domschl/RaspberryNtpServer/blob/2a3551de7954e77f23b2a313be044d94047ab4d5/src/chronotron.py#L114):

```python
lcd = LcdDisplay(sm_bus=1, i2c_addr=0x27, cols=20, rows=4)
```

Old Raspis use `sm_bus=0`.

> **Note:** if the LCD screen looks inverted or too faint, use the potentiometer on the adapter-board to adjust the contrast.

## Software requirements

This project uses Martijn Braam's python gpsd driver <https://github.com/MartijnBraam/gpsd-py3> (minimum version `0.3.0`, and `smbus` (already available on some distributions).

Please check first, if either of those packages are available via your linux package manager. 

If not, they can be installed with:

Install with:

```bash
# You need at least version 0.3.0 of gpsd-py3:
pip install gpsd-py3
# If smbus is not available, install with:
pip install smbus
# Note: if the chronotron.service runs as root (default), you need instead install as sudo:
sudo pip install gpsd-py3 smbus
# (This is not recommended and may generate conflicts with your package manager, so first check, if
# either gpsd-py3 or smbus are available as python packages with your default package manager!)
```

Currently, a number of distributions is changing to Python 3.11. After each Python-update, you'll need to
reinstall the required packages! 

If `chronotron` does not start, check with `sudo systemctl status chronotron`: It will show if it can't 
import a required packages.

## Installation

Copy the python files to `/opt/chronotron`, and the `service` file to `/etc/systemd/system`.
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

Oct 25 14:44:17 chronotron systemd[1]: Started Display chrony statistics on 4x20 LCD.
```

## Notes on the display-information

<img src="https://github.com/domschl/RaspberryNtpServer/blob/main/images/ntp-lcd-notes.jpg" align="right" width="600" />

1. Time and date according to NTP
2. Shows the output of `chronyc tracking`, entry `system time`, the time difference to the NTP reference (see below for further information).
3. `L[ ]` no lock, `L[*]` lock. A lock (`*`) indicates that time synchronisation is established, either via remote NTP servers or GPS + PPS
4. `PPS` signales that the lock is active using GPS and PPS, the server is in high-precision stratum 1 mode. If instead a hostname is displayed, then PPS is NOT active, and the network is used for time synchronisation, resulting in lower precision.
5. `SAT[nn]`, `nn` is the number of satellites that are actively used for time synchronisation.
6. Shows output of `chronyc sources`, the last column of the currently active source, which is the estimated error (see below for further information)

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

## Notes:

The `chronotron.py` systemd service checks periodically `chronyc` for NTP statistics (`chronyc` must be in the path!), and uses `gpsd` for the GPS statistics (number of satellites).

- `button.py` is currently not used.
- `i2c_lcd.py` is a buffered driver for the LCD display.
- `chronotron.service` is the systemd service file.


