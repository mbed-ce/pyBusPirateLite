"""
Script to provide a simple SPI sniffer using the bus pirate device.
Designed to be similar to the "SPI sniffer" application available here:
https://code.google.com/archive/p/the-bus-pirate/downloads

"""

import binascii
import argparse
import sys

from pyBusPirateLite import SPI

# Parse args
parser = argparse.ArgumentParser(description="Sniffs for SPI traffic using the bus pirate and logs it to the console.")

parser.add_argument("-p", "--port", type=str, default="", help="Specify COM port to communicate with the bus pirate on.  If unset, the first detected device will be used.")
parser.add_argument("-c", "--no-cs", action="store_true",
                    help="Don't use the CS pin to detect bus activity -- sniff all the time.")
parser.add_argument("-m", "--spi-mode", type=int, default=0, help="SPI mode to operate in (0-3).  Default 0.")
parser.add_argument("-d", "--debug", action="store_true", help="Debug mode.  Prints raw serial comms with the Pirate.")

args = parser.parse_args()

# Connect and configure device
try:
    buspirate_spi = SPI(portname=args.port, timeout=1.0)
except IOError as err:
    print("Failed to connect to Bus Pirate: " + str(err))
    sys.exit(1)

buspirate_spi.serial_debug = args.debug

# Since we are just sniffing, may as well leave drivers as open drain
config: int = SPI.CONFIG_DRIVERS_OPEN_DRAIN | SPI.CONFIG_SAMPLE_TIME_MIDDLE

# Configure mode settings.
# Reference here: https://en.wikipedia.org/wiki/Serial_Peripheral_Interface#Clock_polarity_and_phase
if args.spi_mode == 0:
    # Note: As far as I can tell, the Bus Pirate firmware seems to have the SPI clock phase
    # swapped -- the setting that seems like it would produce CPHA = 1 instead produces CPHA = 0.
    # I renamed the driver constant to match this.
    config |= SPI.CONFIG_CLOCK_PHASE_0 | SPI.CONFIG_CLOCK_POLARITY_ACT_LOW
elif args.spi_mode == 1:
    config |= SPI.CONFIG_CLOCK_PHASE_1 | SPI.CONFIG_CLOCK_POLARITY_ACT_LOW
elif args.spi_mode == 2:
    config |= SPI.CONFIG_CLOCK_PHASE_0 | SPI.CONFIG_CLOCK_POLARITY_ACT_HIGH
elif args.spi_mode == 3:
    config |= SPI.CONFIG_CLOCK_PHASE_1 | SPI.CONFIG_CLOCK_POLARITY_ACT_HIGH
else:
    print(f"Invalid --spi-mode value {args.spi_mode}.  Must be between 0 and 3 inclusive.")
    sys.exit(1)

buspirate_spi.config = config
buspirate_spi.pins = SPI.PIN_CS
buspirate_spi.enter_sniff_mode(not args.no_cs)

print(f"Sniffing started on {buspirate_spi.portname}, Ctrl-C to exit...")

try:
    while True:
        mosi_miso_bytes = buspirate_spi.sniff_message()
        if mosi_miso_bytes is not None:
            print("MOSI: " + binascii.b2a_hex(mosi_miso_bytes[0]).decode("ASCII"))
            print("MISO: " + binascii.b2a_hex(mosi_miso_bytes[1]).decode("ASCII"))
except KeyboardInterrupt:
    pass

buspirate_spi.disconnect()
sys.exit(0)