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

* Active GPS antenna

When selecting a GPS antenna, make sure to get an active antenna with 3-5V power input. Passive antennas often look similar, but reception quality is far worse at similar cost.

### Antenna adapters

Some boards have uFL antenna connectors, whereas almost all external active antennas use SMA, so you might need an uFL to SMA adapter:

* [Adafruit uFL to SMA adapter](https://www.adafruit.com/product/851)
* [Various uFL to SMA adapters](https://www.aliexpress.com/item/4000166668788.html?spm=a2g0o.productlist.0.0.2c386be8fN3oCH&algo_pvid=6da3d77b-f49d-4e6b-8dba-c9c7446cd7b4&algo_expid=6da3d77b-f49d-4e6b-8dba-c9c7446cd7b4-1&btsid=2100bddf16068135762546912e571d&ws_ab_test=searchweb0_0,searchweb201602_,searchweb201603_)

### Problems

#### Is external antenna selected?

Some GPS modules come with a passive antenna and and external antenna plug. Check the description of your board to find out what's needed to use the external antenna. The Keystudio GPS module listed above for example, requires the removal of capacitor C2 in order to activate the external antenna.

#### PPS signal easily accessible?

Make sure your GPS module has an accessible output for the PPS signal.

If you are using a GPS Hat that plugs into the Raspberry IO connector, check the documentation to which GPIO pin the PPS signal is connected. Adafruit's Hat uses GPIO 4.

#### USB vs serial

When not using a Pi Hat, decide between USB- and serial connection.

USB-Connection:
* No extra cables for Vcc, GND, Tx, Rx are needed: both powersupply and communication goes over USB.
* No modification of Raspberry's serial console is needed, easier software installation

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

## Software

* Raspberry Linux preparations

  * Serial port console
  * bluetooth overlay disable
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

