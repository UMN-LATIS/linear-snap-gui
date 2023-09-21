# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-0-g8feb16b)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class MiniMacroFrame
###########################################################################

class MiniMacroFrame ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 1366,710 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		bSizer6 = wx.BoxSizer( wx.HORIZONTAL )


		bSizer6.Add( ( 10, 0), 0, wx.EXPAND, 5 )

		bSizer5 = wx.BoxSizer( wx.VERTICAL )

		bSizer72 = wx.BoxSizer( wx.VERTICAL )


		bSizer72.Add( ( 0, 10), 0, wx.EXPAND, 5 )

		gSizer1 = wx.GridSizer( 3, 3, 0, 0 )


		gSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_button5 = wx.Button( self, wx.ID_ANY, u"Short Rail Back", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.m_button5, 0, wx.ALIGN_CENTER|wx.ALL, 5 )


		gSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_button3 = wx.Button( self, wx.ID_ANY, u"Long Rail Left", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.m_button3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )


		gSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_button4 = wx.Button( self, wx.ID_ANY, u"Long Rail Right", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.m_button4, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, 5 )


		gSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_button2 = wx.Button( self, wx.ID_ANY, u"Short Rail Forward", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.m_button2, 0, wx.ALIGN_CENTER|wx.ALL, 5 )


		gSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer72.Add( gSizer1, 0, wx.EXPAND, 10 )

		bSizer7 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_button18 = wx.Button( self, wx.ID_ANY, u"Home", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer7.Add( self.m_button18, 0, wx.ALL, 5 )

		self.m_button19 = wx.Button( self, wx.ID_ANY, u"Find Focus", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer7.Add( self.m_button19, 0, wx.ALL, 5 )

		self.m_SlowMoves = wx.CheckBox( self, wx.ID_ANY, u"Slow Moves", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer7.Add( self.m_SlowMoves, 0, wx.ALL, 5 )

		self.m_EnableLiveView = wx.CheckBox( self, wx.ID_ANY, u"Live View", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer7.Add( self.m_EnableLiveView, 0, wx.ALL, 5 )


		bSizer72.Add( bSizer7, 0, wx.EXPAND, 5 )


		bSizer72.Add( ( 0, 20), 0, wx.EXPAND, 5 )

		bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"Core Type", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )

		bSizer4.Add( self.m_staticText3, 0, wx.ALL, 5 )

		m_coreTypeChoices = [ u"Tall", u"Short" ]
		self.m_coreType = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_coreTypeChoices, 0 )
		bSizer4.Add( self.m_coreType, 0, wx.ALL, 5 )


		bSizer72.Add( bSizer4, 0, wx.EXPAND, 5 )


		bSizer72.Add( ( 0, 20), 1, wx.EXPAND, 5 )

		bSizer41 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText31 = wx.StaticText( self, wx.ID_ANY, u"Core ID", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText31.Wrap( -1 )

		bSizer41.Add( self.m_staticText31, 0, wx.ALL, 5 )

		self.m_coreId = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		bSizer41.Add( self.m_coreId, 30, wx.EXPAND, 5 )


		bSizer72.Add( bSizer41, 1, wx.EXPAND, 5 )


		bSizer72.Add( ( 0, 20), 0, 0, 5 )


		bSizer5.Add( bSizer72, 1, wx.EXPAND, 5 )


		bSizer5.Add( ( 0, 10), 1, wx.EXPAND, 5 )

		self.coreCompleteText = wx.StaticText( self, wx.ID_ANY, u"Core Complete! 🎉", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.coreCompleteText.Wrap( -1 )

		self.coreCompleteText.SetFont( wx.Font( 30, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
		self.coreCompleteText.Hide()

		bSizer5.Add( self.coreCompleteText, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )

		gSizer2 = wx.GridSizer( 0, 3, 0, 0 )

		self.halt_button = wx.Button( self, wx.ID_ANY, u"Halt", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.halt_button, 0, wx.ALIGN_BOTTOM|wx.ALL, 5 )

		self.preferences = wx.Button( self, wx.ID_ANY, u"Preferences", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.preferences, 0, wx.ALIGN_BOTTOM|wx.ALL, 5 )

		self.start_core = wx.Button( self, wx.ID_ANY, u"Start Core", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer2.Add( self.start_core, 0, wx.ALIGN_BOTTOM|wx.ALIGN_RIGHT|wx.ALL, 5 )


		bSizer5.Add( gSizer2, 1, wx.EXPAND, 5 )


		bSizer5.Add( ( 0, 5), 0, wx.EXPAND, 5 )


		bSizer6.Add( bSizer5, 0, 0, 5 )


		bSizer6.Add( ( 20, 0), 0, wx.EXPAND, 5 )

		bSizer61 = wx.BoxSizer( wx.VERTICAL )

		self.m_LiveView = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), wx.TAB_TRAVERSAL )
		self.m_LiveView.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_APPWORKSPACE ) )
		self.m_LiveView.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_APPWORKSPACE ) )
		self.m_LiveView.SetMinSize( wx.Size( 320,240 ) )

		bSizer61.Add( self.m_LiveView, 1, wx.ALL|wx.EXPAND, 5 )

		bSizer71 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"Focus Value:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )

		bSizer71.Add( self.m_staticText2, 0, wx.ALL, 5 )

		self.m_Focus = wx.StaticText( self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_Focus.Wrap( -1 )

		bSizer71.Add( self.m_Focus, 0, wx.ALL, 5 )


		bSizer71.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText4 = wx.StaticText( self, wx.ID_ANY, u"Short Rail:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )

		bSizer71.Add( self.m_staticText4, 0, wx.ALL, 5 )

		self.m_ShortRail = wx.StaticText( self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_ShortRail.Wrap( -1 )

		bSizer71.Add( self.m_ShortRail, 0, wx.ALL, 5 )


		bSizer71.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText7 = wx.StaticText( self, wx.ID_ANY, u"Long Rail:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )

		bSizer71.Add( self.m_staticText7, 0, wx.ALL, 5 )

		self.m_LongRail = wx.StaticText( self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_LongRail.Wrap( -1 )

		bSizer71.Add( self.m_LongRail, 0, wx.ALL, 5 )


		bSizer71.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText9 = wx.StaticText( self, wx.ID_ANY, u"Photos", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText9.Wrap( -1 )

		bSizer71.Add( self.m_staticText9, 0, wx.ALL, 5 )

		self.m_PhotoCount = wx.StaticText( self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_PhotoCount.Wrap( -1 )

		bSizer71.Add( self.m_PhotoCount, 0, wx.ALL, 5 )


		bSizer71.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText11 = wx.StaticText( self, wx.ID_ANY, u"Positions", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )

		bSizer71.Add( self.m_staticText11, 0, wx.ALL, 5 )

		self.m_PositionCount = wx.StaticText( self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_PositionCount.Wrap( -1 )

		bSizer71.Add( self.m_PositionCount, 0, wx.ALL, 5 )


		bSizer61.Add( bSizer71, 0, wx.EXPAND, 5 )


		bSizer6.Add( bSizer61, 1, wx.EXPAND, 5 )


		self.SetSizer( bSizer6 )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.m_coreType.SetSelection( int(self.config.configValues['CoreType'] ))

		self.m_button5.Bind( wx.EVT_LEFT_DOWN, self.moveShortBack )
		self.m_button5.Bind( wx.EVT_LEFT_UP, self.stopShort )
		self.m_button3.Bind( wx.EVT_LEFT_DOWN, self.moveLongLeft )
		self.m_button3.Bind( wx.EVT_LEFT_UP, self.stopLong )
		self.m_button4.Bind( wx.EVT_LEFT_DOWN, self.moveLongRight )
		self.m_button4.Bind( wx.EVT_LEFT_UP, self.stopLong )
		self.m_button2.Bind( wx.EVT_LEFT_DOWN, self.moveShortForward )
		self.m_button2.Bind( wx.EVT_LEFT_UP, self.stopShort )
		self.m_button18.Bind( wx.EVT_LEFT_UP, self.goHome )
		self.m_button19.Bind( wx.EVT_LEFT_UP, self.findFocus )
		self.halt_button.Bind( wx.EVT_LEFT_UP, self.stopAll )
		self.preferences.Bind( wx.EVT_BUTTON, self.openPrefs )
		self.start_core.Bind( wx.EVT_LEFT_UP, self.imageCore )
		
		self.m_coreType.Bind( wx.EVT_CHOICE, self.changeCoreType )



	def __del__( self ):
		pass

	def changeCoreType( self, event ):
		event.Skip()


	def onExitButton(self, event):
		event.Skip()

	# Virtual event handlers, override them in your derived class
	def OnPaint(self, event):
		event.Skip()

	def NextFrame(self, event):
		event.Skip()

	def moveShortBack( self, event ):
		event.Skip()

	def stopShort( self, event ):
		event.Skip()

	def moveLongLeft( self, event ):
		event.Skip()

	def stopLong( self, event ):
		event.Skip()

	def moveLongRight( self, event ):
		event.Skip()


	def moveShortForward( self, event ):
		event.Skip()


	def goHome( self, event ):
		event.Skip()

	def findFocus( self, event ):
		event.Skip()

	def stopAll( self, event ):
		event.Skip()

	def imageCore( self, event ):
		event.Skip()

	def liveView( self, event ):
		event.Skip()

	def openPrefs( self, event ):
		event.Skip()
