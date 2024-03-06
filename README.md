# GPS disciplined Stratum-1 NTP Server with Raspberry PI - a HowTo

Stratum-1 NTP time server with Raspberry Pi, GPS and Chrony: 

- how to build a precision time server.
- (optional) [how to add a 4x20 LCD to display](src) server status and GPS and PPS information.


<div align="right">
<img src="https://github.com/domschl/RaspberryNtpServer/blob/main/images/ntp-lcd.jpg" width="300" /><br>
<em>Optional display shows PPS lock</em>
</div>

## Requirements - Hardware

- Raspberry Pi

While you can use any model of Raspberry Pi to implement a Stratum-1 NTP server with GPS, the best choice
is Raspberry Pi 4, due to 1Gbit network interface and fast hardware for lowest possible latencies.

  - Using a Raspberry Pi 5 gives two additional advantages:

    - Support for the inbuilt hardware real time clock (RTC) that comes with the Raspberry Pi 5
    - Support for the PTP protocol, which allows to transmit precision time information via ethernet hardware

Both options are of limited advantage for most settings: the hardware clock is only useful for providing time during the first few seconds after boot (and if both GPS _and_ network are inaccessible), and PTP is a time standard requiring IEEE1588-enabled hardware everywhere and provides no advantages over NTP/chrony in most settings. Both however are documented below (See `chrony` configuration, PTP-chapter).

- GPS module

  * Adafruit GPS hat: [Adafruit ultimate GPS hat](https://www.adafruit.com/product/2324)
  * GPS module with serial output and PPS signal: [Adafruit GPS module](https://www.adafruit.com/product/746)
  * GPS module with USB, SMA connector and PPS: [Keystudio GPS module](https://wiki.keyestudio.com/KS0319_keyestudio_GPS_Module)
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

* Raspberry PI 4 (or 5)
* Either GPS hat (e.g. adafruit ultimate GPS hat + uFL to SMA-Adapter) or USB-GPS-Module with PPS output (e.g. keystudio gps module)
* Active GPS antenna with SMA connector and 3-5V

### Most cost-efficient setup

NEO6 GPS modules are available at very low cost (1-2Eur) at chinese dealers (Aliexpress) and are perfectly usable as long as they allow connecting an active external GPS antenna and provide a PPS signal.

<img src="https://github.com/domschl/RaspberryNtpServer/blob/main/images/gps-wiring.png" width="600" height="400" />

_Typical wiring between GPS module and Raspberry Pi connector._

> **Note:** If your GPS module is connected via USB, you only need to connect the PPS connector on the GPS module to GPIO 4 on the Raspberry. Power (Vin), Gnd and Tx/Rx are handled via USB.

### Test

**Before you continue with software:** At this point, the GPS module should be connected to the Raspberry Pi and the active antenna. Power up the Raspberry Pi, and check that the GPS module receives the GPS signal (the antenna must have unhindered access to the open sky, it does *not* work indoors!).

If reception is ok, a led ("FIX" or "PPS") should start blinking on your GPS module. 

Check the documentation for your specific hardware how "FIX" is signaled:

- The Adafruit module blinks once per second if there is no fix and once every 10 seconds when there is a fix.

### More information

* Adafruit has an excellent [GPS guide](https://learn.adafruit.com/adafruit-ultimate-gps) for their ultimate GPS module.

### Professional / Lab considerations: PTP precision time protocol (OPTIONAL)

If you are using laboratory equipment that uses PTP (precision time protocol) information (IEEE 1588), then you will need to use the Raspberry Pi 5 and make sure that your network switches are IEEE 1588 capable. Note that most consumer switches are not IEEE 1588 capable and cannot be used to set up a PTP network. See below (PTP chapter) for setup details and hardware tests.

PTP is completely optional and not required in a network in order to have excellent results with your Raspberry Pi NTP server!

## Software

> **Note:** _(Optional info)_ The original repository of `chrony` at <https://chrony.tuxfamily.org/> seems to be of low availability. In case of problems, use the mirror at <https://github.com/mlichvar/chrony)> if you want to reference the original `chrony` sources at some point.

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

Once you successfully receive output from your GPS module, next step is to install `gpsd` via your package manager.

For Raspberry Pi OS (and Ubuntu and Debian variants), that would be:

```bash
sudo apt install gpsd
```

Edit `/etc/default/gpsd`:

For serial connections (use your device name as tested above):

```
GPSD_OPTIONS="-n -G"
DEVICES="/dev/ttyS0"
USBAUTO="false"
```

For USB connections (again use your actual device name):

```
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

We need to enable a special kernel driver and overlay in order to receive this once-per-second GPS synchronised pulse as precisely as possible. The location of config files for kernel modules and options has changed recently (2024-03)!jj

### Current Raspberry Pi OS 'Bookworm' (since 2024-03)

You'll find that `/boot/config.txt` just contains a note that file content has moved to `/boot/firmware/config.txt`. 

1. Edit `/boot/config.txt` and add a line `dtoverlay=pps-gpio,gpiopin=4`. (Editing `cmdline.txt` is no longer necessary)
2. Edit `/etc/modules-load.d/raspberrypi.conf` and add two lines with `pps-gpio` and `pps-ldisc`, to load the required kernel modules

### Older versions of Raspberry Pi OS and other distris

if your `/boot/config.txt` does __not__ contain a note that content has moved to `/boot/firmware/config.txt`:

1. Edit `/boot/cmdline.txt` and add ` bcm2708.pps_gpio_pin=4` at the end of the line. (Might not be necessary)
2. Edit `/boot/config.txt` and add a line `dtoverlay=pps-gpio,gpiopin=4`. (Depending on your distri, either 1. or 2. is necessary, but it doesn't seem to hurt to do both).
3. Edit `/etc/modules-load.d/raspberrypi.conf` and add two lines with `pps-gpio` and `pps-ldisc`, to load the required kernel modules

After a reboot, a new device `/dev/pps0` should exist, and `dmesg` should show something like:

```
[    7.528565] pps_core: LinuxPPS API ver. 1 registered
[    7.530144] pps_core: Software ver. 5.3.6 - Copyright 2005-2007 Rodolfo Giometti <giometti@linux.it>
[    7.540372] pps pps0: new PPS source pps@4.-1
[    7.542012] pps pps0: Registered IRQ 166 as PPS source
[    7.550775] pps_ldisc: PPS line discipl43ine registered
```

Now use `ppstest` (you might need to install `pps-utils` or `pps-tools` depending on your distri):

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

### Access permissions for `/dev/pps0`

Some linux distribution only allow `root` to read or access `/dev/pps0`. This is no issue, if only root services want to access `/dev/pps0`. Note that recent versions of `chronyd` drop privileges after start, and then might not be able to access `/dev/pps0` anymore. See below for solutions (`udev` or running `chronyd` as root.)

### Timeouts with Raspberry Pi OS 64-bit 2023-03 onwards

**Note:** This problem seems to be fixed with current Raspberry Pi OS 'bookworm' releases (2023-12 status).

`sudo ppstest /dev/pps0` yields:

```
found PPS source "/dev/pps0"
ok, found 1 source(s), now start fetching data...
source 0 - assert 1679340614.003464678, sequence: 84623 - clear  0.000000000, sequence: 0
time_pps_fetch() error -1 (Connection timed out)
```

See issue [6](https://github.com/domschl/RaspberryNtpServer/issues/6) for the ongoing discussion.

## Setting up Chrony as time-server

> **Note:** Before you setup `chrony`, make sure you completed `gpsd` configuration and that `gpsd` is running ok, and that you have a valid PPS signal at `/dev/pps0`.

> **Note:** Especially when using Raspberry Pi 5 (with new features PTP and RTC), it is recommended to use the standard Raspberry Pi OS, which comes with a chrony version, that is aware of the Raspberry Pi hardware.

Recent chronyd versions drop root privilege after start (check for the `-u` option in `chronyd.service` to see the user that will be used to run `chronyd`). If `/dev/pps0` is not accessible for that user, pps won't work. There are two solutions: either use a version of chronyd that doesn't drop privileges and runs as root, or setup a `udev` rule that allows access to `/dev/pps0` for the process-user of `chronyd`.

If you [compile](https://chrony.tuxfamily.org/doc/3.5/installation.html), [mirror](https://github.com/mlichvar/chrony/blob/master/doc/installation.adoc) `chrony` yourself, there is an option `--disable-privdrop` for `configure`. See `configure -h` for all options for building `chrony`.

### `udev` rules example

Udev rules are tricky and depend on the user of the `chronyd` process and the type of connection your are using.

Create a file `/etc/udev/rules.d/pps-sources.rules` starting with this example (which works with Raspberry Pi OS), which you will need to modify to your configuration:

```
KERNEL=="pps0", OWNER="root", GROUP="_chrony", MODE="0660"
KERNEL=="ttyS0", RUN+="/bin/setserial -v /dev/%k low_latency irq 4"
```

To activate those new `udev` rules, either reboot, or use: `sudo udevadm control --reload-rules && sudo udevadm trigger`.

This assumes `_chrony` being the user/group of the `chronyd` process (check with `ps aux | grep chronyd`) and a serial connection (here `/dev/ttyS0`) being used.[^1]

### Installation of `chrony`

Install `chrony`, an alternative NTP server that in my experience results in higher precision time servers than good old ntpd.

Make sure that no other time server (`ntdp`, `systemd-timedated`) is active, e.g.

```
sudo systemctl disable systemd-timedated
sudo systemctl stop systemd-timedated
```

Depending on you distri and chrony versione, the config is either `/etc/chrony/chrony.conf` or `/etc/chrony.conf`, edit the file and add two lines:

```
refclock PPS /dev/pps0 lock GPS
refclock SHM 0 refid GPS precision 1e-1 offset 0.01 delay 0.2 noselect
```

> **Note:** For recent `chrony` versions, an offset of `0.0` seems to prevent GPS sync, hence set it to `offset 0.01` (or any small, non-zero value) for start. See below, how to get the actual correct `offset` value.

This uses a shared memory device `SHM` to get unprecise time information from GPSD (low precision, marked as `noselect`, so that chrony doesn't try to sync to serial time data). This unprecise time information is then synchronised with the much more precise PPS signal.

#### Additional Raspberry Pi 5 features

Verify that `chrony.conf` contains the following line (standard in Raspberry Pi OS version):

```
# This directive enables kernel synchronisation (every 11 minutes) of the
# real-time clock. Note that it can't be used along with the 'rtcfile' directive.
rtcsync
```

If you want to transmit PTP hardware timestamps via ethernet, add:

```
hwtimestamp *
```

See below for some more details on PTP.

#### All version, continued

Now enable and start `chrony`:

```
# Note: Some distributions use `chronyd` instead of `chrony`, so replace, if necessary:
sudo systemctl enable chrony
sudo systemctl start chrony
```

Verify that `chrony` started ok with `sudo systemctl status chronyd`. One possible error is a fatal message that `chronyd has been compiled without PPS support`. If that's the case (e.g. Manjaro ARM 64bit), you either need to [compile chrony yourself](https://chrony.tuxfamily.org/doc/2.4/installation.html), [mirror](https://github.com/mlichvar/chrony/blob/master/doc/installation.adoc), or switch to another distri.

Then start the chrony console with `chronyc`. At the `chronyc>` prompt, enter:

`sources`

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

<div align="right">
<img src="https://github.com/domschl/RaspberryNtpServer/blob/main/images/ntp-lcd-slow.jpg" width="300" /><br>
<em>Before PPS lock, stratum 3</em>
</div>

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

<div align="right">
<img src="https://github.com/domschl/RaspberryNtpServer/blob/main/images/ntp-lcd.jpg" width="300" /><br>
<em>After PPS lock, stratum 1</em>
</div>

> **Note:** A value of `offset 0.0` seems to prevent synchronisation for some versions of chrony, so use some small non-zero value instead, if a value close to 0 is required for your installation.

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

* For more information, check the [chrony PPS documentation](https://chrony.tuxfamily.org/faq.html#_using_a_pps_reference_clock), [mirror](https://github.com/mlichvar/chrony/blob/master/doc/faq.adoc#using-pps-refclock)

### Making you new precision time server available on the network

By default, chrony allows only local access, use `allow` in `/etc/chrony.conf` to allow access in your local network, e.g.:

```
allow 192.168/16
```

To be able to administer the chrony time server over the net, add:

```
cmdallow 192.168/16
```

### Remote testing

The tool `sntp` (available by default on macOS, part of the `ntp` package for most linux distributions)
allows for simple remote testing:

> **Note:** when installing `ntp` for getting access to the `sntp` tool, make sure that you do not accidentally activate the `ntp` server which will conflict with your chrony installation.

```bash
sntp <ip-or-hostname-of-raspberry-chrony-server>
```

yields (mac connected via WLAN):
```bash
sntp chronotron
# Output:
+0.011341 +/- 0.002986 chronotron 192.168.178.3
```

More information is available with `sntp -d`

```bash
sntp -d chronotron
# Output:
sntp_exchange {
        result: 0 (Success)
        header: 24 (li:0 vn:4 mode:4)
       stratum: 01 (1)
          poll: 00 (1)
     precision: FFFFFFE8 (5.960464e-08)
         delay: 0000.0001 (0.000015259)
    dispersion: 0000.000B (0.000167847)
           ref: 50505300 ("PPS ")
    ...
}
```

Interesting information is for example:

- `ref: xx.. ("PPS")`
- `precision: (5.9e-08)`

### Raspberry Pi 5 and the PTP precision time protocol via ethernet  [OPTIONAL for SPECIAL SETTINGS]

> **Note:** The PTP precision time protocol (IEEE 1588) is of limited use for home networks, it requires that every component (server, network switch, client) have hardware support for IEEE 1588 which is not the case for most consumer hardware. You cannot use PTP if a single component does not support it.

An excellent overview over PTP, it's relation to NTP can be found at Redhat's [_combining ptp and ntp_](https://www.redhat.com/en/blog/combining-ptp-ntp-get-best-both-worlds) article.
If you are not in a professional lab environment, _you might not need PTP at all!_

#### Preparations

You can verify that hardware timestamping is active by executing `sudo systemctl status chrony` right after start of chrony. You should see something like:

```
Dec 20 15:17:15 chronotron chronyd[9525]: chronyd version 4.3 starting (+CMDMON +NTP +REFCLOCK +RTC +PRIVDROP +SCFILTER +SIGND +ASYNCDNS +NTS +SECHASH +IPV6 -DEBUG)
Dec 20 15:17:15 chronotron chronyd[9525]: Enabled HW timestamping on eth0
```

To verify if a chrony client or server can support the PTP protocol, use:

```bash
ethtool -T eth0
```

You should see something like:

```
Time stamping parameters for eth0:
Capabilities:
        hardware-transmit
        software-transmit
        hardware-receive
        software-receive
        software-system-clock
        hardware-raw-clock
PTP Hardware Clock: 0
Hardware Transmit Timestamp Modes:
        off
        on
        onestep-sync
Hardware Receive Filter Modes:
        none
        all
```

Required are the `hardware-transmit` and `hardware-receive` options.

#### PTP software

Make sure the kernel module `ptp` is loaded (`sudo modprobe ptp`). In addition, you will need `linuxptp` on both server and client. On the
raspberry, it can be installed with `sudo apt install linuxptp`

On the raspberry server:

```
sudo ptp4l -i eth0 ptp0 -m -2
```

The ptp server should start and output something like:

```
ptp4l[6491.320]: selected /dev/ptp0 as PTP clock
ptp4l[6491.364]: port 1: INITIALIZING to LISTENING on INIT_COMPLETE
ptp4l[6491.364]: port 0: INITIALIZING to LISTENING on INIT_COMPLETE
ptp4l[6498.761]: port 1: LISTENING to MASTER on ANNOUNCE_RECEIPT_TIMEOUT_EXPIRES
ptp4l[6498.761]: selected local clock d83add.fffe.b1d67a as best master
ptp4l[6498.761]: port 1: assuming the grand master role
```

Now, on a client that has a network card with IEEE 1588 support (check with `ethtool -T eth0` that hardware-transmit is supported) and is connected either directly or via a PTP-IEEE 1588 enabled switch (hint: most consumer network switch _do not support the required protocol_!):

again make sure module `ptp` is loaded, install `linuxptp` and:

```
sudo ptp4l -i enp86s0 -m -2 -s
```

the `-s` option enables slave mode for the client.

If it works, you should see something like:

```
ptp4l[82232.615]: selected /dev/ptp0 as PTP clock
ptp4l[82232.689]: port 1 (enp86s0): INITIALIZING to LISTENING on INIT_COMPLETE
ptp4l[82232.689]: port 0 (/var/run/ptp4l): INITIALIZING to LISTENING on INIT_COMPLETE
ptp4l[82232.689]: port 0 (/var/run/ptp4lro): INITIALIZING to LISTENING on INIT_COMPLETE
ptp4l[82233.617]: port 1 (enp86s0): new foreign master d83add.fffe.b1d67a-1
ptp4l[82237.617]: selected best master clock d83add.fffe.b1d67a
ptp4l[82237.617]: port 1 (enp86s0): LISTENING to UNCALIBRATED on RS_SLAVE
ptp4l[82239.619]: master offset   59823 s0 freq  -51831 path delay    4413
ptp4l[82240.618]: master offset   59749 s1 freq -2154985 path delay   4159
ptp4l[82241.618]: master offset   59733 s2 freq  +91748 path delay   4159
```

If you get any `received SYNC without timestamp` or similar with `DELAY`, then somewhere in your transmission chain there is non-IEEE 1588 hw, and the sync doesn't work.

### Further optimizations in `chrony.conf`

* `lock_all` to make sure chrony is always in memory.
* `local stratum 1` to signal precision time.
* `allow` without any address simply allows all networks. (Including external access, if your machine is connected to the internet!)

For more, check the [official chrony documenation](https://chrony.tuxfamily.org/doc/4.0/chrony.conf.html), [mirror: chrony.conf](https://github.com/mlichvar/chrony/blob/master/doc/chrony.conf.adoc).

## Add a 4x20 hardware LCD display

<img src="https://github.com/domschl/RaspberryNtpServer/blob/main/images/gps-with-pps-and-i2c-lcd.jpg" align="right" width="450" />

Optionally, you can use [this sub-project to a status display to the Raspberry Pi](src).

## History

- 2024-03-06: Update: location of `/boot/config.txt` has changed to `/boot/firmware/config.txt`. Thanks to @Nebulosa-Cat for the information!
- 2023-12-21: Cleanup for the display software, display current stratum level (thanks @Lefuneste83, see [#7](https://github.com/domschl/RaspberryNtpServer/issues/7)), implemented logging.
- 2023-12-20: Raspberry 5 and suport for RTC and PTP precision time protocol how-tos.
- 2023-07-11: Documentation fixes (thx. @glenne), see [#4](https://github.com/domschl/RaspberryNtpServer/issues/4) for details. Mirror links for `chrony` added.
- 2023-02-24: Added information by @cvonderstein on initial `offset 0.01` and `udev` rules, see [#1](https://github.com/domschl/RaspberryNtpServer/issues/1) for details.
- 2023-01-09: Code for 4x20 LCD display for NTP server PPS state added.

### References

- [`chrony` documentation (mirror)](https://github.com/mlichvar/chrony/tree/master/doc)

[^1]: Thanks @cvonderstein for providing this information, see [#1](https://github.com/domschl/RaspberryNtpServer/issues/1) for further discussion.
