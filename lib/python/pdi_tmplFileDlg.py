#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
GUIアプリケーション機能
パラメータテンプレートファイル設定ダイアログクラス実装
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


class TemplFileDlg(wx.Dialog):
    """
    HPC/PF PDIサブシステムのパラメータテンプレートファイル設定用
    ダイアログクラスです。
    wxPythonのDialogクラスの派生クラスであり，独立したウインドウとして
    機能します。
    """
    def __init__(self, parent, ID=-1, title='parameter template file(s)'):
        """
        初期化

        [in] parent  親ウインドウ
        [in] ID  ウインドウID
        [in] title  ウインドウタイトル
        """
        wx.Dialog.__init__(self, parent, ID, title)
        self.parent = parent
        vsizer = wx.BoxSizer(wx.VERTICAL)

        self.listBox = wx.ListBox(self, wx.ID_ANY, size=wx.Size(300,200),
                                  style=wx.LB_EXTENDED)
        vsizer.Add(self.listBox, 1, wx.EXPAND|wx.ALL, 5)

        vsizer.Add(wx.StaticLine(self, wx.ID_ANY, size=(3,3)), 0,
                   wx.ALL|wx.EXPAND, 5)

        # buttons
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer.Add(hsizer, 0, wx.EXPAND|wx.ALL, 3)

        addBtn = wx.Button(self, wx.ID_ANY, 'Add')
        hsizer.Add(addBtn, 0, wx.ALIGN_LEFT|wx.ALL, 3)
        hsizer.AddSpacer((5,5))

        delBtn = wx.Button(self, wx.ID_ANY, 'Delete')
        hsizer.Add(delBtn, 0, wx.ALIGN_LEFT|wx.ALL, 3)
        hsizer.AddSpacer((5,5))

        try:
            hsizer.AddStretchSpacer()
        except:
            pass

        closeBtn = wx.Button(self, wx.ID_ANY, 'Close')
        hsizer.Add(closeBtn, 0, wx.ALIGN_RIGHT|wx.ALL, 3)

        # event handlers
        self.Bind(wx.EVT_BUTTON, self.OnAddBtn, addBtn)
        self.Bind(wx.EVT_BUTTON, self.OnDelBtn, delBtn)
        self.Bind(wx.EVT_BUTTON, self.OnCloseBtn, closeBtn)

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

        戻り値 -> bool. 更新に失敗したらFalseを返す.
        """
        if not self.listBox: return False
        try:
            if not self.parent or not self.parent.core: return False
        except:
            return False

        self.listBox.Clear()
        for tp in self.parent.core.templ_pathes:
            tps = os.path.split(tp)
            if tps[1] == '': continue
            if tps[0] == '':
                self.listBox.Append(tps[1] + '  (in  . )')
            else:
                self.listBox.Append(tps[1] + '  (in  %s)' % tps[0])
            continue # end of for(tp)
        return True

    # event handlers
    def OnAddBtn(self, event):
        """
        Addボタンのイベントハンドラ

        [in] event  イベント
        """
        if not self.listBox: return
        try:
            if not self.parent or not self.parent.core: return
        except:
            return

        fileDlg = wx.FileDialog(self, "select parameter template file to open",
                                "", "", "(*)|*", wx.FD_OPEN|wx.FD_MULTIPLE)
        if len(self.parent.core.templ_pathes) > 0:
            d = os.path.dirname(self.parent.core.templ_pathes[-1])
            if d == '':
                fileDlg.SetDirectory(os.getcwd())
            else:
                fileDlg.SetDirectory(d)
        else:
            fileDlg.SetDirectory(os.getcwd())

        if fileDlg.ShowModal() != wx.ID_OK: return
        paths = fileDlg.GetPaths()
        for tp in paths:
            tps = os.path.split(tp)
            if tps[1] == '': continue
            if tp in self.parent.core.templ_pathes: continue
            self.parent.core.templ_pathes.append(tp)
            log.info(LogMsg(0, 'add templ_path: %s' % tp))
            if tps[0] == '':
                self.listBox.AppendAndEnsureVisible(tps[1] + '  (in  . )')
            else:
                self.listBox.AppendAndEnsureVisible(tps[1] +
                                                    '  (in  %s)' % tps[0])
            continue # end of for(tp)
        return

    def OnDelBtn(self, event):
        """
        Deleteボタンのイベントハンドラ

        [in] event  イベント
        """
        if not self.listBox: return
        try:
            if not self.parent or not self.parent.core: return
        except:
            return

        selArr = self.listBox.GetSelections()
        if len(selArr) < 1:
            dlg = wx.MessageDialog(self, 
                                   u'テンプレートファイルが選択されていません',
                                   'pdi message', wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            return
        msg = u'以下のテンプレートファイルをリストから除外しますか\n\n'
        for sel in selArr:
            tps = os.path.split(self.parent.core.templ_pathes[sel])
            if tps[1] == '': continue
            msg += '  %s\n' % tps[1]
            continue # end of for(s)
        dlg = wx.MessageDialog(self, msg, 'pdi message',
                               wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result != wx.ID_OK:
            return

        for sel in selArr:
            log.info(LogMsg(0, 'erase from templ_path: %s' % \
                                self.parent.core.templ_pathes[sel]))

        templ_pathes = []
        idx = 0
        for tp in self.parent.core.templ_pathes:
            if not idx in selArr:
                templ_pathes.append(tp)
            idx += 1
            continue # end of for(tp)
        self.parent.core.templ_pathes = templ_pathes

        self.Update()
        return

    def OnCloseBtn(self, event):
        """
        Closeボタンのイベントハンドラ
        [in] event  イベント
        """
        if self.IsModal(): self.EndModal(wx.ID_CANCEL)
        else: self.Hide()
        return

