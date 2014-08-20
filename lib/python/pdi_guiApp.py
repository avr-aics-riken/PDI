#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
GUIアプリケーション機能
"""

import sys, os

try:
    import pdi_log
    log = pdi_log._log
    from pdi import *
    from pdi_frame import *
except Exception, e:
    sys.exit(str(e))

try:
    import wx
except Exception, e:
    sys.exit(str(e))


class pdiApp(wx.App):
    """
    PDIのGUIモード用Appクラス
    wx.Appクラスの派生クラスです。
    """
    def __init__(self):
        """
        初期化
        """
        wx.App.__init__(self, False) # 2nd arg 'False' for debug

    def setCore(self, core):
        """
        PDIコアデータの登録

        [in] core PDIコアデータ
        """
        if self._core == core:
            return
        self._core = core
        if self._frame:
            self._frame.CreatePages(self._core)
        return

    def OnInit(self):
        """
        アプリケーション初期化
        wxPythonフレームワークより自動的に呼び出されます．

        戻り値 -> 真偽値
        """
        self._core = None
        self._frame = MainFrame(self)
        self._frame.Show()
        return True
