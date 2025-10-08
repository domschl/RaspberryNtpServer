import time
import logging
import smbus
import copy


class LcdDisplay:
    def __init__(self, sm_bus=1, i2c_addr=0x27, cols=20, rows=4):
        self.log = logging.getLogger("LcdDisplay")
        try:
            self.bus = smbus.SMBus(sm_bus)  # Rev 1 Pi: 0, Rev 2 Pi: 1
            self.active = True
        except Exception as e:
            self.log.error(f"Cannot open LCD on I2C bus: {e}")
            self.active = False
            return

        try:
            self.bus.read_byte(i2c_addr)
            self.log.info(f"Connected to display at i2c address {hex(i2c_addr)}")
        except:
            self.log.error(f"No device found at i2c address {hex(i2c_addr)}")
            self.active = False
            return
        
        self.i2c_addr = i2c_addr
        self.cols = cols
        self.rows = rows
        self.line_cmds = [0x80, 0xC0, 0x94, 0xD4]  # lines 1-4

        self.delay = 0.00001
        self.cls_delay = 0.0008
        self.type_data = 1
        self.type_command = 0
        self.enable = 0x04
        self.set_backlight(True)

        self.write(0x33, self.type_command)  # init sequence: 0x03, 0x03
        #        time.sleep(self.delay)
        self.write(0x32, self.type_command)  # init seq cont: 0x03, 0x02
        #        time.sleep(self.delay)
        self.write(0x06, self.type_command)  # cursor dir
        self.write(0x0C, self.type_command)  # display on, cursor off, blink of
        self.write(0x28, self.type_command)  # data len, num lines, font size
        self.write(0x01, self.type_command)  # clear (slow!)
        time.sleep(self.cls_delay)

        self.screen_buf = [[" " for _ in range(cols)] for _ in range(rows)]
        self.cur_row = 0
        self.cur_col = 0
        self.log.debug("LCD display initialized.")

    def set_backlight(self, state):
        if self.active is False:
            return
        if state:
            self.backlight = 0x08
        else:
            self.backlight = 0x00

    def write(self, byte, data_type):
        if self.active is False:
            return

        hi_byte = data_type | (byte & 0xF0) | self.backlight
        lo_byte = data_type | ((byte << 4) & 0xF0) | self.backlight

        self.bus.write_byte(self.i2c_addr, hi_byte)
        time.sleep(self.delay)
        self.bus.write_byte(self.i2c_addr, (hi_byte | self.enable))
        time.sleep(self.delay)
        self.bus.write_byte(self.i2c_addr, (hi_byte & ~self.enable))
        time.sleep(self.delay)

        self.bus.write_byte(self.i2c_addr, lo_byte)
        time.sleep(self.delay)
        self.bus.write_byte(self.i2c_addr, (lo_byte | self.enable))
        time.sleep(self.delay)
        self.bus.write_byte(self.i2c_addr, (lo_byte & ~self.enable))
        time.sleep(self.delay)

    def write_row(self, row):
        if self.active is False:
            return
        ra = self.line_cmds[row]
        self.write(ra, self.type_command)
        for i in range(self.cols):
            self.write(ord(self.screen_buf[row][i]), self.type_data)

    def print_row(self, row, text):
        if self.active is False:
            return
        if row < 0:
            row = 0
        if row >= self.rows:
            row = self.rows - 1
        text = text[: self.cols].ljust(self.cols, " ")
        self.screen_buf[row] = [text[i] for i in range(len(text))]
        self.write_row(row)

    def print_at(self, row, col, text):
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

    def scroll(self, n=1):
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

    def print(self, text):
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
    i2c_addr = 0x27
    lcd = LcdDisplay(1, i2c_addr, 20, 4)
    if lcd.active is True:
        print("Display is active, outputting a test-text to the display...")
        lcd.print(
            "Hello! That is a hell of a lot of text that we are going to display on this tiny screen. However there is always a way to present information in a way that is helpful, even under contrained conditions."
        )
        print("Done")
        exit(0)
    else:
        print("Failed to initialize display")
        exit(-1)
