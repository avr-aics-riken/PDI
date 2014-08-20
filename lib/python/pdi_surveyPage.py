#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
GUIアプリケーション機能
パラメータサーベイページクラス実装
"""

import sys, os, math

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


class SurveyPage(wx.ScrolledWindow):
    """
    HPC/PF PDIサブシステムのパラメータサーベイ設定パネルのクラスです。
    wxPythonのScrolledWindowクラスの派生クラスです。
    """

    def __init__(self, parent, title='_Survey_', bw=3, core=None):
        """
        初期化

        [in] parent  親ウインドウ
        [in] title  ウインドウタイトル
        [in] bw  ボーダー幅
        [in] core  PDIコアデータ
        """
        wx.ScrolledWindow.__init__(self, parent, wx.ID_ANY, name=title)
        self.SetScrollbars(1, 1, 1, 1)
        self.core = core
        self.bw = bw

        # create GridBagSizer (L x 6)
        layout = wx.GridBagSizer()

        # total subcase number
        layout.Add(wx.StaticText(self, wx.ID_ANY, 'Total subcase number'),
                   pos=(0, 0), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, '1', name='totalCaseNum',
                           style=wx.TE_READONLY)
        layout.Add(xTxt, pos=(0, 1), flag=wx.GROW|wx.ALL, border=self.bw)

        # subcase directory number
        sTxt = wx.StaticText(self, wx.ID_ANY, '  subcase directory number')
        xtt = wx.ToolTip(u'作成するサブケースディレクトリ数を設定します')
        sTxt.SetToolTip(xtt)
        layout.Add(sTxt, pos=(1, 0), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, '1', name='wdNum',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(1, 1), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnWdNum)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnWdNum)

        # work directory pattern
        sTxt = wx.StaticText(self, wx.ID_ANY,'  subcase directory pattern')
        xtt = wx.ToolTip(u'サブケースディレクトリパターンを設定します\n'
                         u'パターン中の以下の文字列は置換されます\n'
                         u'   %P  ->  "_" + パラメータ値の並び\n'
                         u'   %Q  ->  "_" + パラメータ名と値の並び\n'
                         u'   #D  ->  "_" + サブケースディレクトリ通番\n'
                         u'   #J  ->  "_" + サブケース通番')
        sTxt.SetToolTip(xtt)
        layout.Add(sTxt, pos=(1, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='wdPattern',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(1, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnWdPattern)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnWdPattern)

        # subcases per directory
        sTxt = wx.StaticText(self, wx.ID_ANY, '  subcases per directory')
        xtt = wx.ToolTip(u'1サブケースディレクトリ当りの'
                         u'サブケース数を設定します')
        sTxt.SetToolTip(xtt)
        layout.Add(sTxt, pos=(2, 0), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, '1', name='casesPerDir',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(2, 1), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnCasesPerDir)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnCasesPerDir)

        # parameter file pattern
        sTxt = wx.StaticText(self, wx.ID_ANY, '  parameter file pattern')
        xtt = wx.ToolTip(u'パラメータファイル名パターンを設定します\n'
                         u'パターン中の以下の文字列は置換されます\n'
                         u'   %T  ->  テンプレートファイルのベース名\n'
                         u'   #D  ->  "_" + サブケースディレクトリ通番\n'
                         u'   #J  ->  "_" + サブケース通番\n'
                         u'   #T  ->  "_" + テンプレートファイル番号\n'
                         u'   #S  ->  "_" + 1ディレクトリ内サブケース番号')
        sTxt.SetToolTip(xtt)
        layout.Add(sTxt, pos=(2, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='pfPattern',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(2, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnPfPattern)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnPfPattern)

        # enable job suspender
        xChk = wx.CheckBox(self, wx.ID_ANY, name='enableSuspender',
                           label='enable job suspender')
        layout.Add(xChk, pos=(3, 0), span=(1, 2), flag=wx.GROW|wx.ALL,
                   border=self.bw)
        self.Bind(wx.EVT_CHECKBOX, self.OnEnableSuspender, xChk)

        # generation loop
        xChk = wx.CheckBox(self, wx.ID_ANY, name='generationLoop',
                           label='generation loop')
        layout.Add(xChk, pos=(3, 3), span=(1, 2), flag=wx.GROW|wx.ALL,
                   border=self.bw)
        self.Bind(wx.EVT_CHECKBOX, self.OnGenerationLoop, xChk)

        # job suspender
        layout.Add(wx.StaticText(self, wx.ID_ANY, '    job suspender'),
                   pos=(4, 0), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='jobSuspender',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(4, 1), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnJobSuspender)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnJobSuspender)
        xBtn = wx.Button(self, wx.ID_ANY, label='...', name='jobSuspenderBrows')
        layout.Add(xBtn, pos=(4, 2), flag=wx.GROW|wx.ALL, border=self.bw)
        self.Bind(wx.EVT_BUTTON, self.OnJobSuspenderBrows, xBtn)

        # max generation
        layout.Add(wx.StaticText(self, wx.ID_ANY, '    max generation'),
                   pos=(4, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, '1', name='maxGeneration',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(4, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnMaxGeneration)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnMaxGeneration)

        # generator
        layout.Add(wx.StaticText(self, wx.ID_ANY, '    generator'),
                   pos=(5, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='generator',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(5, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnGenerator)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnGenerator)
        xBtn = wx.Button(self, wx.ID_ANY, label='...', name='generatorBrows')
        layout.Add(xBtn, pos=(5, 5), flag=wx.GROW|wx.ALL, border=self.bw)
        self.Bind(wx.EVT_BUTTON, self.OnGeneratorBrows, xBtn)

        # score file pattern
        layout.Add(wx.StaticText(self, wx.ID_ANY, '    score file pattern'),
                   pos=(6, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='sfPattern',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(6, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnSfPattern)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnSfPattern)

        layout.AddGrowableCol(1)
        layout.AddGrowableCol(4)
        self.SetSizer(layout)
        layout.Layout()
        self.SetScrollbars(10, 50, 10, 50, 0, 0)
        return

    def Update(self):
        """
        表示のアップデート
        """
        if not self.core: return False
        core = self.core

        # total case number
        ctl = self.FindWindowByName('totalCaseNum')
        if not ctl: return False
        cn = core.getTotalCaseNum()
        if cn < 0: return False
        ctl.SetValue(str(cn))

        # adjust wdNum and casesPerDir
        core.adjustWdnAndCpd()

        # work directory number
        ctl = self.FindWindowByName('wdNum')
        if not ctl: return False
        ctl.SetValue(str(core.wdNum))

        # cases per directory
        ctl = self.FindWindowByName('casesPerDir')
        if not ctl: return False
        ctl.SetValue(str(core.casesPerDir))

        # work directory pattern
        ctl = self.FindWindowByName('wdPattern')
        if not ctl: return False
        ctl.SetValue(core.wdPattern)

        # parameter file pattern
        ctl = self.FindWindowByName('pfPattern')
        if not ctl: return False
        ctl.SetValue(core.pfPattern)

        # enable job suspender
        ctl = self.FindWindowByName('enableSuspender')
        if not ctl: return False
        ctl.SetValue(core.enableSuspender)

        # job suspender
        ctl = self.FindWindowByName('jobSuspender')
        if not ctl: return False
        ctl.SetValue(core.jobSuspender)
        ctl.Enable(core.enableSuspender)
        ctl = self.FindWindowByName('jobSuspenderBrows')
        if not ctl: return False
        ctl.Enable(core.enableSuspender)

        # generation loop
        ctl = self.FindWindowByName('generationLoop')
        if not ctl: return False
        ctl.SetValue(core.generationLoop)

        # max generation
        ctl = self.FindWindowByName('maxGeneration')
        if not ctl: return False
        ctl.SetValue(str(core.maxGeneration))
        ctl.Enable(core.generationLoop)

        # generator
        ctl = self.FindWindowByName('generator')
        if not ctl: return False
        ctl.SetValue(core.generator)
        ctl.Enable(core.generationLoop)
        ctl = self.FindWindowByName('generatorBrows')
        if not ctl: return False
        ctl.Enable(core.generationLoop)

        # score file pattern
        ctl = self.FindWindowByName('sfPattern')
        if not ctl: return False
        ctl.SetValue(core.sfPattern)

        return True

    # enent handlers
    def OnWdNum(self, evt):
        """
        subcase directory number欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        cn = core.getTotalCaseNum()
        ctl = self.FindWindowByName('wdNum')
        if not ctl: return
        try:
            val = int(ctl.GetValue())
            if val < 1 or val > cn: raise Exception('invalid value')
            core.wdNum = val
            core.casesPerDir = int(math.ceil(float(cn)/core.wdNum))
            self.Update()
            if core.wdNum != val:
                dlg = wx.MessageDialog(self, 
                                   u"設定されたディレクトリ数は" +
                                       u"%dに調整されました" % core.wdNum,
                                   "pdi message", wx.OK|wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
        except:
            ctl.SetValue(str(core.wdNum))
        return
    
    def OnCasesPerDir(self, evt):
        """
        subcase number per directory欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        cn = core.getTotalCaseNum()
        ctl = self.FindWindowByName('casesPerDir')
        if not ctl: return
        try:
            val = int(ctl.GetValue())
            if val < 1 or val > cn: raise Exception('invalid value')
            core.casesPerDir = val
            core.wdNum = int(math.ceil(float(cn)/core.casesPerDir))
            self.Update()
        except:
            ctl.SetValue(str(core.casesPerDir))
        return

    def OnWdPattern(self, evt):
        """
        subcase directory pattern欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('wdPattern')
        if not ctl: return
        val = ctl.GetValue()
        core.wdPattern = val
        return

    def OnPfPattern(self, evt):
        """
        parameter file pattern欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('pfPattern')
        if not ctl: return
        val = ctl.GetValue()
        core.pfPattern = val
        return

    def OnEnableSuspender(self, evt):
        """
        enable suspenderチェックボックスのイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('enableSuspender')
        ctl1= self.FindWindowByName('jobSuspender')
        ctl2= self.FindWindowByName('jobSuspenderBrows')
        if not ctl or not ctl1 or not ctl2: return
        val = ctl.GetValue()
        '''
        if val:
            dlg = wx.MessageDialog(self, 
                                   u"本機能は実装されていません",
                                   "pdi message", wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            val = False
            ctl.SetValue(val)
        '''
        ctl1.Enable(val)
        ctl2.Enable(val)
        core.enableSuspender = val
        return

    def OnJobSuspender(self, evt):
        """
        job suspender欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('jobSuspender')
        if not ctl: return
        val = ctl.GetValue()
        core.jobSuspender = val
        '''
        if not os.path.exists(val):
            dlg = wx.MessageDialog(self, 
                                   u"指定されたパスは存在しません",
                                   "pdi message", wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
        '''
        return

    def OnJobSuspenderBrows(self, evt):
        """
        job suspender browsボタンのイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('jobSuspender')
        fileDlg = wx.FileDialog(self, 'select a job suspender file',
                                "", "", '(*)|*', wx.FD_OPEN)
        if core.jobSuspender != '':
            fileDlg.SetPath(core.jobSuspender)
        if fileDlg.ShowModal() != wx.ID_OK: return
        val = fileDlg.GetPath()
        if len(val) < 1: return
        ctl.SetValue(val)
        core.jobSuspender = val
        return

    def OnGenerationLoop(self, evt):
        """
        generation loopチェックボックスのイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('generationLoop')
        ctl1= self.FindWindowByName('maxGeneration')
        ctl2= self.FindWindowByName('generator')
        ctl3= self.FindWindowByName('generatorBrows')
        if not ctl or not ctl1 or not ctl2 or not ctl3: return
        val = ctl.GetValue()
        '''
        if val:
            dlg = wx.MessageDialog(self, 
                                   u"本機能は実装されていません",
                                   "pdi message", wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            val = False
            ctl.SetValue(val)
        '''
        ctl1.Enable(val)
        ctl2.Enable(val)
        ctl3.Enable(val)
        core.generationLoop = val
        return

    def OnMaxGeneration(self, evt):
        """
        max generation欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('maxGeneration')
        if not ctl: return
        try:
            val = int(ctl.GetValue())
            if val < 1: raise Exception('invalid value')
            core.maxGeneration = val
        except:
            ctl.SetValue(str(core.maxGeneration))
        return

    def OnGenerator(self, evt):
        """
        generator欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('generator')
        if not ctl: return
        val = ctl.GetValue()
        core.generator = val
        '''
        if not os.path.exists(val):
            dlg = wx.MessageDialog(self, 
                                   u"指定されたパスは存在しません",
                                   "pdi message", wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
        '''
        return

    def OnGeneratorBrows(self, evt):
        """
        generator browsボタンのイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('generator')
        fileDlg = wx.FileDialog(self, 'select a generator file',
                                "", "", '(*)|*', wx.FD_OPEN)
        if core.generator != '':
            fileDlg.SetPath(core.generator)
        if fileDlg.ShowModal() != wx.ID_OK: return
        val = fileDlg.GetPath()
        if len(val) < 1: return
        ctl.SetValue(val)
        core.generator = val
        return

    def OnSfPattern(self, evt):
        """
        score file pattern欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('sfPattern')
        if not ctl: return
        val = ctl.GetValue()
        core.sfPattern = val
        return
