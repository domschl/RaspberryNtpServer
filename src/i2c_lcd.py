import time
import logging
import smbus
import copy


class LcdDisplay:
    """ Support for LCD displays using HD44780 display chips using
        I2C via either PCF8574 or MCP23008 (Adafruit way) I2C to GPIO converters
    """
    def __init__(self, sm_bus:int=1, i2c_addr:int=0x27, cols:int=20, rows:int=4, ada:bool=False):
        """
        smbus:int: should be `1` for all Raspbery PI (with exception of Raspberry 1)
        i2c_addr:int: default is 0x27 (used with most hardware), Adafruit uses 0x20 if no bridges soldered
        cols:int: currently always 20
        rows:int: currently always 4
        ada:bool: default False, use PCF8574 chip and pin-layout
                          True: use Adafruit MCP23008 and their specific pin-layout
        """
        self.log: logging.Logger = logging.getLogger("LcdDisplay")
        self.ada: bool = ada
        try:
            self.bus:smbus.SMBus = smbus.SMBus(sm_bus)  # Rev 1 Pi: 0, Rev 2 Pi: 1  # pyright:ignore[reportUnknownMemberType]
            self.active:bool = True
        except Exception as e:
            self.log.error(f"Cannot open LCD on I2C bus: {e}")
            self.active = False
            return

        try:
            self.bus.read_byte(i2c_addr)  # pyright:ignore[reportUnknownMemberType]
            self.log.info(f"Connected to display at i2c address {hex(i2c_addr)}")
        except:
            self.log.error(f"No device found at i2c address {hex(i2c_addr)}")
            self.active = False
            return
        
        self.i2c_addr:int = i2c_addr
        self.cols:int = cols
        self.rows:int = rows
        self.line_cmds:list[int] = [0x80, 0xC0, 0x94, 0xD4]  # lines 1-4

        self.start_byte_delay:float = 0.001
        self.delay:float = 0.00001
        self.cls_delay:float = 0.003
        self.type_data:int = 1
        self.type_command:int = 0
        self.enable:int = 0x04
        self.set_backlight(True)

        if self.ada is True:
            # If MCP23008 chip is used, initialize it. (PCF8574 doesn't need init)
            self._init_mcp23008()

        # Initialize the display chip HD44780
        self.write(0x33, self.type_command)  # init sequence: 0x03, 0x03
        self.write(0x32, self.type_command)  # init seq cont: 0x03, 0x02
        self.write(0x06, self.type_command)  # cursor dir
        self.write(0x0C, self.type_command)  # display on, cursor off, blink of
        self.write(0x28, self.type_command)  # data len, num lines, font size
        self.write(0x01, self.type_command)  # clear (slow!)
        time.sleep(self.cls_delay)

        # Initialize the display buffer
        self.screen_buf:list[list[str]] = [[" " for _ in range(cols)] for _ in range(rows)]
        self.cur_row:int = 0
        self.cur_col:int = 0
        
        self.log.debug("LCD display initialized.")

    def _init_mcp23008(self):
        # Taken from: <https://github.com/adafruit/Adafruit_CircuitPython_MCP230xx/blob/main/adafruit_mcp230xx/mcp23008.py>
        if self.ada is True:
            self.bus.write_byte_data(self.i2c_addr, 0x00, 0x01)  # IODIR, reset almost all to OUTPUT, bit 0 input (unused)  # pyright:ignore[reportUnknownMemberType]
            time.sleep(self.delay)
            self.bus.write_byte_data(self.i2c_addr, 0x06, 0x00)  # GGPU, all pull-ups off  # pyright:ignore[reportUnknownMemberType]
            time.sleep(self.delay)
            self.bus.write_byte_data(self.i2c_addr, 0x01, 0x00)  # IPOL, no inverse polarity  # pyright:ignore[reportUnknownMemberType]
            time.sleep(self.delay)
            
    def set_backlight(self, state:bool):
        """ Set backlight on/off """
        if self.active is False:
            return
        if state is True:
            self.backlight:int = 0x08
        else:
            self.backlight = 0x00

    def _dev_write(self, byte:int):
        if self.ada is True:
            # Do a register-write for MCP23008, using GPIO function 0x09
            self.bus.write_byte_data(self.i2c_addr, 0x09, byte)  # MCP23008 GPIO function    # pyright:ignore[reportUnknownMemberType]
        else:
            # Just write content for PCF8574
            self.bus.write_byte(self.i2c_addr, byte)  # pyright:ignore[reportUnknownMemberType]
        
    def write(self, byte:int, data_type:int):
        """ write to Display chip using an I2C to GPIO converter """
        if self.active is False:
            return

        if self.ada is True:
            # 'cabling' between display chip and i2c convert is different for adafruit!
            backlight = self.backlight << 4
            data_type = data_type << 1
            hi_byte = data_type | ((byte & 0xF0) >> 1) | backlight
            lo_byte = data_type | ((byte & 0x0F) << 3) | backlight
        else:
            hi_byte = data_type | (byte & 0xF0) | self.backlight
            lo_byte = data_type | ((byte << 4) & 0xF0) | self.backlight

        time.sleep(self.start_byte_delay)
        self._dev_write(hi_byte)
        time.sleep(self.delay)
        self._dev_write(hi_byte | self.enable)
        time.sleep(self.delay)
        self._dev_write(hi_byte & ~self.enable)
        time.sleep(self.delay)

        time.sleep(self.start_byte_delay)
        self._dev_write(lo_byte)
        time.sleep(self.delay)
        self._dev_write(lo_byte | self.enable)
        time.sleep(self.delay)
        self._dev_write(lo_byte & ~self.enable)
        time.sleep(self.delay)

    def write_row(self, row:int):
        """ Write complete row from buffer """
        if self.active is False:
            return
        ra = self.line_cmds[row]
        self.write(ra, self.type_command)
        for i in range(self.cols):
            self.write(ord(self.screen_buf[row][i]), self.type_data)

    def print_row(self, row:int, text:str):
        """ Print row to buffer and display """
        if self.active is False:
            return
        if row < 0:
            row = 0
        if row >= self.rows:
            row = self.rows - 1
        text = text[: self.cols].ljust(self.cols, " ")
        self.screen_buf[row] = [text[i] for i in range(len(text))]
        self.write_row(row)

    def print_at(self, row:int, col:int, text:str):
        """ Print to buffer and display at given coordinates """
        if self.active is False:
            return
        if row < 0 or row > self.rows - 1:
            row = 0
        if col < 0 or col > self.cols - 1:
            col = 0
        text = text[: self.cols - col]
        for i in range(len(text)):
            self.screen_buf[row][i + col] = text[i]
        self.write_row(row)

    def scroll(self, n:int=1):
        """ Scroll screen a number of lines """
        if self.active is False:
            return
        for _ in range(n):
            for r in range(self.rows - 1):
                self.screen_buf[r] = copy.copy(self.screen_buf[r + 1])
            for i in range(self.cols):
                self.screen_buf[self.rows - 1][i] = " "
        for i in range(self.rows):
            self.write_row(i)
        if self.cur_row > 0:
            self.cur_row = self.cur_row - 1

    def print(self, text:str):
        """ Print longer text, scroll if necessary """
        if self.active is False:
            return
        if len(text) + self.cur_col > self.cols:
            ctext = text[: self.cols - self.cur_col]
            rtext = text[self.cols - self.cur_col :]
        else:
            ctext = text
            rtext = None
        if self.cur_row >= self.rows:
            self.scroll()
        for i in range(len(ctext)):
            self.screen_buf[self.cur_row][self.cur_col + i] = ctext[i]
        self.cur_col = self.cur_col + len(ctext)
        self.write_row(self.cur_row)
        if self.cur_col >= self.cols:
            self.cur_col = 0
            self.cur_row = self.cur_row + 1
        if rtext is not None:
            self.print(rtext)


if __name__ == "__main__":
    """ Stand-alone test routines for the display
        Adapt i2c_addr and adafruit_hw below
    """

    # Adapt:
    i2c_addr:int = 0x27         # I2C address, adapt to your board (usual values are 0x20 .. 0x27)
    adafruit_hw:bool = False    # Set to True for Adafruit MCP23008 based I2C converter, False for all others (PCF8574 converter)

    # Start test:
    logging.basicConfig(level=logging.DEBUG)
    lcd = LcdDisplay(1, i2c_addr, 20, 4, ada=adafruit_hw)
    if lcd.active is True:
        if adafruit_hw is True:  #pyright:ignore[reportUnnecessaryComparison]
            print("Display (Ada) is active, outputting a test-text to the display...")  #pyright:ignore[reportUnreachable]
        else:
            print("Display is active, outputting a test-text to the display...")
        lcd.print(
            "Hello! That is a hell of a lot of text that we are going to display on this tiny screen. However there is always a way to present information in a way that is helpful, even under contrained conditions."
        )
        print("Done")
        exit(0)
    else:
        print("Failed to initialize display")
        exit(-1)
