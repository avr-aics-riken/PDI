#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
GUIアプリケーション機能
ケースディレクトリ設定ダイアログクラス実装
"""

#----------------------------------------------------------------------
# imports library
import sys, os

try:
    import pdi_log
    log = pdi_log._log
    from pdi import *
except Exception, e:
    sys.exit(str(e))

try:
    import wx
except Exception, e:
    sys.exit(str(e))


#----------------------------------------------------------------------
class ExecDirDlg(wx.Dialog):
    """
    HPC/PF PDIサブシステムのケースディレクトリ(実行ディレクトリ)設定用
    ダイアログクラスです。
    wxPythonのDialogクラスの派生クラスであり，独立したウインドウとして
    機能します。
    """
    def __init__(self, parent, ID=-1, title='case directory (exec directory)'):
        """
        初期化

        [in] parent  親ウインドウ
        [in] ID  ウインドウID
        [in] title  ウインドウタイトル
        """
        wx.Dialog.__init__(self, parent, ID, title)
        self.parent = parent
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # text area
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer.Add(hsizer, 0, wx.EXPAND|wx.ALL, 3)
        self.textBox = wx.TextCtrl(self, wx.ID_ANY, size=wx.Size(400,-1))
        hsizer.Add(self.textBox, 1, wx.EXPAND|wx.ALL, 5)
        brwsBtn = wx.Button(self, wx.ID_ANY, '...', style=wx.BU_EXACTFIT)
        hsizer.Add(brwsBtn, 0, wx.ALL, 3)

        vsizer.Add(wx.StaticLine(self, wx.ID_ANY, size=(3,3)), 0,
                   wx.ALL|wx.EXPAND, 5)

        # buttons
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer.Add(hsizer, 0, wx.EXPAND|wx.ALL, 3)

        okBtn = wx.Button(self, wx.ID_ANY, 'OK')
        hsizer.Add(okBtn, 0, wx.ALL, 3)
        hsizer.AddSpacer((5,5))
        cancelBtn = wx.Button(self, wx.ID_ANY, 'Cancel')
        hsizer.Add(cancelBtn, 0, wx.ALL, 3)

        # event handlers
        self.Bind(wx.EVT_BUTTON, self.OnBrwsBtn, brwsBtn)
        self.Bind(wx.EVT_BUTTON, self.OnOkBtn, okBtn)
        self.Bind(wx.EVT_BUTTON, self.OnCancelBtn, cancelBtn)

        # layout
        self.SetAutoLayout(True)
        self.SetSizer(vsizer)
        vsizer.SetSizeHints(self)
        vsizer.Fit(self)

        self.Update()
        return

    def Update(self):
        """
        アップデート処理.

        戻り値 -> 真偽値. 更新に失敗したらFalseを返す.
        """
        if not self.textBox: return False
        try:
            if not self.parent or not self.parent.core: return False
        except:
            return False

        if self.parent.core.exec_dir == None or self.parent.core.exec_dir == '':
            self.parent.core.exec_dir = os.path.getcwd()
            self.textBox.SetValue(self.parent.core.exec_dir)
            return
        self.textBox.SetValue(self.parent.core.exec_dir)
        return

    # event handlers
    def OnBrwsBtn(self, event):
        """
        Brwsボタンのイベントハンドラ

        [in] event  イベント
        """
        if not self.textBox: return
        try:
            if not self.parent or not self.parent.core: return
        except:
            return

        dirDlg = wx.DirDialog(self, "select a case directory to execute",
                              style=wx.DD_DIR_MUST_EXIST)
        if self.parent.core.exec_dir != '':
            dirDlg.SetPath(self.parent.core.exec_dir)
        else:
            dirDlg.SetPath(os.path.getcwd())

        if dirDlg.ShowModal() != wx.ID_OK: return
        d = dirDlg.GetPath()
        self.textBox.SetValue(d)
        return

    def OnOkBtn(self, event):
        """
        OKボタンのイベントハンドラ

        [in] event  イベント
        """
        if not self.textBox: return
        try:
            if not self.parent or not self.parent.core: return
        except:
            return
        core = self.parent.core

        d = str(self.textBox.GetValue())
        if d == core.exec_dir or d == '.':
            if self.IsModal(): self.EndModal(wx.ID_OK)
            else: self.Hide()
            return
        # chdir to exec dir
        if not core.setExecDir(d):
            msgDlg = wx.MessageDialog(self,
                                      u'ディレクトリの移動に失敗しました\n' + d)
            msgDlg.ShowModal()
            if self.IsModal(): self.EndModal(wx.ID_OK)
            else: self.Hide()
            return
        # load snapshot file
        if os.path.exists(pdi_dotf):
            try:
                if not core.loadXML(pdi_dotf, snapshot=True):
                    raise Exception('load snapshot file failed: ' + pdi_dotf)
            except Exception, e:
                log.warn(LogMsg(0, 'load %s/%s file failed\n'
                                % (core.exec_dir, pdi_dotf)))
                log.warn(str(e))
        # done
        if self.IsModal(): self.EndModal(wx.ID_OK)
        else: self.Hide()
        return

    def OnCancelBtn(self, event):
        """
        Cancelボタンのイベントハンドラ

        [in] event  イベント
        """
        if self.IsModal(): self.EndModal(wx.ID_CANCEL)
        else: self.Hide()
        return
