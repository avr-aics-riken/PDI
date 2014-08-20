#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
テンプレート変換機能
"""

import sys, os
import re
import ast

try:
    import pdi_log
    log = pdi_log._log
    LogMsg = pdi_log.LogMsg
except Exception, e:
    sys.exit(str(e))

try:
    import pdi_desc
except Exception, e:
    log.error(LogMsg(51, 'pdi_desc module import failed'))
    log.error(e)

#----------------------------------------------------------------------
# utils
def GetSurrogateFunc(expression='VAL'):
    """
    式をPython関数にコンパイルする
    　式は
    [in]expression  VALを変数としたPythonの式の文字列
    戻り値 -> サロゲート関数
    """
    # ベースになる関数のソース
    defun = "def surrogate(VAL): return True\n";

    # ASTにパース
    xast = ast.parse(defun, mode='single')

    # AST中のベース関数の戻り値(True)を、expressionのASTノードに置き換え
    xast.body[0].body[0].value = \
        ast.parse(expression, mode='single').body[0].value

    # Pythonコードにコンパイル
    com = compile(xast, '<string>', 'single')

    # 関数定義をサンドボックス内で実行
    locals={}
    eval(com, {}, locals)

    # 定義された関数を返す
    return locals['surrogate']


def DecompPattern(s):
    """
    パラメータ記述形式の分解
      記述形式 ::= %パラメータ名[!デフォルト値][：式(VAL)]%
      記述形式 ::= %パラメータ名[!デフォルト値][＊数値][＋数値]%

    [in] s  パラメータ記述文字列
    戻り値 -> (パラメータ名, デフォルト値, サロゲート関数, 掛ける数値, 加算値)
    """
    (nm, dv, sf, v1, v2) = (None, '', None, None, None)
    if not s or len(s) < 3: return (nm, dv, sf, v1, v2)
    ss = s[1:-1].strip() # omit '%'s
    # 式表現かどうかの判定(':'が含まれるか)
    toks = ss.split(':')
    if len(toks) > 1:
        # ':'以降の式をサロゲート関数に変換する
        sf = GetSurrogateFunc(toks[1])
        ss = toks[0]
    else:
        # 一次式形式('*', '+'を含む)
        toks = ss.split('+')
        if len(toks) > 1:
            #v2 = float(toks[1])
            v2 = toks[1]
            ss = toks[0]
        toks = ss.split('*')
        if len(toks) > 1:
            #v1 = float(toks[1])
            v1 = toks[1]
            ss = toks[0]
    # パラメータ名とデフォルト値の分解
    toks = ss.split('!')
    if len(toks) > 1:
        dv = toks[1]
        ss = toks[0]
    nm = ss
    return (nm, dv, sf, v1, v2)

#----------------------------------------------------------------------
# process
def ConvTmpl(inpath, outpath, paramDesc, xpl=None):
    """
    テンプレートファイルの変換

    [in] inpath  入力ファイル(パラメータテンプレートファイル)のパス
    [in] outpath  出力ファイル(生成するパラメータファイル)のパス
    [in] paramDesc  パラメータ記述データ
    [in] xpl  スイープパラメータ辞書(key=パラメータ名, value=パラメータ値)
    戻り値 -> 真偽値
    """
    if not inpath or not outpath or not paramDesc:
        return False

    try:
        fin = open(inpath, 'r')
    except Exception, e:
        log.error(LogMsg(61, 'can not open file: ' + inpath))
        log.error(e)
        return False
    try:
        fout = open(outpath, 'w')
    except Exception, e:
        log.error(LogMsg(62, 'can not open file: ' + outpath))
        log.error(e)
        fin.close()
        return False

    pat = re.compile('%.+?%') # '?' must be specified for minimal match
    for l in fin:
        res = pat.search(l)
        while res:
            (nm, dv, sf, v1, v2) = DecompPattern(res.group())
            param = paramDesc.getParam(nm)
            valStr = ''
            if param and not param.disable:
                if param.type == pdi_desc.Param.Type_INT or \
                        param.type == pdi_desc.Param.Type_REAL:
                    if xpl and nm in xpl:
                        val = xpl[nm]
                    else:
                        val = param.getValue()
                    if sf:
                        try:
                            val = sf(val)
                        except:
                            pass
                    else:
                        try:
                            if v1: val = val * float(v1)
                            if v2: val = val + float(v2)
                        except:
                            pass
                    valStr = str(val)
                elif param.type == pdi_desc.Param.Type_BOOL:
                    if xpl and nm in xpl:
                        valStr = str(xpl[nm])
                    else:
                        valStr = str(param.getValue())
                    if valStr == 'True':
                        if v1: valStr = v1
                    else:
                        if v2: valStr = v2
                else:
                    if xpl and nm in xpl:
                        valStr = str(xpl[nm])
                    else:
                        valStr = str(param.getValue())
            else:
                valStr = dv

            l = pat.sub(valStr, l, 1)
            res = pat.search(l)
            continue # end of while(res)

        try:
            fout.write(l)
        except Exception, e:
            log.error(LogMsg(63, 'write failed to file: ' + outpath))
            log.error(e)
            fin.close()
            fout.close()
            return False
        continue # end of for(l)

    fin.close()
    fout.close()
    return True
