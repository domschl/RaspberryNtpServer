# RaspberryNtpServer

Stratum-1 NTP time server with Raspberry Pi, GPS and Chrony

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

* Adafruit has an execellent [GPS guide](https://learn.adafruit.com/adafruit-ultimate-gps) for their ultimate GPS module.

## Software

### Raspberry Linux preparations

#### Serial port console

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

See [Source](https://www.raspberrypi.org/documentation/configuration/uart.md#:~:text=Disable%20Linux%20serial%20console&text=This%20can%20be%20done%20by,Select%20option%20P6%20%2D%20Serial%20Port) at raspberrypi.org.

Older versions of `raspi-config` hide the same serial options under "Advanced options"

##### Other linux distributions and manual configuration

1. Edit `/boot/cmdline.txt` and remove references to the serial port `ttyAMA0`. E.g. remove: `console=ttyAMA0,115200` and (if present) `kgdboc=ttyAMA0,115200`.
2. Disable getty on serial port. `sudo systemctl disable getty@ttyAMA0` or, on some Linux distris: `sudo systemctl disable serial-getty@ttyAMA0`
3. Enable uart in `/boot/config.txt`, add a line `enable_uart=1`
4. For RPI 3 or later disable bluetooth via overlay, add another line to `/boot/config.txt`: `dtoverlay=pi3-disable-bt-overlay`


  
See also: [this reference for RPI 3, 4 and zero](https://www.abelectronics.co.uk/kb/article/1035/raspberry-pi-3-serial-port-usage).  
  
  
  
  
  
  * pps kernel drivers and gpio
  
* gspd tests
* pps tests

  * pps-utils
  
* chrony

## Setting up GPS

## Setting up PPS

## Setting up Chrony as time-server

* https://chrony.tuxfamily.org/faq.html#_using_a_pps_reference_clock

### Tuning GPS delay


## Testing and trouble shooting

## Accessing GPS and time information with python

