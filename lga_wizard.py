from __future__ import division
import pcbnew

import FootprintWizardBase
import PadArray as PA


class LGAPadGridArray(PA.PadGridArray):
    """Pad grid with A1, A2 ... naming (skipping I and O)."""

    def NamingFunction(self, n_x, n_y):
        return "%s%d" % (
            self.AlphaNameFromNumber(
                n_y + 1,
                alphabet="ABCDEFGHJKLMNPRTUVWY",
            ),
            n_x + 1,
        )


class LGAWizard(FootprintWizardBase.FootprintWizard):
    """Generic rectangular LGA footprint wizard.

    Features:
    - Independent pitch in X and Y
    - Configurable columns/rows
    - Selectable pad shape: rect, round, roundrect
    - Configurable roundrect corner radius ratio
    - Pads on B.Cu/B.Mask/B.Paste (bottom side LGA)
    - IPC-style body outline, silkscreen and courtyard
    """

    def GetName(self):
        return "LGA (rectangular)"

    def GetDescription(self):
        return "Rectangular Land Grid Array Footprint Wizard"

    # -------------------------------------------------------------------------
    # Parameters
    # -------------------------------------------------------------------------

    def GenerateParameterList(self):
        # Pads
        self.AddParam("Pads", "pitch_x",          self.uMM,      1.00,       designator="px")
        self.AddParam("Pads", "pitch_y",          self.uMM,      1.00,       designator="py")
        self.AddParam("Pads", "size_x",           self.uMM,      0.50)
        self.AddParam("Pads", "size_y",           self.uMM,      0.50)
        self.AddParam("Pads", "shape",            self.uString,  "roundrect", hint="rect | round | roundrect")
        self.AddParam("Pads", "roundrect_ratio",  self.uFloat,   0.25,        hint="Corner radius ratio for roundrect (0.0-0.5)")
        self.AddParam("Pads", "columns",          self.uInteger, 5,           designator="nx")
        self.AddParam("Pads", "rows",             self.uInteger, 5,           designator="ny")

        # Package
        self.AddParam("Package", "width",  self.uMM, 6,    designator="X")
        self.AddParam("Package", "length", self.uMM, 6,    designator="Y")
        self.AddParam("Package", "margin", self.uMM, 0.25, min_value=0.2, hint="Courtyard margin")

    # -------------------------------------------------------------------------
    # Parameter validation
    # -------------------------------------------------------------------------

    def CheckParameters(self):
        pads = self.parameters["Pads"]

        width_min  = pcbnew.ToMM(pads["pitch_x"] * (pads["columns"] - 1))
        length_min = pcbnew.ToMM(pads["pitch_y"] * (pads["rows"]    - 1))

        self.CheckParam("Package", "width",
            min_value=width_min,
            info="Package width is too small (< {w}mm)".format(w=width_min))
        self.CheckParam("Package", "length",
            min_value=length_min,
            info="Package length is too small (< {l}mm)".format(l=length_min))

    # -------------------------------------------------------------------------
    # Value string
    # -------------------------------------------------------------------------

    def GetValue(self):
        pads = self.parameters["Pads"]
        pins = pads["rows"] * pads["columns"]
        return "LGA-{n}_{a}x{b}_{x}x{y}mm".format(
            n=pins,
            a=pads["columns"],
            b=pads["rows"],
            x=pcbnew.ToMM(self.parameters["Package"]["width"]),
            y=pcbnew.ToMM(self.parameters["Package"]["length"]),
        )

    # -------------------------------------------------------------------------
    # Build
    # -------------------------------------------------------------------------

    def BuildThisFootprint(self):
        pads = self.parameters["Pads"]

        rows    = pads["rows"]
        cols    = pads["columns"]
        size_x  = pads["size_x"]
        size_y  = pads["size_y"]
        pitch_x = pads["pitch_x"]
        pitch_y = pads["pitch_y"]
        rr_ratio = float(pads["roundrect_ratio"])

        shape_name = str(pads["shape"]).lower().strip()
        if shape_name.startswith("roundrect") or shape_name.startswith("rr"):
            shape = pcbnew.PAD_SHAPE_ROUNDRECT
        elif shape_name.startswith("round") or shape_name.startswith("circle"):
            shape = pcbnew.PAD_SHAPE_CIRCLE
        else:
            shape = pcbnew.PAD_SHAPE_RECT

        # --- Help messages in the log panel ----------------------------------
        self.buildmessages = ""
        self.buildmessages += "\n--- LGA Wizard Help ---\n"
        self.buildmessages += "\nPad shape options (field 'shape'):\n"
        self.buildmessages += "  rect      -> standard rectangle\n"
        self.buildmessages += "  round     -> circle/oval (size_x = diameter in X, size_y = diameter in Y)\n"
        self.buildmessages += "  roundrect -> rectangle with rounded corners (default, recommended for LGA)\n"
        self.buildmessages += "\nroundrect_ratio: corner radius as fraction of the shorter side (0.0 - 0.5).\n"
        self.buildmessages += "  Example: 0.25 -> corner radius = 25% of min(size_x, size_y)\n"
        self.buildmessages += "  Only used when shape = roundrect.\n"
        self.buildmessages += "\nsize_x / size_y:\n"
        self.buildmessages += "  rect/roundrect -> pad width (X) and height (Y)\n"
        self.buildmessages += "  round          -> diameter in X and Y (use equal values for a circle)\n"
        self.buildmessages += "\nAM5 reference values (estimated):\n"
        self.buildmessages += "  Body: 40.0 x 40.0 mm | pitch_x ~ 0.94 mm | pitch_y ~ 0.81 mm\n"
        self.buildmessages += "  Grid: ~46 columns x ~79 rows (1718 active lands out of ~3634 positions)\n"
        self.buildmessages += "-------------------------------\n"
        # ----------------------------------------------------------------------

        # SMD pad prototype on B.Cu/B.Mask/B.Paste
        pad_maker = PA.PadMaker(self.module)
        pad = pad_maker.SMDPad(
            Vsize=size_y,
            Hsize=size_x,
            shape=shape,
        )

        if shape == pcbnew.PAD_SHAPE_ROUNDRECT:
            ratio = max(0.0, min(0.5, rr_ratio))
            pad.SetRoundRectRadiusRatio(ratio)

        layers = pcbnew.LSET()
        layers.AddLayer(pcbnew.B_Cu)
        layers.AddLayer(pcbnew.B_Paste)
        layers.AddLayer(pcbnew.B_Mask)
        pad.SetLayerSet(layers)

        # Rectangular LGA array centred at origin
        array = LGAPadGridArray(pad, cols, rows, pitch_x, pitch_y)
        array.AddPadsToModule(self.draw)

        # --- F.Fab body outline ----------------------------------------------
        self.draw.SetLayer(pcbnew.F_Fab)
        ssx = self.parameters["Package"]["width"]  / 2
        ssy = self.parameters["Package"]["length"] / 2

        bevel = pcbnew.FromMM(1) if pcbnew.ToMM(ssx) >= 1 else ssx
        self.draw.BoxWithDiagonalAtCorner(0, 0, ssx * 2, ssy * 2, bevel)

        # --- F.SilkS silkscreen ----------------------------------------------
        self.draw.SetLayer(pcbnew.F_SilkS)
        offset = pcbnew.FromMM(0.15)
        len_x  = 0.5 * ssx
        len_y  = 0.5 * ssy

        edge = [
            [ssx + offset - len_x, -ssy - offset],
            [ssx + offset,          -ssy - offset],
            [ssx + offset,          -ssy - offset + len_y],
        ]
        self.draw.Polyline(edge)
        self.draw.Polyline(edge, mirrorY=0)
        self.draw.Polyline(edge, mirrorX=0, mirrorY=0)

        bevel_silk = bevel + offset
        pin1 = [
            [-ssx - offset + len_x,       -ssy - offset],
            [-ssx - offset + bevel_silk,  -ssy - offset],
            [-ssx - offset,               -ssy - offset + bevel_silk],
            [-ssx - offset,               -ssy - offset + len_y],
        ]
        if bevel_silk > len_x: pin1 = pin1[1:]
        if bevel_silk > len_y: pin1 = pin1[:-1]
        self.draw.Polyline(pin1)
        self.draw.Circle(-ssx, -ssy, pcbnew.FromMM(0.2), filled=True)

        # --- F.CrtYd courtyard -----------------------------------------------
        cmargin = self.parameters["Package"]["margin"]
        self.draw.SetLayer(pcbnew.F_CrtYd)
        sizex = pcbnew.PutOnGridMM((ssx + cmargin) * 2, 0.1)
        sizey = pcbnew.PutOnGridMM((ssy + cmargin) * 2, 0.1)

        self.draw.SetLineThickness(pcbnew.FromMM(0.05))
        self.draw.Box(0, 0, sizex, sizey)
        self.draw.SetLineThickness(pcbnew.FromMM(cmargin))

        # --- Ref / Value -----------------------------------------------------
        text_size = self.GetTextSize()
        ypos = ssy + text_size
        self.draw.Value(0,  ypos, text_size)
        self.draw.Reference(0, -ypos, text_size)


LGAWizard().register()
