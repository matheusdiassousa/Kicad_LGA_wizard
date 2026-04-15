import pcbnew


class LGADesignerPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "LGA Footprint Designer"
        self.category = "Footprint"
        self.description = "Interactive LGA footprint generator with clickable pad grid"
        self.show_toolbar_button = True
        self.icon_file_name = ""

    def Run(self):
        import wx
        from .dialog import LGADesignerDialog
        dlg = LGADesignerDialog(None)
        dlg.ShowModal()
        dlg.Destroy()
