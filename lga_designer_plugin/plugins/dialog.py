import wx
import wx.lib.scrolledpanel as scrolled
import pcbnew
import os

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CELL_SIZE  = 14   # px per pad cell in the grid canvas
CELL_PAD   = 2    # px gap between cells
STEP       = CELL_SIZE + CELL_PAD

COLOR_ON   = wx.Colour(70, 130, 180)   # steel blue  – active pad
COLOR_OFF  = wx.Colour(40, 40,  40)    # dark grey   – removed pad
COLOR_BG   = wx.Colour(20, 20,  20)    # background
COLOR_LBL  = wx.Colour(160, 200, 255)  # label text


# ---------------------------------------------------------------------------
# Interactive grid canvas
# ---------------------------------------------------------------------------
class PadGridCanvas(wx.Panel):
    """Draws an n_col x n_row grid of clickable pad cells."""

    def __init__(self, parent, n_cols, n_rows):
        self.n_cols = n_cols
        self.n_rows = n_rows
        # active[row][col] = True/False
        self.active = [[True] * n_cols for _ in range(n_rows)]

        w = n_cols * STEP + CELL_PAD
        h = n_rows * STEP + CELL_PAD
        super().__init__(parent, size=(w, h))
        self.SetMinSize((w, h))
        self.SetBackgroundColour(COLOR_BG)

        self.Bind(wx.EVT_PAINT,       self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN,   self.OnClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnClick)

    # ------------------------------------------------------------------
    def rebuild(self, n_cols, n_rows):
        self.n_cols = n_cols
        self.n_rows = n_rows
        self.active = [[True] * n_cols for _ in range(n_rows)]
        w = n_cols * STEP + CELL_PAD
        h = n_rows * STEP + CELL_PAD
        self.SetMinSize((w, h))
        self.SetSize((w, h))
        self.GetParent().SetupScrolling(scroll_x=True, scroll_y=True)
        self.Refresh()

    # ------------------------------------------------------------------
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(COLOR_BG))
        dc.Clear()
        for r in range(self.n_rows):
            for c in range(self.n_cols):
                colour = COLOR_ON if self.active[r][c] else COLOR_OFF
                dc.SetBrush(wx.Brush(colour))
                dc.SetPen(wx.TRANSPARENT_PEN)
                x = CELL_PAD + c * STEP
                y = CELL_PAD + r * STEP
                dc.DrawRoundedRectangle(x, y, CELL_SIZE, CELL_SIZE, 2)

    # ------------------------------------------------------------------
    def OnClick(self, event):
        x, y = event.GetPosition()
        c = (x - CELL_PAD) // STEP
        r = (y - CELL_PAD) // STEP
        if 0 <= r < self.n_rows and 0 <= c < self.n_cols:
            self.active[r][c] = not self.active[r][c]
            self.Refresh()

    # ------------------------------------------------------------------
    def get_active_set(self):
        """Return set of (row, col) for active pads."""
        result = set()
        for r in range(self.n_rows):
            for c in range(self.n_cols):
                if self.active[r][c]:
                    result.add((r, c))
        return result

    def select_all(self):
        self.active = [[True] * self.n_cols for _ in range(self.n_rows)]
        self.Refresh()

    def select_none(self):
        self.active = [[False] * self.n_cols for _ in range(self.n_rows)]
        self.Refresh()


# ---------------------------------------------------------------------------
# Main dialog
# ---------------------------------------------------------------------------
class LGADesignerDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="LGA Footprint Designer",
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self._build_ui()
        self.SetSize((900, 700))
        self.Centre()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = wx.BoxSizer(wx.HORIZONTAL)

        # ---- LEFT PANEL: parameters ------------------------------------
        left = wx.BoxSizer(wx.VERTICAL)

        def addrow(label, ctrl):
            row = wx.BoxSizer(wx.HORIZONTAL)
            row.Add(wx.StaticText(self, label=label), 0,
                    wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
            row.Add(ctrl, 1, wx.EXPAND)
            left.Add(row, 0, wx.EXPAND | wx.BOTTOM, 6)

        # Footprint name
        self.txt_name = wx.TextCtrl(self, value="LGA_Custom")
        addrow("Footprint name:", self.txt_name)

        # Grid size
        self.sp_cols = wx.SpinCtrl(self, value="10", min=1, max=200)
        self.sp_rows = wx.SpinCtrl(self, value="10", min=1, max=200)
        addrow("Columns:", self.sp_cols)
        addrow("Rows:",    self.sp_rows)

        # Pitch
        self.sc_pitch_x = wx.SpinCtrlDouble(self, value="1.00", min=0.1, max=10.0, inc=0.05)
        self.sc_pitch_y = wx.SpinCtrlDouble(self, value="1.00", min=0.1, max=10.0, inc=0.05)
        self.sc_pitch_x.SetDigits(3)
        self.sc_pitch_y.SetDigits(3)
        addrow("Pitch X (mm):", self.sc_pitch_x)
        addrow("Pitch Y (mm):", self.sc_pitch_y)

        # Pad size
        self.sc_size_x = wx.SpinCtrlDouble(self, value="0.50", min=0.05, max=5.0, inc=0.05)
        self.sc_size_y = wx.SpinCtrlDouble(self, value="0.50", min=0.05, max=5.0, inc=0.05)
        self.sc_size_x.SetDigits(3)
        self.sc_size_y.SetDigits(3)
        addrow("Pad size X (mm):", self.sc_size_x)
        addrow("Pad size Y (mm):", self.sc_size_y)

        # Pad shape
        self.ch_shape = wx.Choice(self, choices=["roundrect", "rect", "round"])
        self.ch_shape.SetSelection(0)
        addrow("Pad shape:", self.ch_shape)

        # Roundrect ratio
        self.sc_rr = wx.SpinCtrlDouble(self, value="0.25", min=0.0, max=0.5, inc=0.05)
        self.sc_rr.SetDigits(2)
        addrow("Roundrect ratio:", self.sc_rr)

        # Soldermask
        self.ch_mask = wx.Choice(self, choices=["SMD (mask expansion = 0)",
                                                "NSMD (no solder mask)"])
        self.ch_mask.SetSelection(0)
        addrow("Soldermask:", self.ch_mask)

        # Staggered
        self.cb_stagger = wx.CheckBox(self, label="Staggered grid (offset every other column)")
        left.Add(self.cb_stagger, 0, wx.BOTTOM, 6)

        self.sc_stagger = wx.SpinCtrlDouble(self, value="0.5", min=0.0, max=1.0, inc=0.1)
        self.sc_stagger.SetDigits(2)
        addrow("Stagger offset (fraction of pitch Y):", self.sc_stagger)

        # Separator
        left.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 8)

        # Grid controls
        btn_rebuild = wx.Button(self, label="Rebuild grid")
        btn_all     = wx.Button(self, label="Select all")
        btn_none    = wx.Button(self, label="Select none")
        for b in (btn_rebuild, btn_all, btn_none):
            left.Add(b, 0, wx.EXPAND | wx.BOTTOM, 4)

        btn_rebuild.Bind(wx.EVT_BUTTON, self.OnRebuild)
        btn_all.Bind(wx.EVT_BUTTON,     lambda e: self.canvas.select_all())
        btn_none.Bind(wx.EVT_BUTTON,    lambda e: self.canvas.select_none())

        # Separator
        left.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 8)

        # Active pad count label
        self.lbl_count = wx.StaticText(self, label="Active pads: -")
        left.Add(self.lbl_count, 0, wx.BOTTOM, 4)

        # Generate button
        btn_gen = wx.Button(self, label="Generate footprint")
        btn_gen.SetBackgroundColour(wx.Colour(0, 120, 60))
        btn_gen.SetForegroundColour(wx.WHITE)
        left.Add(btn_gen, 0, wx.EXPAND | wx.TOP, 4)
        btn_gen.Bind(wx.EVT_BUTTON, self.OnGenerate)

        # Close
        btn_close = wx.Button(self, label="Close")
        left.Add(btn_close, 0, wx.EXPAND | wx.TOP, 4)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))

        # ---- RIGHT PANEL: scrolled pad grid ----------------------------
        self.scroll = scrolled.ScrolledPanel(self, style=wx.SUNKEN_BORDER)
        self.scroll.SetBackgroundColour(COLOR_BG)

        n_cols = self.sp_cols.GetValue()
        n_rows = self.sp_rows.GetValue()
        self.canvas = PadGridCanvas(self.scroll, n_cols, n_rows)

        scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        scroll_sizer.Add(self.canvas, 0, wx.ALL, 4)
        self.scroll.SetSizer(scroll_sizer)
        self.scroll.SetupScrolling(scroll_x=True, scroll_y=True)

        # Help text below canvas
        help_txt = ("Click a pad to toggle it on/off. "
                    "Blue = active  |  Dark = removed.")
        lbl_help = wx.StaticText(self.scroll, label=help_txt)
        lbl_help.SetForegroundColour(COLOR_LBL)
        scroll_sizer.Add(lbl_help, 0, wx.ALL, 6)

        # Timer to update count label
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._update_count, self.timer)
        self.timer.Start(500)

        # Compose root sizer
        root.Add(left, 0, wx.EXPAND | wx.ALL, 12)
        root.Add(self.scroll, 1, wx.EXPAND | wx.ALL, 6)
        self.SetSizer(root)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _update_count(self, event=None):
        n = len(self.canvas.get_active_set())
        self.lbl_count.SetLabel("Active pads: {}".format(n))

    def OnRebuild(self, event):
        n_cols = self.sp_cols.GetValue()
        n_rows = self.sp_rows.GetValue()
        self.canvas.rebuild(n_cols, n_rows)
        self.scroll.SetupScrolling(scroll_x=True, scroll_y=True)
        self.scroll.Layout()
        self._update_count()

    # ------------------------------------------------------------------
    # Footprint generation
    # ------------------------------------------------------------------
    def OnGenerate(self, event):
        import pcbnew

        name    = self.txt_name.GetValue().strip() or "LGA_Custom"
        pitch_x = pcbnew.FromMM(self.sc_pitch_x.GetValue())
        pitch_y = pcbnew.FromMM(self.sc_pitch_y.GetValue())
        size_x  = pcbnew.FromMM(self.sc_size_x.GetValue())
        size_y  = pcbnew.FromMM(self.sc_size_y.GetValue())
        rr_ratio = self.sc_rr.GetValue()
        stagger  = self.cb_stagger.GetValue()
        stagger_offset = pcbnew.FromMM(
            self.sc_stagger.GetValue() * self.sc_pitch_y.GetValue())

        shape_idx = self.ch_shape.GetSelection()
        shape_map = {
            0: pcbnew.PAD_SHAPE_ROUNDRECT,
            1: pcbnew.PAD_SHAPE_RECT,
            2: pcbnew.PAD_SHAPE_CIRCLE,
        }
        shape = shape_map.get(shape_idx, pcbnew.PAD_SHAPE_ROUNDRECT)

        nsmd = (self.ch_mask.GetSelection() == 1)  # True = NSMD

        active = self.canvas.get_active_set()
        if not active:
            wx.MessageBox("No active pads to generate!",
                          "LGA Designer", wx.OK | wx.ICON_WARNING)
            return

        # -- Build footprint ----------------------------------------------
        fp = pcbnew.FOOTPRINT(None)
        fp.SetReference("REF**")
        fp.SetValue(name)

        # Alphabet without I and O
        ALPHA = "ABCDEFGHJKLMNPRTUVWY"

        def row_label(r):
            """Convert 0-based row index to spreadsheet-style letter label."""
            label = ""
            r += 1
            while r > 0:
                r, rem = divmod(r - 1, len(ALPHA))
                label = ALPHA[rem] + label
            return label

        n_cols = self.sp_cols.GetValue()
        n_rows = self.sp_rows.GetValue()

        # Centre offset so array is centred at origin
        origin_x = -(n_cols - 1) * pitch_x // 2
        origin_y = -(n_rows - 1) * pitch_y // 2

        for r, c in sorted(active):
            pad = pcbnew.PAD(fp)
            pad.SetSize(pcbnew.VECTOR2I(size_x, size_y))
            pad.SetShape(shape)

            if shape == pcbnew.PAD_SHAPE_ROUNDRECT:
                pad.SetRoundRectRadiusRatio(max(0.0, min(0.5, rr_ratio)))

            pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)

            # Layers: B.Cu + B.Paste always; B.Mask only for SMD
            layers = pcbnew.LSET()
            layers.AddLayer(pcbnew.B_Cu)
            layers.AddLayer(pcbnew.B_Paste)
            if not nsmd:
                layers.AddLayer(pcbnew.B_Mask)
            pad.SetLayerSet(layers)

            if nsmd:
                # NSMD: mask expansion negative so mask doesn't cover the pad
                pad.SetLocalSolderMaskMargin(-pcbnew.FromMM(0.05))

            # Position
            x = origin_x + c * pitch_x
            y = origin_y + r * pitch_y
            if stagger and (c % 2 == 1):
                y += stagger_offset

            pad.SetPosition(pcbnew.VECTOR2I(x, y))
            pad.SetNumber("{}{}".format(row_label(r), c + 1))

            fp.Add(pad)

        # -- Save footprint into current board's rescue lib ----------------
        board = pcbnew.GetBoard()
        if not board:
            wx.MessageBox("No board loaded – open a board to attach the new footprint.",
                          "LGA Designer", wx.OK | wx.ICON_WARNING)
            return

        lib = pcbnew.FootprintLibsTable()
        # For now, just show the footprint in a preview dialog
        from pcbnew import FOOTPRINT_VIEWER_FRAME

        viewer = FOOTPRINT_VIEWER_FRAME(None)
        viewer.ShowFootprint(fp)
        viewer.Show(True)

        wx.MessageBox("Footprint generated and opened in viewer.\n"
                      "You can now save it to any library.",
                      "LGA Designer", wx.OK | wx.ICON_INFORMATION)
