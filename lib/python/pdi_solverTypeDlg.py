#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
GUIアプリケーション機能
ソルバータイプ選択ダイアログクラス実装
"""

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


class SolverTypeDlg(wx.Dialog):
    """
    HPC/PF PDIサブシステムのソルバータイプ選択用ダイアログクラスです。
    wxPythonのDialogクラスの派生クラスであり，独立したウインドウとして
    機能します。
    """
    def __init__(self, parent, ID=-1, title='select solver type'):
        """
        初期化

        [in] parent  親ウインドウ
        [in] ID  ウインドウID
        [in] title  ウインドウタイトル
        """
        wx.Dialog.__init__(self, parent, ID, title)
        self.parent = parent
        vsizer = wx.BoxSizer(wx.VERTICAL)

        self.listBox = wx.ListBox(self, wx.ID_ANY, size=wx.Size(300,200))
        vsizer.Add(self.listBox, 1, wx.EXPAND|wx.ALL, 5)

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
        アップデート処理

        戻り値 -> 真偽値. 更新に失敗したらFalseを返す.
        """
        if not self.listBox: return False
        try:
            if not self.parent or not self.parent.core: return False
        except:
            return False

        self.listBox.Clear()
        self.listBox.Append('FFB_LES3C')
        self.listBox.Append('FFB_LES3C_MPI')
        self.listBox.Append('FFB_LES3X')
        self.listBox.Append('FFB_LES3X_MPI')
        self.listBox.Append('FFV_C')
        self.listBox.Append('OpenFOAM_icoFoam')
        self.listBox.Append('none')

        ret = self.listBox.SetStringSelection(self.parent.core.solver_type)
        if ret < 0 or self.parent.core.solver_type == '':
            self.listBox.SetStringSelection('none')
        return True

    # event handlers
    def OnOkBtn(self, event):
        """
        OKボタンのイベントハンドラ

        [in] event  イベント
        """
        if not self.listBox: return
        try:
            if not self.parent or not self.parent.core: return
        except:
            return

        sel = self.listBox.GetSelection()
        if sel < 0:
            msgDlg = wx.MessageDialog(self,
                                      u'ソルバータイプが選択されていません.')
            msgDlg.ShowModal()
            return
        selStr = str(self.listBox.GetStringSelection())
        try:
            self.parent.core.setupSolverHints(selStr)
        except Exception, e:
            msgDlg = wx.MessageDialog(self,
                                      u'ソルバータイプの設定に失敗しました\n'
                                      + str(e))
            msgDlg.ShowModal()
            if self.IsModal(): self.EndModal(wx.ID_CANCEL)
            else: self.Hide()
            return

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

