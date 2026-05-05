import framebuf

# SSD1306 commands
SET_CONTRAST        = 0x81
SET_ENTIRE_ON       = 0xA4
SET_NORM_INV        = 0xA6
SET_DISP            = 0xAE
SET_MEM_ADDR        = 0x20
SET_COL_ADDR        = 0x21
SET_PAGE_ADDR       = 0x22
SET_DISP_START_LINE = 0x40
SET_SEG_REMAP       = 0xA0
SET_MUX_RATIO       = 0xA8
SET_COM_OUT_DIR     = 0xC0
SET_DISP_OFFSET     = 0xD3
SET_COM_PIN_CFG     = 0xDA
SET_DISP_CLK_DIV    = 0xD5
SET_PRECHARGE       = 0xD9
SET_VCOM_DESEL      = 0xDB
SET_CHARGE_PUMP     = 0x8D


class SSD1306:
    def __init__(self, i2c, addr=0x3C, width=72, height=40):
        self.i2c = i2c
        self.addr = addr
        self.width = width
        self.height = height
        self.inverted = False
        # Column offset for 72x40 display (centered in 128-wide RAM)
        self.col_offset = (128 - width) // 2  # 28
        self.buf = bytearray(width * height // 8)
        self.fb = framebuf.FrameBuffer(self.buf, width, height, framebuf.MONO_VLSB)
        self._init()

    def _cmd(self, cmd):
        self.i2c.writeto(self.addr, bytes([0x00, cmd]))

    def _init(self):
        for cmd in [
            SET_DISP,
            SET_MEM_ADDR, 0x00,
            SET_DISP_START_LINE,
            SET_SEG_REMAP | 0x01,
            SET_MUX_RATIO, self.height - 1,    # 39 for 40px
            SET_COM_OUT_DIR | 0x08,
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x12,              # alternative COM pin config for 40px
            SET_DISP_CLK_DIV, 0xF0,
            SET_PRECHARGE, 0xF1,
            SET_VCOM_DESEL, 0x30,
            SET_CONTRAST, 0xFF,
            SET_ENTIRE_ON,
            SET_NORM_INV,
            SET_CHARGE_PUMP, 0x14,
            SET_DISP | 0x01,
        ]:
            self._cmd(cmd)

    def invert(self, on):
        self.inverted = on
        self._cmd(SET_NORM_INV | (1 if on else 0))

    def show(self):
        self._cmd(SET_COL_ADDR);  self._cmd(self.col_offset); self._cmd(self.col_offset + self.width - 1)
        self._cmd(SET_PAGE_ADDR); self._cmd(0); self._cmd(self.height // 8 - 1)
        self.i2c.writeto(self.addr, b'\x40' + self.buf)

    def fill(self, c):   self.fb.fill(c)
    def text(self, s, x, y, c=1): self.fb.text(s, x, y, c)

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
