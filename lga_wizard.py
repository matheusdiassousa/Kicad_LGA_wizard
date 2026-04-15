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
    """Generic rectangular LGA footprint wizard (pitch X/Y independentes).

    Features:
    - Pitch independente em X e Y
    - Número de colunas/linhas configurável
    - Corpo retangular com bevel IPC na F.Fab
    - Silk de orientação em F.SilkS
    - Courtyard em F.CrtYd
    - Pads SMD criados por padrão em B.Cu/B.Mask/B.Paste (LGA na face de baixo)
    """

    def GetName(self):
        return "LGA (rectangular)"

    def GetDescription(self):
        return "Rectangular Land Grid Array Footprint Wizard (pitch X/Y independentes)"

    # -------------------------------------------------------------------------
    # Parâmetros
    # -------------------------------------------------------------------------

    def GenerateParameterList(self):
        # Pads
        self.AddParam("Pads", "pitch_x", self.uMM, 1.00, designator="px")
        self.AddParam("Pads", "pitch_y", self.uMM, 1.00, designator="py")
        self.AddParam("Pads", "size_x", self.uMM, 0.50)
        self.AddParam("Pads", "size_y", self.uMM, 0.50)
        self.AddParam("Pads", "shape", self.uString, "roundrect", hint="rect | round | roundrect")
        self.AddParam("Pads", "columns", self.uInteger, 5, designator="nx")
        self.AddParam("Pads", "rows", self.uInteger, 5, designator="ny")

        # Corpo
        self.AddParam("Package", "width", self.uMM, 6, designator="X")
        self.AddParam("Package", "length", self.uMM, 6, designator="Y")
        self.AddParam(
            "Package",
            "margin",
            self.uMM,
            0.25,
            min_value=0.2,
            hint="Courtyard margin",
        )

    # -------------------------------------------------------------------------
    # Validação de parâmetros
    # -------------------------------------------------------------------------

    def CheckParameters(self):
        pads = self.parameters["Pads"]

        width_min = pcbnew.ToMM(pads["pitch_x"] * (pads["columns"] - 1))
        length_min = pcbnew.ToMM(pads["pitch_y"] * (pads["rows"] - 1))

        self.CheckParam(
            "Package",
            "width",
            min_value=width_min,
            info="Package width is too small (< {w}mm)".format(w=width_min),
        )
        self.CheckParam(
            "Package",
            "length",
            min_value=length_min,
            info="Package length is too small (< {l}mm)".format(l=length_min),
        )

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
    # Construção do footprint
    # -------------------------------------------------------------------------

    def BuildThisFootprint(self):
        pads = self.parameters["Pads"]

        rows = pads["rows"]
        cols = pads["columns"]
        size_x = pads["size_x"]
        size_y = pads["size_y"]
        pitch_x = pads["pitch_x"]
        pitch_y = pads["pitch_y"]

        shape_name = str(pads["shape"]).lower().strip()
        if shape_name.startswith("roundrect") or shape_name.startswith("rr"):
            shape = pcbnew.PAD_SHAPE_ROUNDRECT
        elif shape_name.startswith("round") or shape_name.startswith("circle"):
            shape = pcbnew.PAD_SHAPE_CIRCLE
        else:
            shape = pcbnew.PAD_SHAPE_RECT

        # Protótipo de pad SMD em B.Cu/B.Mask/B.Paste
        pad_maker = PA.PadMaker(self.module)
        pad = pad_maker.SMDPad(
            Vsize=size_y,
            Hsize=size_x,
            shape=shape,
        )

        layers = pcbnew.LSET()
        layers.AddLayer(pcbnew.B_Cu)
        layers.AddLayer(pcbnew.B_Paste)
        layers.AddLayer(pcbnew.B_Mask)
        pad.SetLayerSet(layers)

        # Matriz retangular LGA centrada na origem
        array = LGAPadGridArray(pad, cols, rows, pitch_x, pitch_y)
        array.AddPadsToModule(self.draw)

        # ---------------- Corpo mecânico em F.Fab ----------------
        self.draw.SetLayer(pcbnew.F_Fab)
        ssx = self.parameters["Package"]["width"] / 2
        ssy = self.parameters["Package"]["length"] / 2

        if pcbnew.ToMM(ssx) < 1:
            bevel = ssx
        else:
            bevel = pcbnew.FromMM(1)

        self.draw.BoxWithDiagonalAtCorner(0, 0, ssx * 2, ssy * 2, bevel)

        # ---------------- Serigrafia F.SilkS ----------------
        self.draw.SetLayer(pcbnew.F_SilkS)
        offset = pcbnew.FromMM(0.15)
        len_x = 0.5 * ssx
        len_y = 0.5 * ssy

        edge = [
            [ssx + offset - len_x, -ssy - offset],
            [ssx + offset, -ssy - offset],
            [ssx + offset, -ssy - offset + len_y],
        ]

        self.draw.Polyline(edge)
        self.draw.Polyline(edge, mirrorY=0)
        self.draw.Polyline(edge, mirrorX=0, mirrorY=0)

        bevel_silk = bevel + offset
        pin1 = [
            [-ssx - offset + len_x, -ssy - offset],
            [-ssx - offset + bevel_silk, -ssy - offset],
            [-ssx - offset, -ssy - offset + bevel_silk],
            [-ssx - offset, -ssy - offset + len_y],
        ]

        if bevel_silk > len_x:
            pin1 = pin1[1:]
        if bevel_silk > len_y:
            pin1 = pin1[:-1]

        self.draw.Polyline(pin1)
        self.draw.Circle(-ssx, -ssy, pcbnew.FromMM(0.2), filled=True)

        # ---------------- Courtyard em F.CrtYd ----------------
        cmargin = self.parameters["Package"]["margin"]
        self.draw.SetLayer(pcbnew.F_CrtYd)
        sizex = (ssx + cmargin) * 2
        sizey = (ssy + cmargin) * 2

        sizex = pcbnew.PutOnGridMM(sizex, 0.1)
        sizey = pcbnew.PutOnGridMM(sizey, 0.1)

        self.draw.SetLineThickness(pcbnew.FromMM(0.05))
        self.draw.Box(0, 0, sizex, sizey)
        self.draw.SetLineThickness(pcbnew.FromMM(cmargin))

        # ---------------- Ref / Value ----------------
        text_size = self.GetTextSize()
        ypos = ssy + text_size
        self.draw.Value(0, ypos, text_size)
        self.draw.Reference(0, -ypos, text_size)


LGAWizard().register()
