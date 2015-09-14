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

        # survey type radio
        xRadio = wx.RadioButton(self, wx.ID_ANY, name='survey_simple',
                                label='Simple param survey',
                                style=wx.RB_GROUP)
        xRadio.SetToolTip(wx.ToolTip('select simple parameter survey'))
        layout.Add(xRadio, pos=(0, 0), flag=wx.GROW|wx.ALL, border=self.bw)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnSurveyType, xRadio)

        xRadio = wx.RadioButton(self, wx.ID_ANY, name='survey_moea',
                                label='MOEA param survey')
        xRadio.SetToolTip(wx.ToolTip('select MOEA parameter survey'))
        layout.Add(xRadio, pos=(0, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnSurveyType, xRadio)

        sTxt = wx.StaticText(self, wx.ID_ANY, '  /  ')
        layout.Add(sTxt, pos=(0, 2), flag=wx.GROW|wx.ALL, border=self.bw)

        # left hand side
        row = 1

        # total subcase number
        sTxt = wx.StaticText(self, wx.ID_ANY, 'total subcase number')
        layout.Add(sTxt, pos=(row, 0), flag=wx.GROW|wx.ALL, border=self.bw)
        xtt = wx.ToolTip(u'パラメータスイープの総ケースを表示します'
                         u'(READ ONLY)')
        sTxt.SetToolTip(xtt)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, '1', name='totalCaseNum',
                           style=wx.TE_READONLY)
        layout.Add(xTxt, pos=(row, 1), flag=wx.GROW|wx.ALL, border=self.bw)
        row += 1

        # subcase directory number
        sTxt = wx.StaticText(self, wx.ID_ANY, '  subcase directory number')
        xtt = wx.ToolTip(u'作成するサブケースディレクトリ数を設定します')
        sTxt.SetToolTip(xtt)
        layout.Add(sTxt, pos=(row, 0), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, '1', name='wdNum',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 1), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnWdNum)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnWdNum)
        row += 1

        # subcases per directory
        sTxt = wx.StaticText(self, wx.ID_ANY, '  subcases per directory')
        xtt = wx.ToolTip(u'1サブケースディレクトリ当りの'
                         u'サブケース数を設定します')
        sTxt.SetToolTip(xtt)
        layout.Add(sTxt, pos=(row, 0), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, '1', name='casesPerDir',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 1), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnCasesPerDir)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnCasesPerDir)
        row += 1
        row += 1

        # work directory pattern
        sTxt = wx.StaticText(self, wx.ID_ANY,'subcase directory pattern')
        xtt = wx.ToolTip(u'サブケースディレクトリパターンを設定します\n'
                         u'パターン中の以下の文字列は置換されます\n'
                         u'   %P  ->  "_" + パラメータ値の並び\n'
                         u'   %Q  ->  "_" + パラメータ名と値の並び\n'
                         u'   #D  ->  "_" + サブケースディレクトリ通番\n'
                         u'   #J  ->  "_" + サブケース通番')
        sTxt.SetToolTip(xtt)
        layout.Add(sTxt, pos=(row, 0), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='wdPattern',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 1), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnWdPattern)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnWdPattern)
        row += 1

        # parameter file pattern
        sTxt = wx.StaticText(self, wx.ID_ANY, 'parameter file pattern')
        xtt = wx.ToolTip(u'パラメータファイル名パターンを設定します\n'
                         u'パターン中の以下の文字列は置換されます\n'
                         u'   %T  ->  テンプレートファイルのベース名\n'
                         u'   #D  ->  "_" + サブケースディレクトリ通番\n'
                         u'   #J  ->  "_" + サブケース通番\n'
                         u'   #T  ->  "_" + テンプレートファイル番号\n'
                         u'   #S  ->  "_" + 1ディレクトリ内サブケース番号')
        sTxt.SetToolTip(xtt)
        layout.Add(sTxt, pos=(row, 0), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='pfPattern',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 1), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnPfPattern)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnPfPattern)
        row += 1

        # right hand side
        row = 1

        # number of variable
        sTxt = wx.StaticText(self, wx.ID_ANY, 'design variable number')
        layout.Add(sTxt, pos=(row, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xtt = wx.ToolTip(u'MOEAの設計変数の数を表示します(READ ONLY)\n'
                         u'(レンジが設定されているINT/REALパラメータ)')
        sTxt.SetToolTip(xtt)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, '1', name='moeaVariableNum',
                           style=wx.TE_READONLY)
        layout.Add(xTxt, pos=(row, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        row += 1

        # population
        sTxt = wx.StaticText(self, wx.ID_ANY, 'population')
        layout.Add(sTxt, pos=(row, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xtt = wx.ToolTip(u'MOEAの個体数(4の倍数)を設定します')
        sTxt.SetToolTip(xtt)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, '1', name='population',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnPopulation)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnPopulation)
        row += 1

        # max generation
        sTxt = wx.StaticText(self, wx.ID_ANY, 'max generation')
        layout.Add(sTxt, pos=(row, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xtt = wx.ToolTip(u'MOEAの最大世代値を設定します')
        sTxt.SetToolTip(xtt)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, '1', name='maxGeneration',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnMaxGeneration)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnMaxGeneration)
        row += 1

        # evaluator path
        sTxt = wx.StaticText(self, wx.ID_ANY, 'evaluator path')
        layout.Add(sTxt, pos=(row, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xtt = wx.ToolTip(u'Evaluatorプログラムのパスを設定します')
        sTxt.SetToolTip(xtt)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='evaluator',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnEvaluator)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnEvaluator)
        xBtn = wx.Button(self, wx.ID_ANY, label='...', name='evaluatorBrows',
                         style=wx.BU_EXACTFIT)
        layout.Add(xBtn, pos=(row, 5), flag=wx.GROW|wx.ALL, border=self.bw)
        self.Bind(wx.EVT_BUTTON, self.OnEvaluatorBrows, xBtn)
        row += 1

        # optimizer path
        sTxt = wx.StaticText(self, wx.ID_ANY, 'optimizer path')
        layout.Add(sTxt, pos=(row, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xtt = wx.ToolTip(u'Optimizerプログラムのパスを設定します')
        sTxt.SetToolTip(xtt)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='optimizer',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnOptimizer)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnOptimizer)
        xBtn = wx.Button(self, wx.ID_ANY, label='...', name='optimizerBrows',
                         style=wx.BU_EXACTFIT)
        layout.Add(xBtn, pos=(row, 5), flag=wx.GROW|wx.ALL, border=self.bw)
        self.Bind(wx.EVT_BUTTON, self.OnOptimizerBrows, xBtn)
        row += 1

        # random seed
        sTxt = wx.StaticText(self, wx.ID_ANY, 'random seed')
        layout.Add(sTxt, pos=(row, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xtt = wx.ToolTip(u'乱数シードの値を設定します(0.0～1.0)\n'
                         u'(負値の場合は自動生成)')
        sTxt.SetToolTip(xtt)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='randSeed',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnRandSeed)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnRandSeed)
        row += 1

        # crossover rate
        sTxt = wx.StaticText(self, wx.ID_ANY, 'crossover rate')
        layout.Add(sTxt, pos=(row, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xtt = wx.ToolTip(u'交叉率を設定します(0.0～1.0)')
        sTxt.SetToolTip(xtt)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='crossoverRate',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnCrossoverRate)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnCrossoverRate)
        row += 1

        # mutation rate
        sTxt = wx.StaticText(self, wx.ID_ANY, 'mutation rate')
        layout.Add(sTxt, pos=(row, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xtt = wx.ToolTip(u'突然変異率を設定します(0.0～1.0)\n'
                         u'(負値の場合は1.0/設計変数個数)')
        sTxt.SetToolTip(xtt)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='mutationRate',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnMutationRate)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnMutationRate)
        row += 1
        
        # eta crossover
        sTxt = wx.StaticText(self, wx.ID_ANY, 'eta crossover')
        layout.Add(sTxt, pos=(row, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xtt = wx.ToolTip(u'交叉のdistribution index(5～40)')
        sTxt.SetToolTip(xtt)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='etaCrossover',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnEtaCrossover)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnEtaCrossover)
        row += 1

        # eta mutation
        sTxt = wx.StaticText(self, wx.ID_ANY, 'eta mutation')
        layout.Add(sTxt, pos=(row, 3), flag=wx.GROW|wx.ALL, border=self.bw)
        xtt = wx.ToolTip(u'突然変異のdistribution index(5～50)')
        sTxt.SetToolTip(xtt)
        xTxt = wx.TextCtrl(self, wx.ID_ANY, name='etaMutation',
                           style=wx.TE_PROCESS_ENTER)
        layout.Add(xTxt, pos=(row, 4), flag=wx.GROW|wx.ALL, border=self.bw)
        xTxt.Bind(wx.EVT_TEXT_ENTER, self.OnEtaMutation)
        xTxt.Bind(wx.EVT_KILL_FOCUS, self.OnEtaMutation)
        row += 1

        # history / duplicate
        hsizer = wx.BoxSizer()
        xChk = wx.CheckBox(self, wx.ID_ANY, name='history',
                           label='history')
        xtt = wx.ToolTip(u'history.txt(全評価個体の履歴)を作成するか')
        xChk.SetToolTip(xtt)
        self.Bind(wx.EVT_CHECKBOX, self.OnChecks, xChk)
        hsizer.Add(xChk, 1, flag=wx.GROW)
        xChk = wx.CheckBox(self, wx.ID_ANY, name='duplicate',
                           label='duplicate')
        xtt = wx.ToolTip(u'重複する設計点を作成するか')
        xChk.SetToolTip(xtt)
        self.Bind(wx.EVT_CHECKBOX, self.OnChecks, xChk)
        hsizer.Add(xChk, 1, flag=wx.GROW)
        layout.Add(hsizer, pos=(row, 4), flag=wx.GROW|wx.ALL, border=self.bw)

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

        # survey mode
        ctl0 = self.FindWindowByName('survey_simple')
        ctl = self.FindWindowByName('survey_moea')
        if not core.moeaMode:
            if ctl0: ctl0.SetValue(True)
            if ctl: ctl.SetValue(False)
        else:
            if ctl0: ctl0.SetValue(False)
            if ctl: ctl.SetValue(True)

        # set enable/disable according to survey mode
        ctl = self.FindWindowByName('totalCaseNum')
        if ctl: ctl.Enable(not core.moeaMode)
        ctl = self.FindWindowByName('wdNum')
        if ctl: ctl.Enable(not core.moeaMode)
        ctl = self.FindWindowByName('casesPerDir')
        if ctl: ctl.Enable(not core.moeaMode)
        """
        ctl = self.FindWindowByName('wdPattern')
        if ctl: ctl.Enable(not core.moeaMode)
        ctl = self.FindWindowByName('pfPattern')
        if ctl: ctl.Enable(not core.moeaMode)
        """

        ctl = self.FindWindowByName('moeaVariableNum')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('population')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('maxGeneration')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('evaluator')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('evaluatorBrows')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('optimizer')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('optimizerBrows')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('randSeed')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('crossoverRate')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('mutationRate')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('etaCrossover')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('etaMutation')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('history')
        if ctl: ctl.Enable(core.moeaMode)
        ctl = self.FindWindowByName('duplicate')
        if ctl: ctl.Enable(core.moeaMode)


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


        # design variable number
        ctl = self.FindWindowByName('moeaVariableNum')
        if not ctl: return False
        vn = core.moea.getDesignVariableNum(core.pd)
        if vn < 0: return False
        ctl.SetValue(str(vn))

        # population
        ctl = self.FindWindowByName('population')
        if not ctl: return False
        ctl.SetValue(str(core.moea.population))

        # max generation
        ctl = self.FindWindowByName('maxGeneration')
        if not ctl: return False
        ctl.SetValue(str(core.moea.maxGeneration))

        # evaluator
        ctl = self.FindWindowByName('evaluator')
        if not ctl: return False
        ctl.SetValue(core.moea.evaluator)

        # optimizer
        ctl = self.FindWindowByName('optimizer')
        if not ctl: return False
        ctl.SetValue(core.moea.optimizer)

        # random seed
        ctl = self.FindWindowByName('randSeed')
        if not ctl: return False
        ctl.SetValue(str(core.moea.randSeed))

        # crossover rate
        ctl = self.FindWindowByName('crossoverRate')
        if not ctl: return False
        ctl.SetValue(str(core.moea.crossoverRate))

        # mutation rate
        ctl = self.FindWindowByName('mutationRate')
        if not ctl: return False
        ctl.SetValue(str(core.moea.mutationRate))

        # eta crossover
        ctl = self.FindWindowByName('etaCrossover')
        if not ctl: return False
        ctl.SetValue(str(core.moea.etaCrossover))

        # eta mutation
        ctl = self.FindWindowByName('etaMutation')
        if not ctl: return False
        ctl.SetValue(str(core.moea.etaMutation))

        # history
        ctl = self.FindWindowByName('history')
        if not ctl: return False
        ctl.SetValue(core.moea.history)

        # duplicate
        ctl = self.FindWindowByName('duplicate')
        if not ctl: return False
        ctl.SetValue(core.moea.duplicate)

        return True

    # enent handlers
    def OnSurveyType(self, evt):
        """
        select survey type欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl1 = self.FindWindowByName('survey_simple')
        ctl2 = self.FindWindowByName('survey_moea')
        if not ctl1 and not ctl2: return
        if ctl1.GetValue():
            core.moeaMode = False
        elif ctl2.GetValue():
            core.moeaMode = True
        self.Update()
        return

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

    def OnPopulation(self, evt):
        """
        population欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('population')
        if not ctl: return
        try:
            val = int(ctl.GetValue())
            if val < 1:
                raise Exception('invalid value ( < 1 )')
            if val % 4 != 0:
                dlg = wx.MessageDialog(self, 
                                   u'populationは4の倍数である必要があります',
                                   'pdi message', wx.OK|wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                raise Exception('invalid value ( mod(4) != 0 )')
            core.moea.population = val
        except:
            ctl.SetValue(str(core.moea.population))
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
            core.moea.maxGeneration = val
        except:
            ctl.SetValue(str(core.moea.maxGeneration))
        return

    def OnEvaluator(self, evt):
        """
        evaluator path欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('evaluator')
        if not ctl: return
        val = ctl.GetValue()
        core.moea.evaluator = val
        return

    def OnEvaluatorBrows(self, evt):
        """
        evaluator browsボタンのイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        fileDlg = wx.FileDialog(self, 'select a evaluator program path',
                                "", "", '(*)|*', wx.FD_OPEN)
        if len(core.moea.evaluator) > 0:
            fileDlg.SetPath(core.moea.evaluator)
        elif core.exec_dir != '':
            fileDlg.SetDirectory(core.exec_dir)
        else:
            fileDlg.SetDirectory(os.path.getcwd())
        if fileDlg.ShowModal() != wx.ID_OK: return
        path = fileDlg.GetPath()
        if len(path) < 1: return
        core.moea.evaluator = path
        self.Update()
        return

    def OnOptimizer(self, evt):
        """
        optimizer path欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('optimizer')
        if not ctl: return
        val = ctl.GetValue()
        core.moea.optimizer = val
        return

    def OnOptimizerBrows(self, evt):
        """
        optimizer browsボタンのイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        fileDlg = wx.FileDialog(self, 'select a optimizer program path',
                                "", "", '(*)|*', wx.FD_OPEN)
        if len(core.moea.optimizer) > 0:
            fileDlg.SetPath(core.moea.optimizer)
        elif core.exec_dir != '':
            fileDlg.SetDirectory(core.exec_dir)
        else:
            fileDlg.SetDirectory(os.path.getcwd())
        if fileDlg.ShowModal() != wx.ID_OK: return
        path = fileDlg.GetPath()
        if len(path) < 1: return
        core.moea.optimizer = path
        self.Update()
        return

    def OnRandSeed(self, evt):
        """
        random seed欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('randSeed')
        if not ctl: return
        try:
            val = float(ctl.GetValue())
            if val > 1.0: raise Exception('invalid value')
            elif val < 0.0: val = -1.0
            core.moea.randSeed = val
            self.Update()
        except:
            ctl.SetValue(str(core.moea.randSeed))
        return

    def OnCrossoverRate(self, evt):
        """
        crossover rate欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('crossoverRate')
        if not ctl: return
        try:
            val = float(ctl.GetValue())
            if val < 0.0 or val > 1.0: raise Exception('invalid value')
            core.moea.crossoverRate = val
            self.Update()
        except:
            ctl.SetValue(str(core.moea.crossoverRate))
        return

    def OnMutationRate(self, evt):
        """
        mutation rate欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('mutationRate')
        if not ctl: return
        try:
            val = float(ctl.GetValue())
            if val > 1.0: raise Exception('invalid value')
            elif val < 0.0: val = -1.0
            core.moea.mutationRate = val
            self.Update()
        except:
            ctl.SetValue(str(core.moea.mutationRate))
        return

    def OnEtaCrossover(self, evt):
        """
        eta crossover欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('etaCrossover')
        if not ctl: return
        try:
            val = int(ctl.GetValue())
            if val < 5 or val > 40: raise Exception('invalid value')
            core.moea.etaCrossover = val
        except:
            ctl.SetValue(str(core.moea.etaCrossover))
        return

    def OnEtaMutation(self, evt):
        """
        eta mutation欄のイベントハンドラ

        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        ctl = self.FindWindowByName('etaMutation')
        if not ctl: return
        try:
            val = int(ctl.GetValue())
            if val < 5 or val > 50: raise Exception('invalid value')
            core.moea.etaMutation = val
        except:
            ctl.SetValue(str(core.moea.etaMutation))
        return

    def OnChecks(self, evt):
        """
        history, duplicateのイベントハンドラ
        
        [in] evt  イベント
        """
        if not self.core: return False
        core = self.core
        obj = evt.GetEventObject()
        val = obj.GetValue()
        oname = obj.GetName()
        if oname == 'history':
            core.moea.history = val
        elif oname == 'duplicate':
            core.moea.duplicate = val
        return
