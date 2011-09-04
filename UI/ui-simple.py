#!/usr/bin/env python

import cProfile
import pstats

import wx

import thread
import  wx.lib.newevent

import matplotlib
#matplotlib.interactive( True )
matplotlib.use( 'WXAgg' )

import serial
import struct
import time

(UpdateTempEvent, EVT_UPDATE_VALUES) = wx.lib.newevent.NewEvent()

lock = thread.allocate_lock()

temps = [1.0]
times = [0.0]
target = [1.0]
p_val = [1.0]
i_val = [1.0]
d_val = [1.0]

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

    def setP(self, p):
        Pstr = 'P' + struct.pack('f', p)
        self.write(Pstr)

    def setI(self, i):
        Istr = 'I' + struct.pack('f', i)
        self.write(Istr)

    def setD(self, d):
        Dstr = 'D' + struct.pack('f', d)
        self.write(Dstr)

    def setTarget(self, temp):
        Tstr = 'T' + struct.pack('f', temp)
        self.write(Tstr)


hotplate = pid_hotplate()


class MyDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_1 = wx.StaticText(self, -1, _("PID_P :"), style=wx.ALIGN_RIGHT)
        self.text_ctrl_P = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)
        self.label_2 = wx.StaticText(self, -1, _("PID_I :"), style=wx.ALIGN_RIGHT)
        self.text_ctrl_I = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)
        self.label_3 = wx.StaticText(self, -1, _("PID_D :"), style=wx.ALIGN_RIGHT)
        self.text_ctrl_D = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)
        self.label_4 = wx.StaticText(self, -1, _("Target Temp :"), style=wx.ALIGN_RIGHT)
        self.text_ctrl_T = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)
        self.ApplySettings = wx.Button(self, -1, _("Ok"))
        self.Cancel = wx.Button(self, -1, _("Cancel"))

        self.__set_properties()
        self.__do_layout()

        #self.Bind(wx.EVT_TEXT_ENTER, self.updateData, self.text_ctrl_P)
        #self.Bind(wx.EVT_TEXT_ENTER, self.updateData, self.text_ctrl_I)
        #self.Bind(wx.EVT_TEXT_ENTER, self.updateData, self.text_ctrl_D)
        #self.Bind(wx.EVT_TEXT_ENTER, self.updateData, self.text_ctrl_T)
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
        grid_sizer_1.Add(self.text_ctrl_P, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(self.label_2, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0)
        grid_sizer_1.Add(self.text_ctrl_I, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(self.label_3, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0)
        grid_sizer_1.Add(self.text_ctrl_D, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(self.label_4, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0)
        grid_sizer_1.Add(self.text_ctrl_T, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(self.ApplySettings, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(self.Cancel, 0, wx.EXPAND, 0)
        self.SetSizer(grid_sizer_1)
        grid_sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def updateData(self, event): # wxGlade: MyDialog.<event_handler>
        value = self.text_ctrl_P.GetValue()
        try:
            P = float(value)
            hotplate.setP(P)
        except ValueError:
            self.text_ctrl_P.SetValue("")

        value = self.text_ctrl_I.GetValue()
        try:
            I = float(value)
            hotplate.setI(I)
        except ValueError:
            self.text_ctrl_I.SetValue("")

        value = self.text_ctrl_D.GetValue()
        try:
            D = float(value)
            hotplate.setD(D)
        except ValueError:
            self.text_ctrl_D.SetValue("")

        value = self.text_ctrl_T.GetValue()
        try:
            T = float(value)
            hotplate.setTarget(T)
        except ValueError:
            self.text_ctrl_T.SetValue("")


    def OnOk(self, event): # wxGlade: MyDialog.<event_handler>
        self.updateData(event)
        self.Close(True)
        event.Skip()

    def OnCancle(self, event): # wxGlade: MyDialog.<event_handler>
        self.Close(True)

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

        #self.Bind(wx.EVT_IDLE, self._onIdle)
        self.Bind(wx.EVT_SIZE, self._onSize)

    def _onSize( self, event ):
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
        global lock
        global p_val
        global i_val
        global d_val
        """Draw data."""

        lock.acquire()
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

            #self.subplot = self.figure.add_subplot( 212 )
            #self.p_val, = self.subplot.plot(times, p_val)
            #self.i_val, = self.subplot.plot(times, i_val)
            #self.d_val, = self.subplot.plot(times, d_val)
            #self.subplot.set_xlabel("Time (Seconds)")
            #self.subplot.set_ylabel('P, I, D')
            #self.figure.canvas.draw()

        self.figure.clear( )
        self.figure.suptitle("Live Temperature")
        self.subplot = self.figure.add_subplot( 111 )
        self.subplot.grid(True)
        self.temp, = self.subplot.plot(times, temps)
        self.targ, = self.subplot.plot(times, target)
        self.subplot.set_xlabel("Time (Seconds)")
        self.subplot.set_ylabel(r'Temperature $^{\circ}$C')
        self.subplot.axis([times[0],times[len(times)-1] + 1, min_t -1 ,max_t +1])

        #self.subplot = self.figure.add_subplot( 212 )
        #self.p_val, = self.subplot.plot(times, p_val)
        #self.i_val, = self.subplot.plot(times, i_val)
        #self.d_val, = self.subplot.plot(times, d_val)
        #self.subplot.set_xlabel("Time (Seconds)")
        #self.subplot.set_ylabel('P, I, D')
        self.figure.canvas.draw()

        self.figure.canvas.draw()
        lock.release()
            


class SMT_Reflow(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: SMT_Reflow.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        #kwds["style"] = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.SYSTEM_MENU|wx.SIMPLE_BORDER|wx.RESIZE_BORDER|wx.FRAME_TOOL_WINDOW|wx.CLIP_CHILDREN
        wx.Frame.__init__(self, *args, **kwds)
       
        self.on = False
        self.boil = 101
        self.flux = 200
        self.pb = 220
        self.no_pb = 240
        self.running = True

        self.graph = TempeturePlotPanel(self )
        # Menu Bar
        self.frame_1_menubar = wx.MenuBar()
        self.smt_control = wx.Menu()
        settings = self.smt_control.Append(11, "change Settings", "change Settings")

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
        self.frame_1_toolbar.AddLabelTool(4, _("reflo-pb"), wx.NullBitmap, wx.NullBitmap, wx.ITEM_RADIO, "", "")
        self.frame_1_toolbar.AddLabelTool(5, _("reflo-pb-free"), wx.NullBitmap, wx.NullBitmap, wx.ITEM_RADIO, "", "")
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
        self.Bind(wx.EVT_MENU, self.SettingsDlg, id=11)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        #self.Bind(wx.EVT_MENU, self.SettingsDlg, settings)
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

        self.graph.SetMinSize((800,500))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: SMT_Reflow.__do_layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.graph, 1, wx.EXPAND, 1)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        # end wxGlade

   
    def SettingsDlg(self, e):
        dlg = MyDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def update_thread(self):
        global temps
        global times
        global target
        global p_val
        global i_val
        global d_val
        global lock

        outfile = open("logfile.txt", "w")

        hotplate.setTarget(1.0)
        start_time = time.time()
        while self.running:
            current_pos = time.time() - start_time
            self.data = hotplate.read_temp().split(' ')
            print >>outfile, self.data[0], self.data[1], self.data[2], self.data[3], self.data[4], self.data[5], self.data[6], self.data[7], self.data[8] 
            # If we got new data then append it to the list of
            # temperatures and trim to 240 points
            lock.acquire()
            target.append(float(self.data[0]))
            temps.append(float(self.data[1]))
            p_val.append(float(self.data[5]))
            i_val.append(float(self.data[6]))
            d_val.append(float(self.data[7]))
            times.append(current_pos)
            lock.release()
            if len(temps) > 120:
                temps = temps[-120:]
                times = times[-120:]
                target = target[-120:]
                p_val = target[-120:]
                i_val = target[-120:]
                d_val = target[-120:]

            evt = UpdateTempEvent(
                    target = self.data[0],
                    temp = self.data[1],
                    P = self.data[2],
                    I = self.data[3],
                    D = self.data[4],
                    power = self.data[8])
            wx.PostEvent(self, evt)
            time.sleep(0.50)
        outfile.close()

    def OnUpdate(self, evt):
        for i in range(5):
            self.frame_1_statusbar.SetStatusText(self.data[i], i)
        self.frame_1_statusbar.SetStatusText(self.data[8], 5)
        self.Refresh(True)
        #if self.on:
        self.graph.draw()

    def OnOn(self, e):
        hotplate.setTarget(1.0)

    def OnBoil(self, e):
        hotplate.setTarget(self.boil) 

    def OnFlux(self, e):
        hotplate.setTarget(self.flux) 

    def OnHg(self, e):
        hotplate.setTarget(self.pb) 

    def OnHgFree(self, e):
        hotplate.setTarget(self.no_pb) 

    def OnClose(self, e):
        hotplate.setTarget(0.0)
        self.running = False
        time.sleep(0.6)
        self.Destroy()
        


# end of class SMT_Reflow
def main():
    import gettext
    gettext.install("app") # replace with the appropriate catalog name

    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = SMT_Reflow(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    listen = thread.start_new_thread(frame_1.update_thread, ())
    app.MainLoop()

if __name__ == "__main__":
    main()
    #cProfile.run("main()", "prof.txt")
    #stats = pstats.Stats("prof.txt")
    #stats.print_stats()

