import time
from machine import Pin

# Commands
LCD_CLEARDISPLAY        = 0x01
LCD_RETURNHOME          = 0x02
LCD_ENTRYMODESET        = 0x04
LCD_DISPLAYCONTROL      = 0x08
LCD_CURSORSHIFT         = 0x10
LCD_FUNCTIONSET         = 0x20
LCD_SETCGRAMADDR        = 0x40
LCD_SETDDRAMADDR        = 0x80

# Entry flags
LCD_ENTRYRIGHT          = 0x00
LCD_ENTRYLEFT           = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# Control flags
LCD_DISPLAYON           = 0x04
LCD_DISPLAYOFF          = 0x00
LCD_CURSORON            = 0x02
LCD_CURSOROFF           = 0x00
LCD_BLINKON             = 0x01
LCD_BLINKOFF            = 0x00

# Move flags
LCD_DISPLAYMOVE         = 0x08
LCD_CURSORMOVE          = 0x00
LCD_MOVERIGHT           = 0x04
LCD_MOVELEFT            = 0x00

# Function set flags
LCD_8BITMODE            = 0x10
LCD_4BITMODE            = 0x00
LCD_2LINE               = 0x08
LCD_1LINE               = 0x00
LCD_5x10DOTS            = 0x04
LCD_5x8DOTS             = 0x00

# Offset for up to 4 rows.
LCD_ROW_OFFSETS         = (0x00, 0x40, 0x14, 0x54)

class CharLCD(object):
    def __init__(self, rs, en, d4, d5, d6, d7, cols, lines):
        # Save column and line state.
        self._cols = cols
        self._lines = lines
        # Setup all pins as outputs.
        self._rs = Pin(rs, mode=Pin.OUT, pull=Pin.PULL_DOWN, value=0)
        self._en = Pin(en, mode=Pin.OUT, pull=Pin.PULL_DOWN, value=0)
        self._d4 = Pin(d4, mode=Pin.OUT, pull=Pin.PULL_DOWN, value=0)
        self._d5 = Pin(d5, mode=Pin.OUT, pull=Pin.PULL_DOWN, value=0)
        self._d6 = Pin(d6, mode=Pin.OUT, pull=Pin.PULL_DOWN, value=0)
        self._d7 = Pin(d7, mode=Pin.OUT, pull=Pin.PULL_DOWN, value=0)
  
        # Initialize the display.
        self.write8(0x33)
        self.write8(0x32)
        # Initialize display control, function, and mode registers.
        self.displaycontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF
        self.displayfunction = LCD_4BITMODE | LCD_1LINE | LCD_2LINE | LCD_5x8DOTS
        self.displaymode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT
        # Write registers.
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write8(LCD_FUNCTIONSET | self.displayfunction)
        self.write8(LCD_ENTRYMODESET | self.displaymode)  # set the entry mode
        self.clear()

    def home(self):
        """Move the cursor back to its home (first line and first column)."""
        self.write8(LCD_RETURNHOME)  # set cursor position to zero
        self._delay_microseconds(10000)  # this command takes a long time!

    def clear(self):
        """Clear the LCD."""
        self.write8(LCD_CLEARDISPLAY)  # command to clear display
        self._delay_microseconds(10000)  # 3000 microsecond sleep, clearing the display takes a long time

    def set_cursor(self, col, row):
        """Move the cursor to an explicit column and row position."""
        # Clamp row to the last row of the display.
        if row > self._lines:
            row = self._lines - 1
        # Set location.
        self.write8(LCD_SETDDRAMADDR | (col + LCD_ROW_OFFSETS[row]))

    def enable_display(self, enable):
        """Enable or disable the display.  Set enable to True to enable."""
        if enable:
            self.displaycontrol |= LCD_DISPLAYON
        else:
            self.displaycontrol &= ~LCD_DISPLAYON
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)

    def show_cursor(self, show):
        """Show or hide the cursor.  Cursor is shown if show is True."""
        if show:
            self.displaycontrol |= LCD_CURSORON
        else:
            self.displaycontrol &= ~LCD_CURSORON
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)

    def blink(self, blink):
        """Turn on or off cursor blinking.  Set blink to True to enable blinking."""
        if blink:
            self.displaycontrol |= LCD_BLINKON
        else:
            self.displaycontrol &= ~LCD_BLINKON
        self.write8(LCD_DISPLAYCONTROL | self.displaycontrol)

    def move_left(self):
        """Move display left one position."""
        self.write8(LCD_CURSORSHIFT | LCD_DISPLAYMOVE | LCD_MOVELEFT)

    def move_right(self):
        """Move display right one position."""
        self.write8(LCD_CURSORSHIFT | LCD_DISPLAYMOVE | LCD_MOVERIGHT)

    def set_left_to_right(self):
        """Set text direction left to right."""
        self.displaymode |= LCD_ENTRYLEFT
        self.write8(LCD_ENTRYMODESET | self.displaymode)

    def set_right_to_left(self):
        """Set text direction right to left."""
        self.displaymode &= ~LCD_ENTRYLEFT
        self.write8(LCD_ENTRYMODESET | self.displaymode)

    def autoscroll(self, autoscroll):
        """Autoscroll will 'right justify' text from the cursor if set True,
        otherwise it will 'left justify' the text.
        """
        if autoscroll:
            self.displaymode |= LCD_ENTRYSHIFTINCREMENT
        else:
            self.displaymode &= ~LCD_ENTRYSHIFTINCREMENT
        self.write8(LCD_ENTRYMODESET | self.displaymode)

    def message(self, text):
        """Write text to display. Note that text can include newlines."""
        line = 0
        # Iterate through each character.
        for char in text:
            # Advance to next line if character is a new line.
            if char == '\n':
                line += 1
                # Move to left or right side depending on text direction.
                col = 0 if self.displaymode & LCD_ENTRYLEFT > 0 else self._cols-1
                self.set_cursor(col, line)
            # Write the character to the display.
            else:
                self.write8(ord(char), True)

    def write8(self, value, char_mode=False):
        """Write 8-bit value in character or data mode.  Value should be an int
        value from 0-255, and char_mode is True if character data or False if
        non-character data (default).
        """
        # One millisecond delay to prevent writing too quickly.
        time.sleep_us(1000)
        # Set character / data bit.
        self._rs(char_mode)
        # Write upper 4 bits.
        self._d4((value >> 4) & 1)
        self._d5((value >> 5) & 1)
        self._d6((value >> 6) & 1)
        self._d7((value >> 7) & 1)
        self._pulse_enable()
        # Write lower 4 bits.
        self._d4(value        & 1)
        self._d5((value >> 1) & 1)
        self._d6((value >> 2) & 1)
        self._d7((value >> 3) & 1)
        self._pulse_enable()

    def create_char(self, location, pattern):
          # only position 0..7 are allowed
        location &= 0x7
        self.write8(LCD_SETCGRAMADDR | (location << 3))
        for i in range(8):
            self.write8(pattern[i], char_mode=True)

    def _delay_microseconds(self, microseconds):
        time.sleep_ms(microseconds // 1000)

    def _pulse_enable(self):
        # Pulse the clock enable line off, on, off to send command.
        self._en(0)
        time.sleep_us(5)
        self._en(1)
        time.sleep_us(5)
        self._en(0)
        time.sleep_us(50)
