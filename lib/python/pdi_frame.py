#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
GUIアプリケーション機能
メインフレームクラス実装
"""

import sys, os

try:
    import pdi_log
    log = pdi_log._log
    from pdi_desc import *
    from pdi_paramPage import *
    from pdi_surveyPage import *
except Exception, e:
    sys.exit(str(e))

try:
    import wx
except Exception, e:
    sys.exit(str(e))


class MainFrame(wx.Frame):
    """
    HPC/PF PDIサブシステムのメインフレームウインドウのクラスです。
    wxPythonのFrameクラスの派生クラスであり，独立したフレームウインドウとして
    機能します。
    """

    def __init__(self, app, w =980, h =480):
        """
        初期化

        [in] app  アプリケーションクラス
        [in] w  ウィンドウ幅
        [in] h  ウィンドウ高さ
        """
        wx.Frame.__init__(self, None, wx.ID_ANY, 'pdi',
                          wx.DefaultPosition, wx.Size(w,h))
        self.app = app
        self.core = None
        if self.app and self.app._core:
            self.core = self.app._core
        self._notebook = None
        self._pageDict = {}

        # create the menubar
        self.CreateMenuBar()
        
        # create status-bar
        self.CreateStatusBar()

        # create pages
        self.CreatePages()

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Layout()
        self._force_quit = False

        self.UpdateTitle()
        return

    def CreateMenuBar(self):
        """
        メニューバーを構築する．
        """
        menuBar = wx.MenuBar()

        # File menu
        menu = wx.Menu()
        menu.Append(wx.ID_OPEN, "&Load parameter description file...\tCtrl-O",
                    "Load parameter description file")
        menu.Append(wx.ID_SAVE, "&Save parameter description file...\tCtrl-S",
                    "Save parameter description file")
        menu.AppendSeparator()
        mid_setCaseDir = wx.NewId()
        menu.Append(mid_setCaseDir, "Set case directory...",
                    "Set case directory (execution directory)")
        menu.AppendSeparator()
        mid_genSolvParam = wx.NewId()
        menu.Append(mid_genSolvParam, "Generate solver parameter file(s)",
                    "Create work directories and solver parameter files")
        menu.AppendSeparator()
        menu.Append(wx.ID_EXIT, "&Quit\tCtrl-Q", "Quit")
        menuBar.Append(menu, "&File")
        self.Bind(wx.EVT_MENU, self.OnMenuOpen, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnMenuSave, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnMenuCaseDir, id=mid_setCaseDir)
        self.Bind(wx.EVT_MENU, self.OnMenuQuit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.OnMenuGenerate, id=mid_genSolvParam)

        # Edit menu
        menu = wx.Menu()
        mid_setTemplFile = wx.NewId()
        menu.Append(mid_setTemplFile, "Set parameter template file(s)...",
                    "Set parameter template file(s)")
        menu.AppendSeparator()
        mid_setSolverType = wx.NewId()
        menu.Append(mid_setSolverType, "Select solver type...",
                    "Select solver type")
        menuBar.Append(menu, "&Edit")
        self.Bind(wx.EVT_MENU, self.OnMenuTemplates, id=mid_setTemplFile)
        self.Bind(wx.EVT_MENU, self.OnMenuSolverType, id=mid_setSolverType)

        # done
        self.SetMenuBar(menuBar)
        return

    def CreateNewPage(self, parent, title, survey =False):
        """
        ノートブックページを追加する．

        [in] parent  親ウインドウ
        [in] title  タイトル文字列
        [in] survey  サーベイ設定ページフラグ
        戻り値 -> ノートブックページ
        """
        if not parent: return Null
        if survey:
            page = SurveyPage(parent, title, core=self.core)
        else:
            page = ParamPage(parent, title, core=self.core)
        parent.InsertPage(parent.GetPageCount(), page, title)

        if survey:
            return page

        self._pageDict[title] = page
        return page

    def CreatePages(self, core =None):
        """
        ノートブックページを構築する．

        [in] core  PDIコアデータ
        """
        if core:
            self.core = core
        if not self._notebook:
            self._notebook = wx.Notebook(self, wx.ID_ANY)
            self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnChangedPage) 
            self._pageDict = {}
        self._notebook.DeleteAllPages()

        pd = None
        if self.core: pd = self.core.pd
        grpList = []
        if pd:
            page_allgrp = None
            grpList = pd.getGroupList()
            if not self.core.no_all or len(grpList) < 1:
                page_allgrp = self.CreateNewPage(self._notebook, '_All_')

            for g in grpList:
                page = self.CreateNewPage(self._notebook, g)
                continue # end of for(g)

            for p in pd.plist:
                if page_allgrp:
                    page_allgrp.AddParam(p)
                if p.group != '':
                    self._pageDict[p.group].AddParam(p)
                continue # end of for(p)
            if page_allgrp:
                page_allgrp.SetScrollbars(50, 50, 10, 10)
                page_allgrp.AdjustScrollbars()

        for g in grpList:
            try:
                grp_page = self._pageDict[g]
            except:
                continue
            grp_page.SetScrollbars(50, 50, 10, 10)
            grp_page.AdjustScrollbars()
            continue # end of for(g)

        page_survey = self.CreateNewPage(self._notebook, '_Survey_', True)

        self.Update()
        self.UpdateTitle()
        return

    def UpdateTitle(self):
        """
        ウインドウタイトルの更新
        """
        if not self.core or self.core.desc_path == '':
            self.SetTitle('pdi [no param_desc]')
        else:
            self.SetTitle('pdi [%s]' % os.path.basename(self.core.desc_path))
        return

    def Update(self):
        """
        表示の更新

        戻り値 -> 真偽値
        """
        if self._notebook == None or self.core == None:
            return False
        page = self._notebook.GetCurrentPage()
        if not page: return False
        grp = page.GetName()
        if not page.Update():
            return False
        return True
    
    # event handlers
    def OnChangedPage(self, event):
        """
        ノートブックページ変更のイベントハンドラ

        [in] event  イベントデータ
        """
        self.Update()
        return

    # Menu handlers
    def OnMenuOpen(self, event):
        """
        Openメニューのイベントハンドラー

        [in] event イベントデータ
        """
        fileDlg = wx.FileDialog(self, 'select a param desc file',
                                "", "", 'xml file (*.xml)|*.xml|(*)|*',
                                wx.FD_OPEN)
        if self.core.desc_path != '':
            fileDlg.SetPath(self.core.desc_path)
        elif self.core.exec_dir != '':
            fileDlg.SetDirectory(self.core.exec_dir)
        else:
            fileDlg.SetDirectory(os.path.getcwd())
        if fileDlg.ShowModal() != wx.ID_OK: return
        path = fileDlg.GetPath()
        if len(path) < 1: return
        try:
            if not self.core.loadXML(path):
                raise Exception('load param desc file failed')
        except:
            msgDlg = wx.MessageDialog(self,
                                      u'param desc fileのロードに失敗しました\n'
                                      + path)
            msgDlg.ShowModal(); msgDlg.Destroy()
            return
        self.CreatePages()
        return

    def OnMenuSave(self, event):
        """
        Saveメニューのイベントハンドラー

        [in] event イベントデータ
        """
        fileDlg = wx.FileDialog(self, 'select a param desc file',
                                "", "", 'xml file (*.xml)|*.xml|(*)|*',
                                wx.FD_SAVE)
        if self.core.desc_path != '':
            fileDlg.SetPath(self.core.desc_path)
        if fileDlg.ShowModal() != wx.ID_OK: return
        path = fileDlg.GetPath()
        if len(path) < 1: return
        if not path.endswith('.xml'):
            path += '.xml'
        try:
            ofp = open(path, 'r')
            ofp.close()
            msg = 'The specified file has already existed\n  '
            msg += path
            msg += '\n\nAre you sure to override ?\n'
            dlg = wx.MessageDialog(self, msg, 'Save',
                                   wx.OK|wx.CANCEL|wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result != wx.ID_OK:
                return
        except:
            pass
        try:
            if not self.core.saveXML(path):
                raise Exception('save param desc file failed')
        except:
            msgDlg = wx.MessageDialog(self,
                                      u'param desc fileのセーブに失敗しました\n'
                                      + path)
            msgDlg.ShowModal()
            return            
        return

    def OnMenuQuit(self, event):
        """
        Quitメニューのイベントハンドラー

        [in] event  イベントデータ
        """
        self.Close()

    def OnCloseWindow(self, event):
        """
        ウインドウクローズ時のイベントハンドラー
        メインコントロールフレームウインドウのクローズは，
        アプリケーションの終了を意味します．

        [in] event  イベントデータ
        """
        if not self._force_quit:
            dlg = wx.MessageDialog(self, 
                                   #'Do you really want to exit ?',
                                   u'本当に終了しますか ?', 'Confirm Quit',
                                   wx.OK|wx.CANCEL|wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result != wx.ID_OK:
                return
        if self.app:
            self.app.ExitMainLoop()

    def OnMenuGenerate(self, event):
        """
        Generateメニューのイベントハンドラー

        [in] event  イベントデータ
        """
        core = self.core
        cn = core.getTotalCaseNum()
        if cn < 1:
            msgDlg = wx.MessageDialog(self,
                                      u'生成するパラメータケース数が0件です',
                                      'pdi message', wx.OK)
            msgDlg.ShowModal()
            return 
        #if core.out_pattern == '':
        if core.pfPattern == '':
            msgDlg = wx.MessageDialog(self,
                                      u'出力先ディレクトリ・ファイル名の' +
                                      u'パターンが設定されていません',
                                      'pdi message', wx.OK)
            msgDlg.ShowModal()
            return
        if len(core.templ_pathes) < 1:
            msgDlg = wx.MessageDialog(self,
                                      u'パラメータテンプレートファイルが' +
                                      u'設定されていません',
                                      'pdi message', wx.OK)
            msgDlg.ShowModal()
            return

        # generate
        prgDlg = None
        try:
            import pdi_generate
            prgDlg = wx.ProgressDialog('generate solver parameter file(s)',
                                       'creating subcase(s) and paramfile(s)',
                                       maximum=cn, parent=self,
                                       style=wx.PD_CAN_ABORT|wx.PD_APP_MODAL\
                                           |wx.PD_AUTO_HIDE)
            pdi_generate.GenerateParams(core, prgDlg)
        except Exception, e:
            msgDlg = wx.MessageDialog(self,
                                      u'ソルバ入力パラメータファイル生成に' +
                                      u'失敗しました\n\n' + str(e),
                                      'pdi message', wx.OK)
            msgDlg.ShowModal()
        finally:
            if prgDlg: prgDlg.Destroy()
            
        return


    def OnMenuCaseDir(self, event):
        """
        Case directoryメニューのイベントハンドラー

        [in] event  イベントデータ
        """
        try:
            import pdi_execDirDlg
        except:
            return
        dlg = pdi_execDirDlg.ExecDirDlg(self)
        dlg.ShowModal()
        return

    def OnMenuTemplates(self, event):
        """
        Templateメニューのイベントハンドラー

        [in] event  イベントデータ
        """
        try:
            import pdi_tmplFileDlg
        except:
            return
        dlg = pdi_tmplFileDlg.TemplFileDlg(self)
        dlg.ShowModal()
        return

    def OnMenuSolverType(self, event):
        """
        SolverTypeメニューのイベントハンドラー

        [in] event  イベントデータ
        """
        try:
            import pdi_solverTypeDlg
        except:
            return
        dlg = pdi_solverTypeDlg.SolverTypeDlg(self)
        result = dlg.ShowModal()
        if result != wx.ID_OK:
            return
        self.Update()
        return


if __name__ == '__main__':
    """
    テスト用メインルーチン
    """
    app = wx.App()
    f = MainFrame(app)
    f.Show()
    app.MainLoop()

