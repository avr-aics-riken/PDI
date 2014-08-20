#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
ログ機能実装
"""

import sys, os

# global log entity
_log = None


def LogMsg(code, msg):
    """
    ログ出力文字列の生成

    [in] code  エラーコード
    [in] msg  メッセージ文字列
    戻り値 -> ログ出力文字列
    """
    try:
        lmsg = 'PDI-%03d (%s) %s' % (code, os.getlogin(), msg)
    except Exception, e:
        lmsg = 'PDI-%03d (%s) %s' % (code, "windowsuser", msg)
    return lmsg


def LogSetup(conf_dir, level = None):
    """
    ロギング設定

    [in] conf_dir  HPC/PFコンフィグレーションディレクトリ
    [in] level     loggingログレベル
    戻り値 -> グローバルログ
    """
    global _log

    try:
        import logging # log4j equivalent
        import logging.config
    except Exception, e:
        return None

    if _log != None:
        return _log
    
    log_conf_file = os.path.join(conf_dir, 'PDI_log.conf')
    if os.path.exists(log_conf_file):
        logging.config.fileConfig(log_conf_file)
    else:
        logging.basicConfig()

    _log = logging.getLogger('PDI')

    #_log.setLevel(logging.DEBUG)
    if level:
        _log.setLevel(level)

    return _log

