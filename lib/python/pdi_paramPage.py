#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
GUIアプリケーション機能
パラメータページクラス実装
"""

import sys, os

try:
    import pdi_log
    log = pdi_log._log
    from pdi_desc import *
except Exception, e:
    sys.exit(str(e))

try:
    import wx
except Exception, e:
    sys.exit(str(e))


class ParamPage(wx.ScrolledWindow):
    """
    HPC/PF PDIサブシステムのパラメータ設定パネルのクラスです。
    wxPythonのScrolledWindowクラスの派生クラスです。
    """

    def __init__(self, parent, title='_All_', bw=3, core=None):
        """
        初期化

        [in] parent  親ウインドウ
        [in] title  ウインドウタイトル
        [in] bw  ボーダー幅
        [in] core  PDIコアデータ
        """
        wx.ScrolledWindow.__init__(self, parent, wx.ID_ANY, name=title)
        self.SetScrollbars(20, 20, 1, 1)
        self.core = core
        self.bw = bw

        layout = wx.GridBagSizer()

        layout.Add(wx.StaticText(self, wx.ID_ANY, 'name'),
                   pos=(0,0), flag=wx.GROW|wx.ALL|wx.ALIGN_CENTER,
                   border=self.bw)
        layout.Add(wx.StaticText(self, wx.ID_ANY, 'type'),
                   pos=(0,1), flag=wx.GROW|wx.ALL|wx.ALIGN_CENTER,
                   border=self.bw)
        layout.Add(wx.StaticText(self, wx.ID_ANY, 'limitation [min/max]'),
                   pos=(0,2), flag=wx.GROW|wx.ALL, border=self.bw)
        layout.Add(wx.StaticText(self, wx.ID_ANY, 'value(s)'),
                   pos=(0,3), flag=wx.GROW|wx.ALL, border=self.bw)
        layout.Add(wx.StaticText(self, wx.ID_ANY,
                                 'sweep range [start/end/delta]',
                                 name='sweep_range_text'),
                   pos=(0,4), flag=wx.GROW|wx.ALL, border=self.bw)
        layout.Add(wx.StaticText(self, wx.ID_ANY, 'exceptional value(s)'),
                   pos=(0,5), flag=wx.GROW|wx.ALL, border=self.bw)

        line = wx.StaticLine(self)
        layout.Add(line, pos=(1, 0), span=(1, 6),
                   flag=wx.EXPAND|wx.BOTTOM, border=self.bw)

        layout.AddGrowableCol(2)
        layout.AddGrowableCol(3)
        layout.AddGrowableCol(4)
        layout.AddGrowableCol(5)
        self.SetSizer(layout)
        layout.Layout()

        return

    def AddParam(self, param):
        """
        パラメータ項目追加

        [in] param  追加するパラメータ
        戻り値 -> 真偽値
        """
        layout = self.GetSizer()
        if not layout: return False
        row = layout.GetRows()
        # col0 name
        nameTxt = wx.StaticText(self, wx.ID_ANY, param.name,
                                name=param.name +':name')
        nameTxt.Bind(wx.EVT_LEFT_DCLICK, self.OnName)
        if param.desc != '':
            nameTxt.SetToolTip(wx.ToolTip(param.desc))
        else:
            nameTxt.SetToolTip(wx.ToolTip('... no description'))
        layout.Add(nameTxt, pos=(row, 0), flag=wx.GROW|wx.ALL|wx.ALIGN_CENTER,
                   border=self.bw)
        # col1 type
        if param.type == Param.Type_INT:
            typeTxt = wx.StaticText(self, wx.ID_ANY, '[int]')
        elif param.type == Param.Type_REAL:
            typeTxt = wx.StaticText(self, wx.ID_ANY, '[real]')
        elif param.type == Param.Type_BOOL:
            typeTxt = wx.StaticText(self, wx.ID_ANY, '[bool]')
        elif param.type == Param.Type_STRING:
            typeTxt = wx.StaticText(self, wx.ID_ANY, '[string]')
        elif param.type == Param.Type_CHOICE:
            typeTxt = wx.StaticText(self, wx.ID_ANY, '[choice]')
        else:
            typeTxt = wx.StaticText(self, wx.ID_ANY, 'UnKnown')
        layout.Add(typeTxt, pos=(row, 1), flag=wx.GROW|wx.ALL|wx.ALIGN_CENTER,
                   border=self.bw)
        # col2 minmax
        hsizer = wx.BoxSizer()
        if param.type == Param.Type_INT or param.type == Param.Type_REAL:
            xTxt = wx.TextCtrl(self, wx.ID_ANY, name=param.name +':min',
                               style=wx.TE_PROCESS_ENTER)
            hsizer.Add(xTxt, flag=wx.GROW)
            xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnMinMax)
            xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnMinMax)
            hsizer.Add(wx.StaticText(self, wx.ID_ANY, '/'))
            xTxt = wx.TextCtrl(self, wx.ID_ANY, name=param.name +':max',
                               style=wx.TE_PROCESS_ENTER)
            hsizer.Add(xTxt, flag=wx.GROW)
            xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnMinMax)
            xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnMinMax)
        layout.Add(hsizer, pos=(row, 2), flag=wx.GROW|wx.ALL, border=self.bw)
        # col3 valList
        hsizer = wx.BoxSizer()
        xRadio = wx.RadioButton(self, wx.ID_ANY, name=param.name +':useValue',
                                label=' ', style=wx.RB_GROUP)
        xRadio.SetToolTip(wx.ToolTip('use value(s)'))
        hsizer.Add(xRadio)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnUseValueRange, xRadio)
        if param.type == Param.Type_INT or param.type == Param.Type_REAL or \
           param.type == Param.Type_STRING:
            xTxt = wx.TextCtrl(self, wx.ID_ANY, name=param.name +':value',
                               style=wx.TE_PROCESS_ENTER)
            hsizer.Add(xTxt, 1, flag=wx.GROW)
            xTxt.SetToolTip(wx.ToolTip('values separated by space'))
            xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnValueTxt)
            xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnValueTxt)
        elif param.type == Param.Type_CHOICE:
            xChoice = wx.Choice(self, wx.ID_ANY, name=param.name +':value',
                                choices=param.citems)
            hsizer.Add(xChoice, 1, flag=wx.GROW)
            self.Bind(wx.EVT_CHOICE, self.OnValueChoice, xChoice)
        elif param.type == Param.Type_BOOL:
            xChk = wx.CheckBox(self, wx.ID_ANY, name=param.name +':value',
                               label='False', size=wx.Size(70,-1))
            hsizer.Add(xChk, 1, flag=wx.GROW)
            self.Bind(wx.EVT_CHECKBOX, self.OnValueChk, xChk)
        layout.Add(hsizer, pos=(row, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        # col4 range
        hsizer = wx.BoxSizer()
        if param.type != Param.Type_STRING:
            xRadio = wx.RadioButton(self, wx.ID_ANY,
                                    name=param.name +':useRange', label=' ')
            if param.type == Param.Type_BOOL:
                xRadio.SetLabel('  True / False')
            xRadio.SetToolTip(wx.ToolTip('use sweep/search range'))
            hsizer.Add(xRadio)
            self.Bind(wx.EVT_RADIOBUTTON, self.OnUseValueRange, xRadio)
        if param.type == Param.Type_INT or param.type == Param.Type_REAL or \
           param.type == Param.Type_CHOICE:
            xTxt = wx.TextCtrl(self, wx.ID_ANY, name=param.name +':rangeStart',
                               style=wx.TE_PROCESS_ENTER)
            hsizer.Add(xTxt, flag=wx.GROW)
            xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnSweepRange)
            xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnSweepRange)
            hsizer.Add(wx.StaticText(self, wx.ID_ANY, '/'))
            xTxt = wx.TextCtrl(self, wx.ID_ANY, name=param.name +':rangeEnd',
                               style=wx.TE_PROCESS_ENTER)
            hsizer.Add(xTxt, flag=wx.GROW)
            xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnSweepRange)
            xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnSweepRange)
            hsizer.Add(wx.StaticText(self, wx.ID_ANY, '/'))
            xTxt = wx.TextCtrl(self, wx.ID_ANY, name=param.name +':rangeDelta',
                               style=wx.TE_PROCESS_ENTER)
            hsizer.Add(xTxt, flag=wx.GROW)
            xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnSweepRange)
            xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnSweepRange)
        layout.Add(hsizer, pos=(row, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        # col5 except
        hsizer = wx.BoxSizer()
        if param.type == Param.Type_INT or param.type == Param.Type_REAL or \
           param.type == Param.Type_CHOICE:
            xChk = wx.CheckBox(self, wx.ID_ANY, name=param.name + ':useExcept',
                               label=' ')
            xChk.SetToolTip(wx.ToolTip('enable exceptional'))
            hsizer.Add(xChk)
            self.Bind(wx.EVT_CHECKBOX, self.OnUseExcept, xChk)
            xRadio = wx.RadioButton(self, wx.ID_ANY,
                                    name=param.name +':exceptAsRange',
                                    label='range', style=wx.RB_GROUP)
            hsizer.Add(xRadio)
            xRadio.SetToolTip(wx.ToolTip('min / max'))
            self.Bind(wx.EVT_RADIOBUTTON, self.OnUseExceptsRange, xRadio)
            xRadio = wx.RadioButton(self, wx.ID_ANY,
                                    name=param.name +':exceptAsValues',
                                    label='values')
            hsizer.Add(xRadio)
            xRadio.SetToolTip(wx.ToolTip('values separated by space'))
            self.Bind(wx.EVT_RADIOBUTTON, self.OnUseExceptsRange, xRadio)
            xTxt = wx.TextCtrl(self, wx.ID_ANY, name=param.name +':excepts',
                               style=wx.TE_PROCESS_ENTER)
            hsizer.Add(xTxt, flag=wx.GROW)
            xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnExcept)
            xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnExcept)
        layout.Add(hsizer, pos=(row,5), flag=wx.GROW|wx.ALL, border=self.bw)

        line = wx.StaticLine(self)
        layout.Add(line, pos=(row+1, 0), span=(1, 6),
                   flag=wx.EXPAND|wx.BOTTOM, border=self.bw)
        layout.Layout()

        return True

    def Update(self):
        """
        表示アップデート

        戻り値 -> 真偽値
        """
        core = self.core
        if not core or not core.pd or not core.pd.plist:
            return False
        for p in core.pd.plist:
            ctl = self.FindWindowByName(p.name +':name')
            if not ctl: continue
            if p.disable:
                ctl.SetForegroundColour('GRAY')
            elif p.calcCaseNum() < 1:
                if core.moeaMode and p.useRange and \
                        p.sweepRange[0] != None and p.sweepRange[1] != None \
                        and p.sweepRange[0] < p.sweepRange[1]:
                    ctl.SetForegroundColour('BLACK')
                else:
                    ctl.SetForegroundColour('RED')
            else:
                ctl.SetForegroundColour('BLACK')
            ctl0 = self.FindWindowByName(p.name +':useValue')
            if not p.type == Param.Type_STRING:
                ctl = self.FindWindowByName(p.name +':useRange')
                if not ctl0 or not ctl: continue
                ctl.SetValue(p.useRange)
                ctl0.SetValue(not p.useRange)
                ctl0.Enable(not p.disable)
                ctl.Enable(not p.disable)
            else:
                ctl0.SetValue(True)
                ctl0.Enable(not p.disable)

            ctl = self.FindWindowByName(p.name +':value')
            if not ctl: continue
            ctl.Enable(not p.useRange and not p.disable)
            if p.valList != []:
                if p.type == Param.Type_BOOL:
                    ctl.SetValue(p.valList[0])
                    ctl.SetLabel(str(p.valList[0]))
                if p.type == Param.Type_STRING:
                    ctl.SetValue(str(p.valList[0]))
                if p.type == Param.Type_CHOICE:
                    ctl.SetSelection(p.valList[0])
                if p.type == Param.Type_INT or p.type == Param.Type_REAL:
                    vals = ''
                    for v in p.valList:
                        vals += str(v) + ' '
                    ctl.SetValue(vals)

            if p.type == Param.Type_INT or p.type == Param.Type_REAL or \
               p.type == Param.Type_CHOICE:
                if p.type != Param.Type_CHOICE:
                    ctl = self.FindWindowByName(p.name +':min')
                    if not ctl: continue
                    if p.minmax[0] == None:
                        ctl.SetValue('unlimited')
                    else:
                        ctl.SetValue(str(p.minmax[0]))
                    ctl.Enable(not p.disable)

                    ctl = self.FindWindowByName(p.name +':max')
                    if not ctl: continue
                    if  p.minmax[1] == None:
                        ctl.SetValue('unlimited')
                    else:
                        ctl.SetValue(str(p.minmax[1]))
                    ctl.Enable(not p.disable)

                ctl = self.FindWindowByName(p.name +':rangeStart')
                if not ctl: continue
                if  p.sweepRange[0] == None:
                    ctl.SetValue('none')
                else:
                    ctl.SetValue(str(p.sweepRange[0]))
                ctl.Enable(p.useRange and not p.disable)

                ctl = self.FindWindowByName(p.name +':rangeEnd')
                if not ctl: continue
                if  p.sweepRange[1] == None:
                    ctl.SetValue('none')
                else:
                    ctl.SetValue(str(p.sweepRange[1]))
                ctl.Enable(p.useRange and not p.disable)

                ctl = self.FindWindowByName(p.name +':rangeDelta')
                if not ctl: continue
                if not core.moeaMode:
                    if p.sweepRange[2] == None:
                        ctl.SetValue('none')
                    else:
                        ctl.SetValue(str(p.sweepRange[2]))
                else:
                    ctl.SetValue(str(p.arithPrec))
                ctl.Enable(p.useRange and not p.disable)

                ctl = self.FindWindowByName(p.name +':useExcept')
                if not ctl: continue
                if p.useExcept:
                    ctl.SetValue(True)
                else:
                    ctl.SetValue(False)
                ctl.Enable(not p.disable)

                ctl0 = self.FindWindowByName(p.name +':exceptAsRange')
                ctl  = self.FindWindowByName(p.name +':exceptAsValues')
                ctlx = self.FindWindowByName(p.name +':excepts')
                if not ctl0 or not ctl or not ctlx: continue
                if not p.useExceptList: # as range
                    ctl0.SetValue(True)
                    vals = ''
                    if p.exceptRange[0] == None:
                        vals += 'none'
                    else :
                        vals += str(p.exceptRange[0])
                    vals += ' / '
                    if p.exceptRange[1] == None:
                        vals += 'none'
                    else:
                        vals += str(p.exceptRange[1])
                    ctlx.SetValue(vals)
                else: # as values
                    ctl.SetValue(True)
                    vals = ''
                    for v in p.excepts:
                        vals += str(v) + ' '
                    ctlx.SetValue(vals)
                ctl0.Enable(p.useExcept and not p.disable)
                ctl.Enable(p.useExcept and not p.disable)
                ctlx.Enable(p.useExcept and not p.disable)

            continue # end of for(p)

        # sweep range text label
        ctl = self.FindWindowByName('sweep_range_text')
        if ctl:
            if not core.moeaMode:
                ctl.SetLabel('sweep range [start/end/delta]')
            else:
                ctl.SetLabel('search range [low/high/precision]')

        # done
        self.Refresh()
        return True

    # event handlers
    def OnName(self, evt):
        """
        パラメータ名のダブルクリックイベントハンドラ
        
        [in] evt  イベント
        """
        if not self.core: return
        core = self.core
        obj = evt.GetEventObject()
        oname = obj.GetName().split(':')
        try:
            param = core.pd.getParam(oname[0])
            if not param: return
            param.disable = not param.disable
            param.disable_gui = param.disable
            if param.disable:
                obj.SetForegroundColour('GRAY')
            elif param.calcCaseNum() < 1:
                obj.SetForegroundColour('RED')
            else:
                obj.SetForegroundColour('BLACK')
            self.Update()
            return
        except:
            self.Update()
        return

    def OnMinMax(self, evt):
        """
        Min/Max欄のイベントハンドラ
        
        [in] evt  イベント
        """
        if not self.core: return
        core = self.core
        obj = evt.GetEventObject()
        oname = obj.GetName().split(':')
        vstr = obj.GetValue()
        try:
            param = core.pd.getParam(oname[0])
            if not param: return
            if vstr == '':
                raise Exception('invalid value')
            if vstr == 'none' or vstr == 'None' or vstr == 'unlimited':
                val = None
            elif param.type == Param.Type_INT:
                val = int(vstr)
            elif param.type == Param.Type_REAL:
                val = float(vstr)
            if oname[1] == 'min':
                if val == None:
                    param.minmax[0] = None
                    self.Update()
                    return
                if param.minmax[1] == None or param.minmax[1] < val:
                    self.Update()
                    return
                mm = [val, param.minmax[1]]
                param.setMinmax(mm)
                self.Update()
            elif oname[1] == 'max':
                if val == None:
                    param.minmax[1] = None
                    self.Update()
                    return
                if param.minmax[0] == None or param.minmax[0] > val:
                    self.Update()
                    return
                mm =[param.minmax[0], val]
                param.setMinmax(mm)
                self.Update()
            else:
                self.Update()
                return
        except:
            self.Update()
        return

    def OnUseValueRange(self, evt):
        """
        use value rangeラジオボタンのイベントハンドラ
        
        [in] evt  イベント
        """
        if not self.core: return
        core = self.core
        obj = evt.GetEventObject()
        oname = obj.GetName().split(':')
        try:
            param = core.pd.getParam(oname[0])
            if not param: return
            if oname[1] == 'useValue':
                param.useRange = False
                self.Update()
            elif oname[1] == 'useRange':
                param.useRange = True
                self.Update()
            else:
                self.Update()
                return
        except:
            self.Update()
        return

    def OnValueTxt(self, evt):
        """
        Value欄のイベントハンドラ
        
        [in] evt  イベント
        """
        if not self.core: return
        core = self.core
        obj = evt.GetEventObject()
        oname = obj.GetName().split(':')
        try:
            param = core.pd.getParam(oname[0])
            if not param: return
            val = obj.GetValue()
            if val == '':
                raise Exception('invalid value')
            if param.type == Param.Type_INT or param.type == Param.Type_REAL:
                vals =  val.split()
                arr = []
                if param.type == Param.Type_INT:
                    for v in vals:
                        x = int(v)
                        if not x in arr and param.isValidValue(x):
                            arr.append(x)
                else:
                    for v in vals:
                        x = float(v)
                        if not x in arr and param.isValidValue(x):
                            arr.append(x)
                param.valList = arr
                param.checkCascadeParam(core.pd)
                self.Update()
            elif param.type == Param.Type_STRING:
                param.valList = [val,]
        except:
            pass
        self.Update()
        return
    def OnValueChoice(self, evt):
        """
        CHOICE型Value欄のイベントハンドラ
        
        [in] evt  イベント
        """
        if not self.core: return
        core = self.core
        obj = evt.GetEventObject()
        oname = obj.GetName().split(':')
        try:
            val = obj.GetSelection()
            if val < 0: return
            param = core.pd.getParam(oname[0])
            if not param: return
            if param.type == Param.Type_CHOICE:
                param.valList = [val,]
                param.checkCascadeParam(core.pd)
            else:
                return
        except:
            pass
        self.Update()
        return
    def OnValueChk(self, evt):
        """
        BOOL型Value欄のイベントハンドラ
        
        [in] evt  イベント
        """
        if not self.core: return
        core = self.core
        obj = evt.GetEventObject()
        oname = obj.GetName().split(':')
        try:
            val = obj.GetValue()
            param = core.pd.getParam(oname[0])
            if not param: return
            if param.type == Param.Type_BOOL:
                param.valList = [val,]
                param.checkCascadeParam(core.pd)
            else:
                return
        except:
            pass
        self.Update()
        return

    def OnSweepRange(self, evt):
        """
        SweepRange欄のイベントハンドラ
        
        [in] evt  イベント
        """
        if not self.core: return
        core = self.core
        obj = evt.GetEventObject()
        oname = obj.GetName().split(':')
        try:
            param = core.pd.getParam(oname[0])
            if not param: return
            vstr = obj.GetValue()
            if vstr == '':
                raise Exception('invalid value')
            if vstr == 'none' or vstr == 'None' or vstr == 'unlimited':
                val = None
            elif param.type == Param.Type_INT or \
                 param.type == Param.Type_CHOICE:
                val = int(vstr)
            elif param.type == Param.Type_REAL:
                val = float(vstr)
            else:
                raise Exception('invalid value')
            if oname[1] == 'rangeStart':
                if val == None:
                    param.sweepRange[0] = None
                    self.Update()
                    return
                if param.sweepRange[1] != None and val > param.sweepRange[1]:
                    raise Exception('invalid value')
                param.sweepRange[0] = val
                self.Update()
                return
            elif oname[1] == 'rangeEnd':
                if val == None:
                    param.sweepRange[1] = None
                    self.Update()
                    return
                if param.sweepRange[0] != None and val < param.sweepRange[0]:
                    raise Exception('invalid value')
                param.sweepRange[1] = val
                self.Update()
                return
            elif oname[1] == 'rangeDelta':
                if core.moeaMode:
                    val = int(vstr) # arithmetic precision, be integer
                    if val == None:
                        self.Update()
                        return
                    if val < 0:
                        raise Exception('invalid value')
                    param.arithPrec = val
                else:
                    if val == None:
                        param.sweepRange[2] = None
                        self.Update()
                        return
                    if val <= 0:
                        raise Exception('invalid value')
                    param.sweepRange[2] = val
                self.Update()
                return
        except:
            self.Update()
        return

    def OnUseExcept(self, evt):
        """
        use expectチェックボックスのイベントハンドラ
        
        [in] evt  イベント
        """
        if not self.core: return
        core = self.core
        obj = evt.GetEventObject()
        oname = obj.GetName().split(':')
        try:
            param = core.pd.getParam(oname[0])
            if not param: return
            if oname[1] != 'useExcept': return
            val = obj.GetValue()
            param.useExcept = val
            self.Update()
            return
        except:
            self.Update()
        return

    def OnUseExceptsRange(self, evt):
        """
        use expect rangeラジオボタンのイベントハンドラ
        
        [in] evt  イベント
        """
        if not self.core: return
        core = self.core
        obj = evt.GetEventObject()
        oname = obj.GetName().split(':')
        try:
            param = core.pd.getParam(oname[0])
            if not param: return
            if oname[1] == 'exceptAsRange':
                param.useExceptList = False
                self.Update()
            elif oname[1] == 'exceptAsValues':
                param.useExceptList = True
                self.Update()
            else:
                return
        except:
            self.Update()
        return

    def OnExcept(self, evt):
        """
        except欄のイベントハンドラ
        
        [in] evt  イベント
        """
        if not self.core: return
        core = self.core
        obj = evt.GetEventObject()
        oname = obj.GetName().split(':')
        try:
            param = core.pd.getParam(oname[0])
            if not param: return
            if param.type != Param.Type_INT and \
               param.type != Param.Type_REAL and \
               param.type != Param.Type_CHOICE:
                raise Exception('invalid type')
            val = obj.GetValue()
            if val == '':
                raise Exception('invalid value')
            if param.useExceptList:
                param.excepts = []
                vals = val.split()
                arr = []
                if param.type == Param.Type_INT or \
                   param.type == Param.Type_CHOICE:
                    for v in vals:
                        x = int(v)
                        if not x in arr and param.isValidValue(x):
                            arr.append(x)
                else:
                    for v in vals:
                        x = float(v)
                        if not x in arr and param.isValidValue(x):
                            arr.append(x)
                param.excepts = arr
                self.Update()
            else:
                param.exceptRange = [None, None]
                vals = val.split('/')
                svals = [vals[0].strip(), vals[1].strip()]
                exceptRange = [None, None]
                if svals[0] == 'none' or svals[0] == 'None' or \
                        svals[0] == 'unlimited':
                    pass
                elif param.type == Param.Type_INT or \
                     param.type == Param.Type_CHOICE:
                    exceptRange[0] = int(svals[0])
                elif param.type == Param.Type_REAL:
                    exceptRange[0] = float(svals[0])
                if svals[1] == 'none' or svals[1] == 'None' or \
                        svals[1] == 'unlimited':
                    pass
                elif param.type == Param.Type_INT or \
                     param.type == Param.Type_CHOICE:
                    exceptRange[1] = int(svals[1])
                elif param.type == Param.Type_REAL:
                    exceptRange[1] = float(svals[1])
                if exceptRange[1] < exceptRange[0]:
                    x = exceptRange[1]
                    exceptRange[1] = exceptRange[0]
                    exceptRange[0] = x
                param.exceptRange = exceptRange
                self.Update()
        except:
            self.Update()
        return
