# Simple 4x20 LCD display for Raspberry Pi NTP Server

The display shows current NTP time and date, the PPS signal locking state, the offset to the NTP time, the number of satellites that are currently used, and, if no PPS lock is available, alternatively the address of the time server used.

If you see an address of some time server, PPS lock is not (yet) working.

## Hardware requirements

- Display: HD44780 2004 LCD Display 4x20 characters with I2C interface (address 0x27 is assumed by the code)

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

This project uses Martijn Braam's python gpsd driver <https://github.com/MartijnBraam/gpsd-py3>. Install with:

```bash
pip install gpsd-py3
```

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

## Notes:

The `chronotron.py` systemd service checks periodically `chronyc` for NTP statistics (`chronyc` must be in the path!), and uses `gpsd` for the GPS statistics (number of satellites).

- `button.py` is currently not used.
- `i2c_lcd.py` is a buffered driver for the LCD display.
- `chronotron.service` is the systemd service file.

