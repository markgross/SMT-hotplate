#!/usr/bin/env python

import wx

import thread
import  wx.lib.newevent

import matplotlib
#matplotlib.interactive( True )
matplotlib.use( 'WXAgg' )

import serial
import time

(UpdateTempEvent, EVT_UPDATE_VALUES) = wx.lib.newevent.NewEvent()

temps = [20.0]
times = [0.0]
target = [20.0]

class pid_hotplate:

    def __init__(self,dev = '/dev/ttyACM0'):
        self.serial = serial.Serial(dev, baudrate=115200, writeTimeout=10)
        self.serial.open()

    def write(self, data):
        self.serial.write(data)

    def read_temp(self):
        self.write(' ')
        result = self.serial.readline().strip()
        return result



hotplate = pid_hotplate()

class MyDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_1 = wx.StaticText(self, -1, _("PID_P :"), style=wx.ALIGN_RIGHT)
        self.PidPCtrl = wx.SpinCtrl(self, -1, "0", min=-100, max=100)
        self.label_2 = wx.StaticText(self, -1, _("PID_I :"), style=wx.ALIGN_RIGHT)
        self.PidICtrl = wx.SpinCtrl(self, -1, "0", min=-100, max=100)
        self.label_3 = wx.StaticText(self, -1, _("PID_D :"), style=wx.ALIGN_RIGHT)
        self.PidDCtrl = wx.SpinCtrl(self, -1, "0", min=-100, max=100)
        self.label_4 = wx.StaticText(self, -1, _("Target Temp :"), style=wx.ALIGN_RIGHT)
        self.TargTempCtrl = wx.SpinCtrl(self, -1, "0", min=-100, max=100)
        self.ApplySettings = wx.Button(self, -1, _("Ok"))
        self.Cancel = wx.Button(self, -1, _("Cancel"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnOk, self.ApplySettings)
        self.Bind(wx.EVT_BUTTON, self.OnCancle, self.Cancel)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyDialog.__set_properties
        self.SetTitle(_("dialog_1"))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyDialog.__do_layout
        grid_sizer_1 = wx.FlexGridSizer(4, 2, 0, 0)
        grid_sizer_1.Add(self.label_1, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0)
        grid_sizer_1.Add(self.PidPCtrl, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(self.label_2, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0)
        grid_sizer_1.Add(self.PidICtrl, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(self.label_3, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0)
        grid_sizer_1.Add(self.PidDCtrl, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(self.label_4, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0)
        grid_sizer_1.Add(self.TargTempCtrl, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(self.ApplySettings, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(self.Cancel, 0, wx.EXPAND, 0)
        self.SetSizer(grid_sizer_1)
        grid_sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

 
    def OnOk(self, event): # wxGlade: MyDialog.<event_handler>
        print "Event handler `OnOk' not implemented!"
        newP = self.PidPCtrl.get_value()
        newI = self.PidPCtrl.get_value()
        newD = self.PidPCtrl.get_value()
        newTarg = self.PidPCtrl.get_value()

        event.Skip()

    def OnCancle(self, event): # wxGlade: MyDialog.<event_handler>
        print "Event handler `OnCancle' not implemented!"
        event.Skip()

# end of class MyDialog



class PlotPanel (wx.Panel):
    """The PlotPanel has a Figure and a Canvas. OnSize events simply set a 
    flag, and the actual resizing of the figure is triggered by an Idle event."""
    def __init__( self, parent, **kwargs ):
        from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
        from matplotlib.figure import Figure

        # initialize Panel
        if 'id' not in kwargs.keys():
            kwargs['id'] = wx.ID_ANY
        if 'style' not in kwargs.keys():
            kwargs['style'] = wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Panel.__init__( self, parent, **kwargs )

        # initialize matplotlib stuff
        self.figure = Figure()
        self.canvas = FigureCanvasWxAgg( self, -1, self.figure )

        self._SetSize()
        self.draw()
        self._resizeflag = False

        self.Bind(wx.EVT_IDLE, self._onIdle)
        self.Bind(wx.EVT_SIZE, self._onSize)

    def _onSize( self, event ):
        self._resizeflag = True

    def _onIdle( self, evt ):
        if self._resizeflag:
            self._resizeflag = False
            self._SetSize()

    def _SetSize( self ):
        pixels = tuple( self.parent.GetClientSize() )
        self.SetSize( pixels )
        self.canvas.SetSize( pixels )
        self.figure.set_size_inches( float( pixels[0] )/self.figure.get_dpi(),
                                     float( pixels[1] )/self.figure.get_dpi() )

    def draw(self): pass # abstract, to be overridden by child classes


class TempeturePlotPanel (PlotPanel):
    """Plots several lines in distinct colors."""
    def __init__( self, parent, **kwargs ):
        self.parent = parent

        # initiate plotter
        PlotPanel.__init__( self, parent, **kwargs )

    def draw( self ):
        global temps
        global times
        global target
        """Draw data."""

        # Get the minimum and maximum temperatures these are
        # used for annotations and scaling the plot of data
        min_t = min(temps + target)
        max_t = max(temps + target)
        if not hasattr(self, 'subplot'):
            self.figure.clear( )
            self.figure.suptitle("Live Temperature")
            self.subplot = self.figure.add_subplot( 111 )
            self.subplot.grid(True)
            self.temp, = self.subplot.plot(times, temps)
            self.targ, = self.subplot.plot(times, target)
            self.subplot.set_xlabel("Time (Seconds)")
            self.subplot.set_ylabel(r'Temperature $^{\circ}$C')
            self.subplot.axis([times[0],1, min_t ,max_t])
            self.figure.canvas.draw()

        self.figure.clear( )
        self.figure.suptitle("Live Temperature")
        self.subplot = self.figure.add_subplot( 111 )
        self.subplot.grid(True)
        self.temp, = self.subplot.plot(times, temps)
        self.targ, = self.subplot.plot(times, target)
        self.subplot.set_xlabel("Time (Seconds)")
        self.subplot.set_ylabel(r'Temperature $^{\circ}$C')
        #self.targ.set_xdata(times)
        #self.targ.set_xdata(times)
        #self.targ.set_ydata(target)
        #self.temp.set_ydata(temps)
        self.subplot.axis([times[0],times[len(times)-1] + 1, min_t -1 ,max_t +1])
        #self.subplot.draw_artist(self.temp)
        #self.subplot.draw_artist(self.targ)
        self.figure.canvas.draw()
        #self.figure.canvas.blit(self.subplot.bbox)
            
        # Set the axis limits to make the data more readable
        #elf.targ.set_xdata(times)
        #elf.targ.set_xdata(times)
        #elf.targ.set_ydata(target)
        #elf.temp.set_ydata(temps)
        #self.temp.remove()
        #self.targ.remove()
        #self.temp, = self.subplot.plot(times, temps)
        #self.targ, = self.subplot.plot(times, target)
        #self.subplot.draw_artist(self.temp)
        #self.subplot.draw_artist(self.targ)
        #self.subplot.set_xlim([times[0],times[len(times)-1] + 1])
        #self.subplot.set_ylim([min_t -1 ,max_t + 1])
        #self.figure.canvas.draw()
        #self.figure.canvas.blit(self.subplot.bbox)




class SMT_Reflow(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: SMT_Reflow.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        #kwds["style"] = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.SYSTEM_MENU|wx.SIMPLE_BORDER|wx.RESIZE_BORDER|wx.FRAME_TOOL_WINDOW|wx.CLIP_CHILDREN
        wx.Frame.__init__(self, *args, **kwds)
       
        self.on = False
        self.boil = 101
        self.flux = 200
        self.hg = 220
        self.no_hg = 240
        self.target_temp = 15

        self.graph = TempeturePlotPanel(self )
        # Menu Bar
        self.frame_1_menubar = wx.MenuBar()
        self.smt_control = wx.Menu()
        self.frame_1_menubar.Append(self.smt_control, _("SMT control"))
        self.SetMenuBar(self.frame_1_menubar)
        # Menu Bar end
        self.frame_1_statusbar = self.CreateStatusBar(6, wx.ST_SIZEGRIP)
        
        # Tool Bar
        self.frame_1_toolbar = wx.ToolBar(self, -1, style=wx.TB_HORIZONTAL|wx.TB_FLAT|wx.TB_3DBUTTONS|wx.TB_TEXT|wx.TB_NOICONS|wx.TB_HORZ_LAYOUT|wx.TB_HORZ_TEXT)
        self.SetToolBar(self.frame_1_toolbar)
        self.frame_1_toolbar.AddLabelTool(1, _("off"), wx.NullBitmap, wx.NullBitmap, wx.ITEM_RADIO, "", "")
        self.frame_1_toolbar.AddLabelTool(2, _("boil"), wx.NullBitmap, wx.NullBitmap, wx.ITEM_RADIO, "", "")
        self.frame_1_toolbar.AddLabelTool(3, _("flux"), wx.NullBitmap, wx.NullBitmap, wx.ITEM_RADIO, "", "")
        self.frame_1_toolbar.AddLabelTool(4, _("reflo-hg"), wx.NullBitmap, wx.NullBitmap, wx.ITEM_RADIO, "", "")
        self.frame_1_toolbar.AddLabelTool(5, _("reflo-hg-free"), wx.NullBitmap, wx.NullBitmap, wx.ITEM_RADIO, "", "")
        # Tool Bar end
    
        self.data = hotplate.read_temp().split(' ')

        self.Bind(EVT_UPDATE_VALUES, self.OnUpdate)
        self.__set_properties()
        self.__do_layout()
        self.Bind(wx.EVT_TOOL, self.OnOn, id=1)
        self.Bind(wx.EVT_TOOL, self.OnBoil, id=2)
        self.Bind(wx.EVT_TOOL, self.OnFlux, id=3)
        self.Bind(wx.EVT_TOOL, self.OnHg, id=4)
        self.Bind(wx.EVT_TOOL, self.OnHgFree, id=5)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: SMT_Reflow.__set_properties
        self.SetTitle(_("SMT tempature control and tracking"))
        self.frame_1_statusbar.SetStatusWidths([80, 80, 80, 80, 80, 80])
        # statusbar fields
        frame_1_statusbar_fields = [_("pid_P"), _("pid_I"), _("pid_D"), _("target"), _("temp"), _("power")]
        for i in range(len(frame_1_statusbar_fields)):
            self.frame_1_statusbar.SetStatusText(frame_1_statusbar_fields[i], i)
        self.frame_1_toolbar.SetToolBitmapSize((16, 15))
        self.frame_1_toolbar.SetMargins((0, 0))
        self.frame_1_toolbar.SetToolPacking(6)
        self.frame_1_toolbar.SetToolSeparation(5)
        self.frame_1_toolbar.Realize()

        self.graph.SetMinSize((500,200))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: SMT_Reflow.__do_layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.graph, 1, wx.EXPAND, 1)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        # end wxGlade

    def Set_target(self, t):
        count = int(target[len(target) - 1] - t)
        if 0 < count:
            hotplate.write(count*'t')

        if 0 > count:
                hotplate.write((-count)*'T')
    
    def update_thread(self):
        global temps
        global times
        global target
        start_time = time.time()
        while True:
            self.Set_target(self.target_temp)
            current_pos = time.time() - start_time
            self.data = hotplate.read_temp().split(' ')
            # If we got new data then append it to the list of
            # temperatures and trim to 240 points
            temps.append(float(self.data[1]))
            target.append(float(self.data[0]))
            times.append(current_pos)
            if len(temps) > 240:
                temps = temps[-240:]
                times = times[-240:]
                target = target[-240:]

            time.sleep(0.5)
            evt = UpdateTempEvent(
                    target = self.data[0],
                    temp = self.data[1],
                    P = self.data[2],
                    I = self.data[3],
                    D = self.data[4],
                    power = self.data[5])
            wx.PostEvent(self, evt)

    def OnUpdate(self, evt):
        for i in range(6):
            self.frame_1_statusbar.SetStatusText(self.data[i], i)
        self.Refresh(False)
        #if self.on:
        self.graph.draw()

    def OnOn(self, e):
        self.target_temp = 15

    def OnBoil(self, e):
        self.target_temp = self.boil 

    def OnFlux(self, e):
        self.target_temp = self.flux

    def OnHg(self, e):
        self.target_temp = self.hg

    def OnHgFree(self, e):
        self.target_temp = self.no_hg


# end of class SMT_Reflow


if __name__ == "__main__":
    import gettext
    gettext.install("app") # replace with the appropriate catalog name

    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = SMT_Reflow(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    listen = thread.start_new_thread(frame_1.update_thread, ())
    app.MainLoop()