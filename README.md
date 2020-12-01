# RaspberryNtpServer

Stratum-1 NTP time server with Raspberry Pi, GPS and Chrony: how to build a precision time server.

## Requirements - Hardware

* Raspberry Pi

While you can use any model of Raspberry Pi to implement a Stratum-1 NTP server with GPS, the best choice
is Raspberry Pi 4, due to 1Gbit network interface and fast hardware for lowest possible latencies

* GPS module

  * Adafruit GPS hat: [Adafruit ultimate GPS hat](https://www.adafruit.com/product/2324)
  * GPS module with serial output and PPS signal: [Adafruit GPS module](https://www.adafruit.com/product/746)
  * GSP module with USB, SMA connector and PPS: [Keystudio GPS module](https://wiki.keyestudio.com/KS0319_keyestudio_GPS_Module)
  * Cheap NEO6 modules: [Aliexpress NEO6](https://www.aliexpress.com/item/32800500501.html?spm=a2g0o.productlist.0.0.2eae3298PesRP8&algo_pvid=89486c29-bfb7-414c-a88d-81a9972f8080&algo_expid=89486c29-bfb7-414c-a88d-81a9972f8080-1&btsid=2100bdd516068129046292696e617f&ws_ab_test=searchweb0_0,searchweb201602_,searchweb201603_)

<img src="https://github.com/domschl/RaspberryNtpServer/blob/main/images/antenna.jpg" align="right" width="200" height="200" />
  
* Active GPS antenna

When selecting a GPS antenna, make sure to get an active antenna with 3-5V power input. Passive antennas often look similar, but reception quality is far worse at similar cost.

### Antenna adapters

Some boards have uFL antenna connectors, whereas almost all external active antennas use SMA, so you might need an uFL to SMA adapter:

* [Adafruit uFL to SMA adapter](https://www.adafruit.com/product/851)
* [Various uFL to SMA adapters](https://www.aliexpress.com/item/4000166668788.html?spm=a2g0o.productlist.0.0.2c386be8fN3oCH&algo_pvid=6da3d77b-f49d-4e6b-8dba-c9c7446cd7b4&algo_expid=6da3d77b-f49d-4e6b-8dba-c9c7446cd7b4-1&btsid=2100bddf16068135762546912e571d&ws_ab_test=searchweb0_0,searchweb201602_,searchweb201603_)

### To check

#### Is external antenna selected?

Some GPS modules come with a passive antenna and and external antenna plug. Check the description of your board to find out what's needed to use the external antenna. The Keystudio GPS module listed above for example, requires the removal of capacitor C2 in order to activate the external antenna.

<img src="https://github.com/domschl/RaspberryNtpServer/blob/main/images/gps-with-pps.jpg" align="right" width="300" height="300" />

#### PPS signal easily accessible?

Make sure your GPS module has an accessible output for the PPS signal. (Red mark on image)

If you are using a GPS Hat that plugs into the Raspberry IO connector, check the documentation to which GPIO pin the PPS signal is connected. Adafruit's Hat uses GPIO 4.

#### USB vs serial

When not using a Pi Hat, decide between USB- and serial connection.

USB-Connection:
* No extra cables for Vcc, GND, Tx, Rx are needed: both powersupply and communication goes over USB.
* No modification of Raspberry's serial console is needed, easier software installation
* Example: [Keystudio GPS module](https://wiki.keyestudio.com/KS0319_keyestudio_GPS_Module)

Serial connection:
* Usually cheaper, if a module is purchased.
* All Pi Hats use serial connections.
* Raspberry serial console needs to be disabled
* Sometimes, bluetooth needs to be disabled.

### Recommended setup

* Raspberry PI 4
* Either GPS hat (e.g. adafruit ultimate GPS hat + uFL to SMA-Adapter) or USB-GPS-Module with PPS output (e.g. keystudio gps module)
* Active GPS antenna with SMA connector and 3-5V

### Most cost-efficient setup

NEO6 GPS modules are available at very low cost (1-2Eur) at chinese dealers (Aliexpress) and are perfectly usable as long as they allow connecting an active external GPS antenna and provide a PPS signal.

<img src="https://github.com/domschl/RaspberryNtpServer/blob/main/images/gps-wiring.png" width="600" height="400" />

_Typical wiring between GPS module and Raspberry Pi connector._

Note: If your GPS module is connected via USB, you only need to connect the PPS connector on the GPS module to GPIO 4 on the Raspberry. Power (Vin), Gnd and Tx/Rx are handled via USB.

### Test

**Before you continue with software:** At this point, the GPS module should be connected to the Raspberry Pi and the active antenna. Power up the Raspberry Pi, and check that the GPS module receives the GPS signal (the antenna must have unhindered access to the open sky, it does *not* work indoors!).

If reception is ok, a led ("FIX" or "PPS") should start blinking on your GPS module.

### More information

* Adafruit has an excellent [GPS guide](https://learn.adafruit.com/adafruit-ultimate-gps) for their ultimate GPS module.

## Software

### Raspberry Linux preparations

#### Serial port console (skip, if connected via USB)

If your GPS board is connected via serial connection (Rx/Tx), you need to "free up" Raspberry's serial port, which by default is used to connect a serial (debug) console. We need to disable that console to prevent it from interferring with the GPS module. 

This is *not* needed, if your module is connected via USB.

How to disable the serial console on Raspberry variies greatly depending on hardware revision and Linux flavour used. A few examples:

##### For Raspberry Pi 4 with Raspberry Pi OS:

1. Start raspi-config: `sudo raspi-config`.
2. Select option 3 - Interface Options.
3. Select option P6 - Serial Port.
4. At the prompt Would you like a login shell to be accessible over serial? answer 'No'
5. At the prompt Would you like the serial port hardware to be enabled? answer 'Yes'
6. Exit raspi-config and reboot the Pi for changes to take effect.

See ["Disable Linux serial console"](https://www.raspberrypi.org/documentation/configuration/uart.md#:~:text=Disable%20Linux%20serial%20console&text=This%20can%20be%20done%20by,Select%20option%20P6%20%2D%20Serial%20Port) at raspberrypi.org.

Older versions of `raspi-config` hide the same serial options under "Advanced options"

##### Other linux distributions and manual configuration

1. Edit `/boot/cmdline.txt` and remove references to the serial port `ttyAMA0`. E.g. remove: `console=ttyAMA0,115200` and (if present) `kgdboc=ttyAMA0,115200`.
2. Disable getty on serial port. `sudo systemctl disable getty@ttyAMA0` or, on some Linux distris: `sudo systemctl disable serial-getty@ttyAMA0`
3. Enable uart in `/boot/config.txt`, add a line `enable_uart=1`
4. For RPI 3 or later disable bluetooth via overlay, add another line to `/boot/config.txt`: `dtoverlay=pi3-disable-bt-overlay`. In some versions, this is done by *enabling* the overlay `dtoverlay=pi3-miniuart-bt` which disables bluetooth and reestablishes standard serial.

See: ["Raspberry Pi 3, 4 and Zero W Serial Port Usage"](https://www.abelectronics.co.uk/kb/article/1035/raspberry-pi-3-serial-port-usage).  

#### Test serial / USB output of GPS

Do a `cat` on your serial port (e.g. `cat /dev/ttyS0`), or, for USB `cat /dev/ttyACM0` or `cat /dev/ttyUSB0`, and you should receive an output like:

```
$GPGGA,1413247.000,48432.1655,N,01342323.7322,E,1,06,1.340,2505.5,M,347.6,M,,*69
$GPGSA,A,3,123,303,248,205,037,415,,,,,,,1.59,1.340,0.90*049
```

## Setting up GPSD

Once you successfully receive output from your GPS module, next step is to install `gpsd` via your packet manager.

Edit `/etc/default/gpsd`:

For serial connections (use your device name as tested above):

```
START_DAEMON="true"
GPSD_OPTIONS="-n -G"
DEVICES="/dev/ttyS0"
USBAUTO="false"
```

For USB connections (again use your actual device name):

```
START_DAEMON="true"
GPSD_OPTIONS="-n"
DEVICES="/dev/ttyACM0"
USBAUTO="true"
```

Enable and start `gpsd` with:

```
sudo systemctl enable gpsd
sudo systemctl start gpsd
```

Now use `cgps` or `gpsmon` to make sure that you are receiving GPS information and time.

`cgps` should display `Status: 3D fix (xx secs)`. Do not continue until you have a stable GPS fix.

## Setting up PPS

The serial or USB connection to the GPS module alone does not allow precise time synchronisation. The slow communication has latencies somewhere between 50ms to 200ms, much too high latency for precision time servers.

This is compensated by the PPS signal that is directly connected to Raspberry PI's GPIO 4 (you can use other GPIO pins, simply adapt this correpondingly below).

We need to enable a special kernel driver and overlay in order to receive this once-per-second GPS synchronised pulse as precisely as possible.

1. Edit `/boot/cmdline.txt` and add ` bcm2708.pps_gpio_pin=4` at the end of the line.
2. Edit `/boot/config.txt` and add a line `dtoverlay=pps-gpio,gpiopin=4`. (Depending on your distri, either 1. or 2. is necessary, but it doesn't seem to hurt to do both).
3. Edit `/etc/modules-load.d/raspberrypi.conf` and add two lines with `pps-gpio` and `pps-ldisc`, to load the required kernel modules

After a reboot, a new device `/dev/pps0` should exist, and `dmesg` should show something like:

```
[    7.528565] pps_core: LinuxPPS API ver. 1 registered
[    7.530144] pps_core: Software ver. 5.3.6 - Copyright 2005-2007 Rodolfo Giometti <giometti@linux.it>
[    7.540372] pps pps0: new PPS source pps@4.-1
[    7.542012] pps pps0: Registered IRQ 166 as PPS source
[    7.550775] pps_ldisc: PPS line discipline registered
```

Now use `ppstest` (you might need to install `pps-utils`):

`sudo ppstest /dev/pps0`

You should see an output like:

```
trying PPS source "/dev/pps0"
found PPS source "/dev/pps0"
ok, found 1 source(s), now start fetching data...
source 0 - assert 1606833766.999998552, sequence: 341090 - clear  0.000000000, sequence: 0
source 0 - assert 1606833767.999998573, sequence: 341091 - clear  0.000000000, sequence: 0
source 0 - assert 1606833768.999998751, sequence: 341092 - clear  0.000000000, sequence: 0
```

`assert` and `sequence` should both increment by 1 for each line.

Once you receive a PPS signal and GPSD is configured, continue.


## Setting up Chrony as time-server

**Note:** Before you setup `chrony`, make sure you completed `gpsd` configuration and that `gpsd` is running ok, and that you have a valid PPS signal at `/dev/pps0`.

Install `chrony`, an alternative NTP server that in my experience results in higher precision time servers than good old ntpd.

Make sure that no other time server (`ntdp`, `systemd-timedated`) is active, e.g.

```
sudo systemctl disable systemd-timedated
sudo systemctl stop systemd-timedated
```

Edit `/etc/chrony.conf`, and add two lines:

```
refclock PPS /dev/pps0 lock GPS
refclock SHM 0 refid GPS precision 1e-1 offset 0.0 delay 0.2 noselect
```

This uses a shared memory device `SHM` to get unprecise time information from GPSD (low precision, marked as `noselect`, so that chrony doesn't try to sync to serial time data). This unprecise time information is then synchronised with the much more precise PPS signal.

Now enable and start `chrony`:

```
sudo systemctl enable chronyd
sudo systemctl start chronyd
```

Then start the chrony console with `chronyc`. At the `chronyc>` prompt, enter:

`sources`:

```
chronyc> sources
210 Number of sources = 6
MS Name/IP address         Stratum Poll Reach LastRx Last sample               
===============================================================================
#* PPS0                          0   4   377    13   -138ns[ -108ns] +/-  120ns
#? GPS                           0   4   377    13  -4624us[-4624us] +/- 2148us
^- sismox.com                    3  10   377    15   -179us[ -179us] +/-   81ms
^- ntp.fra.de.as206479.net       2  10   377   749  +4235us[+4238us] +/-   16ms
^- mail.trexler.at               2  10   377  1114  +1190us[+1193us] +/-   13ms
^- ntp2.hetzner.de               2  10   377    59   -411us[ -411us] +/-   32ms
chronyc> 
```

If all went well, you should see a `PPS` device marked with `#*`, indicating the active time source. Error should be in nanosecond range (`-138ns[ -108ns] +/-  120ns`). `#?` indicates an unusable time source, `^-` a usable but unused source.

### Synchronizing the offset between serial time information and PPS

The PPS signal is only used, if the divergence between the slow serial/USB time information and the precise PPS signal is less than 200ms. If your PPS device stays on `#?` (unusable), and you are sure that gpsd is receiving valid GPS signals and `ppstest` shows a correct PPS signal, then we need to tune the offset between serial time information and PPS. 

In `chronyc`, enter `sourcestats`

```
chronyc> sourcestats
210 Number of sources = 9
Name/IP Address            NP  NR  Span  Frequency  Freq Skew  Offset  Std Dev
==============================================================================
...
GPS                        40  22   626     -4.310      9.467    512ms  2474us
...
```

the important field is `offset` of `GPS`: if that is larger 200ms, PPS cannot sync to GPS.

Wait a few minutes for the offset to stabilize, note it's value, and edit `/etc/chrony.conf`, and change the offset in the second line with the value above, converted to seconds (512ms are 0.512 sec in this case):

```
refclock PPS /dev/pps0 lock GPS
refclock SHM 0 refid GPS precision 1e-1 offset 0.512 delay 0.2 noselect
```

Restart `chrony` with `sudo systemctl restart chronyd`, and check `chronyc` again:

After some time the output of `sourcestats` should show a much better offset for GPS:

```
chronyc> sourcestats
210 Number of sources = 9
Name/IP Address            NP  NR  Span  Frequency  Freq Skew  Offset  Std Dev
==============================================================================
PPS0                       12   5   179     +0.000      0.003     +1ns   102ns
GPS                        40  22   626     -4.310      9.467  -8600us  2474us
```

and `sources` should now show PPS as active, marked with `#*`.

Use `chronyc` and command `tracking` to get information about the precision of your new time server:

```
chronyc> tracking
Reference ID    : 50505330 (PPS0)
Stratum         : 1
Ref time (UTC)  : Tue Dec 01 15:17:22 2020
System time     : 0.000000032 seconds slow of NTP time
Last offset     : -0.000000059 seconds
RMS offset      : 0.000000103 seconds
Frequency       : 2.167 ppm fast
Residual freq   : -0.000 ppm
Skew            : 0.005 ppm
Root delay      : 0.000000001 seconds
Root dispersion : 0.000025110 seconds
Update interval : 16.0 seconds
Leap status     : Normal
```

* For more information, check the [chrony PPS documentation](https://chrony.tuxfamily.org/faq.html#_using_a_pps_reference_clock)

### Making you new precision time server available on the network

By default, chrony allows only local access, use `allow` in `/etc/chrony.conf` to allow access in your local network, e.g.:

```
allow 192.168/16
```

To be able to administer the chrony time server over the net, add:

```
cmdallow 192.168/16
```

#### Further optimizations in `chrony.conf`

* `lock_all` to make sure chrony is always in memory.
* `local stratum 1` to signal precision time.

For more, check the [official chrony documenation](https://chrony.tuxfamily.org/doc/4.0/chrony.conf.html)

