import framebuf

_SET_CONTRAST        = 0x81
_SET_ENTIRE_ON       = 0xA4
_SET_NORM_INV        = 0xA6
_SET_DISP            = 0xAE
_SET_MEM_ADDR        = 0x20
_SET_COL_ADDR        = 0x21
_SET_PAGE_ADDR       = 0x22
_SET_DISP_START_LINE = 0x40
_SET_SEG_REMAP       = 0xA0
_SET_MUX_RATIO       = 0xA8
_SET_COM_OUT_DIR     = 0xC0
_SET_DISP_OFFSET     = 0xD3
_SET_COM_PIN_CFG     = 0xDA
_SET_DISP_CLK_DIV    = 0xD5
_SET_PRECHARGE       = 0xD9
_SET_VCOM_DESEL      = 0xDB
_SET_CHARGE_PUMP     = 0x8D


class SSD1306:
    """Static driver — knows the SSD1306 I2C protocol. No state."""

    @staticmethod
    def _cmd(i2c, addr, cmd):
        i2c.writeto(addr, bytes([0x00, cmd]))

    @staticmethod
    def init(i2c, addr, width, height):
        cmd = SSD1306._cmd
        for c in [
            _SET_DISP,
            _SET_MEM_ADDR,        0x00,
            _SET_DISP_START_LINE,
            _SET_SEG_REMAP | 0x01,
            _SET_MUX_RATIO,       height - 1,
            _SET_COM_OUT_DIR | 0x08,
            _SET_DISP_OFFSET,     0x00,
            _SET_COM_PIN_CFG,     0x12,
            _SET_DISP_CLK_DIV,    0xF2,
            _SET_PRECHARGE,       0xF1,
            _SET_VCOM_DESEL,      0x30,
            _SET_CONTRAST,        0xFF,
            _SET_ENTIRE_ON,
            _SET_NORM_INV,
            _SET_CHARGE_PUMP,     0x14,
            _SET_DISP | 0x01,
        ]:
            cmd(i2c, addr, c)

    @staticmethod
    def flush(i2c, addr, buf, width, height):
        col_offset = (128 - width) // 2
        cmd = SSD1306._cmd
        cmd(i2c, addr, _SET_COL_ADDR);  cmd(i2c, addr, col_offset); cmd(i2c, addr, col_offset + width - 1)
        cmd(i2c, addr, _SET_PAGE_ADDR); cmd(i2c, addr, 0);          cmd(i2c, addr, height // 8 - 1)
        i2c.writeto(addr, b'\x40' + buf)

    @staticmethod
    def set_invert(i2c, addr, on):
        SSD1306._cmd(i2c, addr, _SET_NORM_INV | (1 if on else 0))


class Display:
    """Instance — owns framebuffer and connection to one physical SSD1306 chip."""

    def __init__(self, i2c, addr=0x3C, width=72, height=40):
        self.i2c    = i2c
        self.addr   = addr
        self.width  = width
        self.height = height
        self.buf = bytearray(width * height // 8)
        self.fb  = framebuf.FrameBuffer(self.buf, width, height, framebuf.MONO_VLSB)
        SSD1306.init(i2c, addr, width, height)

    def show(self):
        SSD1306.flush(self.i2c, self.addr, self.buf, self.width, self.height)

    def invert(self, on):
        SSD1306.set_invert(self.i2c, self.addr, on)

    def fill(self, c):
        self.fb.fill(c)

    def text(self, s, x, y, c=1):
        self.fb.text(s, x, y, c)

    def large_text(self, s, x, y, scale=3, char_pitch=8):
        """Draw text scaled up by integer factor.
        char_pitch: source-pixel advance per character (default 8).
                    Use 7 to tighten horizontal spacing by one pixel column per char.
        """
        temp = bytearray(len(s) * 8)
        tf = framebuf.FrameBuffer(temp, len(s) * 8, 8, framebuf.MONO_VLSB)
        tf.fill(0)
        tf.text(s, 0, 0, 1)
        for cy in range(8):
            for ci in range(len(s)):
                for col in range(8):
                    if tf.pixel(ci * 8 + col, cy):
                        self.fb.fill_rect(x + (ci * char_pitch + col) * scale,
                                          y + cy * scale, scale, scale, 1)

    def large_text_adv(self, s, x, y, scale=3, advances=None):
        """Draw scaled text with per-character advances.
        advances is a list of source-pixel advances, one per character.
        The last character's advance is ignored for width; its full 8px bitmap is drawn.
        """
        if advances is None or len(advances) != len(s):
            advances = [8] * len(s)

        temp = bytearray(len(s) * 8)
        tf = framebuf.FrameBuffer(temp, len(s) * 8, 8, framebuf.MONO_VLSB)
        tf.fill(0)
        tf.text(s, 0, 0, 1)

        x_cursor = 0
        for ci in range(len(s)):
            for cy in range(8):
                for col in range(8):
                    if tf.pixel(ci * 8 + col, cy):
                        self.fb.fill_rect(x + (x_cursor + col) * scale,
                                          y + cy * scale, scale, scale, 1)
            x_cursor += advances[ci]

    def ble_icon(self, x, y, c=1):
        """Draw a 5x7 Bluetooth symbol at (x, y).
        Spine + upper/lower right arms, mirrored left notches:
          . # .
          # # .   <- right arm up
          . # #
          . # .   <- spine mid
          . # #
          # # .   <- right arm down
          . # .
        """
        _PX = (
            (1, 0), (1, 1), (0, 1),
            (1, 2), (2, 2),
            (1, 3),
            (1, 4), (2, 4),
            (1, 5), (0, 5),
            (1, 6),
        )
        for dx, dy in _PX:
            self.fb.pixel(x + dx, y + dy, c)
