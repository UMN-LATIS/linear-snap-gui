import wx;

from PyQt5.QtWidgets import (QFileDialog, QDialog, QListView, QAbstractItemView, QTreeView)

class PreferencesEditor(wx.PreferencesEditor):
	def __init__(self, config):
		super().__init__('Preferences')
		self.general = GeneralPreferencesPage(config)
		self.camera = CameraPrefs(config)
		self.AddPage(self.general)
		self.AddPage(self.camera)
		
		

class GeneralPreferencesPage(wx.StockPreferencesPage):
	def __init__(self, config):
		super().__init__(wx.StockPreferencesPage.Kind_General)
		self.config = config

	def CreateWindow(self, parent):
		# THe main container window

		panel = wx.Panel(parent)
		panel.SetMinSize((600, 430))
		fgSizer1 = wx.FlexGridSizer( 0, 3, 0, 0 )
		fgSizer1.AddGrowableCol( 1 )
		fgSizer1.SetFlexibleDirection( wx.BOTH )
		fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_ALL )

		self.m_staticText1 = wx.StaticText( panel, wx.ID_ANY, u"Base Path", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )

		fgSizer1.Add( self.m_staticText1, 0, wx.ALL, 5 )

		self.basePath = wx.TextCtrl( panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		fgSizer1.Add( self.basePath, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_button_base_path = wx.Button( panel, wx.ID_ANY, u"Browse", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_button_base_path, 0, wx.ALL, 5 )

		self.m_staticText3 = wx.StaticText( panel, wx.ID_ANY, u"Core Output Path", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )

		fgSizer1.Add( self.m_staticText3, 0, wx.ALL, 5 )

		self.corePath = wx.TextCtrl( panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		fgSizer1.Add( self.corePath, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_button3 = wx.Button( panel, wx.ID_ANY, u"Browse", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_button3, 0, wx.ALL, 5 )

		self.m_staticText121 = wx.StaticText( panel, wx.ID_ANY, u"Start Position (big)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText121.Wrap( -1 )

		fgSizer1.Add( self.m_staticText121, 0, wx.ALL, 5 )

		self.m_startPositionBig = wx.TextCtrl( panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_startPositionBig, 0, wx.ALL|wx.EXPAND, 5 )


		fgSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText14 = wx.StaticText( panel, wx.ID_ANY, u"Start Position (small)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText14.Wrap( -1 )

		fgSizer1.Add( self.m_staticText14, 0, wx.ALL, 5 )

		self.m_startPositionSmall = wx.TextCtrl( panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_startPositionSmall, 0,wx.ALL|wx.EXPAND, 5 )


		fgSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText13 = wx.StaticText( panel, wx.ID_ANY, u"Stack Depth", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText13.Wrap( -1 )

		fgSizer1.Add( self.m_staticText13, 0, wx.ALL, 5 )

		self.m_stackDepth = wx.TextCtrl( panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_stackDepth, 0, wx.ALL|wx.EXPAND, 5 )


		fgSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText15 = wx.StaticText( panel, wx.ID_ANY, u"Overlap", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText15.Wrap( -1 )

		fgSizer1.Add( self.m_staticText15, 0, wx.ALL, 5 )

		self.m_overlap = wx.TextCtrl( panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_overlap, 0, wx.ALL|wx.EXPAND, 5 )


		fgSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText11 = wx.StaticText( panel, wx.ID_ANY, u"Refocus Distance", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )

		fgSizer1.Add( self.m_staticText11, 0, wx.ALL, 5 )

		self.m_refocus = wx.TextCtrl( panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_refocus, 0, wx.ALL|wx.EXPAND, 5 )


		fgSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_button7 = wx.Button( panel, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_button7, 0, wx.ALL, 5 )


		panel.SetSizer( fgSizer1 )
		panel.Layout()


		# Connect Events
		self.m_button_base_path.Bind( wx.EVT_BUTTON, lambda event: self.browseForDirectories(event, 'BasePath') )
		self.m_button3.Bind( wx.EVT_BUTTON, lambda event: self.browseForDirectories(event, 'CoreOutputPath') )
		self.m_button7.Bind( wx.EVT_BUTTON,  self.save )
		self.reload()
		
		return panel
	

	def save(self, event=None):
		# self.config.configValues['VignetteMagic'] = str(self.vignetteMagic.GetValue())
		# self.config.configValues['FocusStackLaunchPath'] = self.focusLaunch.GetValue()
		self.config.configValues['StartPositionBig'] = self.m_startPositionBig.GetValue()
		self.config.configValues['StartPositionSmall'] = self.m_startPositionSmall.GetValue()
		self.config.configValues['StackDepth'] = self.m_stackDepth.GetValue()
		self.config.configValues['Overlap'] = self.m_overlap.GetValue()
		self.config.configValues['Refocus'] = self.m_refocus.GetValue()
		self.config.save_config()
	
	def reload(self, event=None):
		
		self.basePath.SetValue(self.config.configValues["BasePath"])
		self.m_startPositionBig.SetValue(self.config.configValues["StartPositionBig"])
		self.m_startPositionSmall.SetValue(self.config.configValues["StartPositionSmall"])
		self.m_stackDepth.SetValue(self.config.configValues["StackDepth"])
		self.m_overlap.SetValue(self.config.configValues["Overlap"])
		self.m_refocus.SetValue(self.config.configValues["Refocus"])


	def browseForFiles( self, event, target):
		dlg = getExistingFiles()
		if dlg.exec_() == QDialog.Accepted:
			self.config.configValues[target] = dlg.selectedFiles()[0]
			self.save();
			self.reload();

	def browseForDirectories(self, event, target):
		dlg = getExistingDirectories()
		dlg.setDirectory(self.config.configValues[target])
		if dlg.exec_() == QDialog.Accepted:
			self.config.configValues[target] = dlg.selectedFiles()[0]
			self.save();
			self.reload();

class getExistingFiles(QFileDialog):
		def __init__(self, *args):
			super(getExistingFiles, self).__init__(*args)
			self.setOption(self.DontUseNativeDialog, True)
			self.setFileMode(self.ExistingFile)
			self.setOption(self.ShowDirsOnly, False)

class getExistingDirectories(QFileDialog):
	def __init__(self, *args):
		super(getExistingDirectories, self).__init__(*args)
		self.setOption(self.DontUseNativeDialog, True)
		self.setFileMode(self.Directory)
		self.setOption(self.ShowDirsOnly, True)
		# self.setDirectory(args[0])
		self.findChildren(QListView)[0].setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.findChildren(QTreeView)[0].setSelectionMode(QAbstractItemView.ExtendedSelection)


class CameraPrefs (wx.StockPreferencesPage):
	def __init__(self, config):
		super().__init__(wx.StockPreferencesPage.Kind_Advanced)
		self.config = config
	
	def CreateWindow(self, parent):
		# THe main container window
		panel = wx.Panel(parent)
		fgSizer2 = wx.FlexGridSizer( 0, 2, 0, 0 )
		fgSizer2.AddGrowableCol( 1 )
		fgSizer2.SetFlexibleDirection( wx.BOTH )
		fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.m_staticText9 = wx.StaticText( panel, wx.ID_ANY, u"Preview ISO", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText9.Wrap( -1 )

		fgSizer2.Add( self.m_staticText9, 0, wx.ALL, 5 )

		self.m_previewISO = wx.TextCtrl( panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.m_previewISO, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText10 = wx.StaticText( panel, wx.ID_ANY, u"Preview Shutter", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText10.Wrap( -1 )

		fgSizer2.Add( self.m_staticText10, 0, wx.ALL, 5 )

		self.m_previewShutter = wx.TextCtrl( panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.m_previewShutter, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText11 = wx.StaticText( panel, wx.ID_ANY, u"Capture ISO", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )

		fgSizer2.Add( self.m_staticText11, 0, wx.ALL, 5 )

		self.m_captureISO = wx.TextCtrl( panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.m_captureISO, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText12 = wx.StaticText( panel, wx.ID_ANY, u"Capture Shutter", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12.Wrap( -1 )

		fgSizer2.Add( self.m_staticText12, 0, wx.ALL, 5 )

		self.m_captureShutter = wx.TextCtrl( panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.m_captureShutter, 0, wx.ALL|wx.EXPAND, 5 )


		self.m_button7 = wx.Button( panel, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.m_button7, 0, wx.ALL, 5 )

		panel.SetSizer( fgSizer2 )
		panel.Layout()

		self.m_button7.Bind( wx.EVT_BUTTON,  self.save )
		self.reload()
		return panel;

	def __del__( self ):
		pass


	def save(self, event=None):
		self.config.configValues['captureISO'] = self.m_captureISO.GetValue()
		self.config.configValues['captureShutter'] = self.m_captureShutter.GetValue()
		self.config.configValues['previewISO'] = self.m_previewISO.GetValue()
		self.config.configValues['previewShutter'] = self.m_previewShutter.GetValue()
		self.config.save_config()
	
	def reload(self, event=None):
		
		self.m_captureISO.SetValue(self.config.configValues["captureISO"])
		self.m_captureShutter.SetValue(self.config.configValues["captureShutter"])
		self.m_previewISO.SetValue(self.config.configValues["previewISO"])
		self.m_previewShutter.SetValue(self.config.configValues["previewShutter"])


