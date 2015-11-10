#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
パラメータ記述データ
"""

import sys, os
try:
    import pdi_log
    log = pdi_log._log
    LogMsg = pdi_log.LogMsg
    from pdi_cond import *
    from xml.dom import minidom
except Exception, e:
    sys.exit('PDI: ' + str(e))

def conv_text(x):
    """
    Unicodeの非正規文字変換
    Pythonでencode()に失敗するUnicode文字を、変換可能な文字に置き換えます。

    [in] x  変換文字列
    戻り値 -> 返還後文字列
    """
    # ハイフン
    x = x.replace(u'\u00ad', u'\u002d')
    x = x.replace(u'\u2011', u'\u002d')
    x = x.replace(u'\u2012', u'\u002d')
    x = x.replace(u'\u2013', u'\u002d')
    x = x.replace(u'\u2043', u'\u002d')
    x = x.replace(u'\ufe63', u'\u002d')
    # マイナス
    x = x.replace(u'\u2212', u'\u002d')
    x = x.replace(u'\u207b', u'\u002d')
    x = x.replace(u'\u208b', u'\u002d')
    x = x.replace(u'\uff0d', u'\u002d')
    # 罫線
    x = x.replace(u'\u2500', u'\u002d')
    x = x.replace(u'\u2501', u'\u002d')
    # 下線
    x = x.replace(u'\uff3f', u'\u005f')
    # 上線
    x = x.replace(u'\u00af', u'\u002d')
    x = x.replace(u'\u203e', u'\u002d')
    x = x.replace(u'\uffe3', u'\u002d')
    # 引用
    x = x.replace(u'\u2014', u'\u002d')
    x = x.replace(u'\u2015', u'\u002d')
    # 音引き
    x = x.replace(u'\u30fc', u'\u002d')
    # 波線
    x = x.replace(u'\u223c', u'\u007e')
    x = x.replace(u'\u223e', u'\u007e')
    x = x.replace(u'\u301c', u'\u007e')
    x = x.replace(u'\u3030', u'\u007e')
    x = x.replace(u'\uff5e', u'\u007e')
    # 3点リーダ
    x = x.replace(u'\u2026', u'\u002d')
    x = x.replace(u'\u22ef', u'\u002d')
    # 中点
    x = x.replace(u'\u00b7', u'\u002d')
    x = x.replace(u'\u2022', u'\u002d')
    x = x.replace(u'\u2219', u'\u002d')
    x = x.replace(u'\u22c5', u'\u002d')
    x = x.replace(u'\u30fb', u'\u002d')
    x = x.replace(u'\uff65', u'\u002d')
    return x


#----------------------------------------------------------------------
# class Param

class Param(object):
    """
    Paramクラス
    パラメータ記述データファイルの<param>タグに対応するクラスです。

    メンバ変数
      (string)name         パラメータ名
      (enum)type           パラメータタイプ
      (void[])valList       パラメータ値リスト
      (string)desc         パラメータ項目説明
      (string)group        所属パラメータグループ名
      (void[2])minmax      値域(タイプがINTまたはREALの場合のみ有効)
      (string[])citems     選択文字列リスト(タイプがCHOICEの場合のみ有効)
      (Cond)depend_cond    パラメータ依存条件への参照
      (bool)useRange       レンジによるパラメータスイープフラグ
      (void[3])sweepRange  パラメータスイープのレンジ[start/end/delta]
                           (タイプがINTまたはREALの場合のみ有効)
      (int)arithPrec       少数点以下の桁数(MOEA)
      (bool)useExcept      除外値参照フラグ
      (bool)useExceptList  除外値リスト参照フラグ
      (void[])excepts      除外値リスト
      (void[2])exceptRange 除外値範囲(タイプがINTまたはREALの場合のみ有効)
      (bool)disable        無効化フラグ
      (bool)disable_gui    GUIによる無効化フラグ
      (Param[])cascadeParams  影響を与えるパラメータのリスト
    """

    (Type_INT, Type_REAL, Type_BOOL, Type_STRING, Type_CHOICE) = range(5)

    def __init__(self):
        """
        初期化
        """
        self.name = ''
        self.type = Param.Type_INT
        self.valList = []
        self.desc = ''
        self.group = ''
        self.minmax = [None, None]
        self.citems = []
        self.depend_cond = None
        self.useRange = False
        self.sweepRange = [None, None, None]
        self.arithPrec = 0
        self.useExcept = False
        self.useExceptList = True
        self.excepts = []
        self.exceptRange = [None, None]
        self.disable = False
        self.disable_gui = False
        self.cascadeParams = []
        self.allowNullStr = True
        return

    def __str__(self):
        """
        値の文字列化

        戻り値 -> 文字列
        """
        ret = self.name + '='
        try:
            if self.type == Param.Type_INT or self.type == Param.Type_REAL:
                if self.minmax[0] and self.valList[0] < self.minmax[0]:
                    ret = ret + str(self.minmax[0])
                elif self.minmax[1] and self.valList[0] > self.minmax[1]:
                    ret = ret + str(self.minmax[1])
                else:
                    ret = ret + str(self.valList[0])
                if self.type == Param.Type_INT:
                    ret = ret + '(INT)'
                else:
                    ret = ret + '(REAL)'
            elif self.type == Param.Type_BOOL or self.type == Param.Type_STRING:
                ret = ret + self.valList[0]
                if self.type == Param.Type_BOOL:
                    ret = ret + '(BOOL)'
                else:
                    ret = ret + '(STRING)'
            elif self.type == Param.Type_CHOICE:
                ret = ret + self.citems[self.valList[0]] \
                    + '(CHOICE:%d)' % self.valList[0]
        except:
            pass
        return ret

    def getValue(self, idx=0):
        """
        パラメータ値の取得

        [in] idx  取得するパラメータ値のインデックス番号
        戻り値 -> パラメータ値
        """
        try:
            if self.type == Param.Type_INT or self.type == Param.Type_REAL:
                return self.valList[idx]
            elif self.type == Param.Type_CHOICE:
                return self.citems[self.valList[idx]]
            else:
                return str(self.valList[0])
        except:
            return None

    def setValue(self, value, idx=0):
        """
        パラメータ値の設定

        [in] value  設定するパラメータ値
        [in] idx  パラメータ値を設定するインデックス番号
        """
        try:
            if self.type == Param.Type_INT or self.type == Param.Type_REAL:
                if self.minmax[0] and value < self.minmax[0]:
                    self.valList[idx] = self.minmax[0]
                elif self.minmax[1] and value > self.minmax[1]:
                    self.valList[idx] = self.minmax[1]
                else:
                    self.valList[idx] = value
            elif self.type == Param.Type_BOOL:
                sval = str(value).lower()
                if sval in ['true', 'yes']:
                    self.valList[idx] = True
                elif sval in ['false', 'no']:
                    self.valList[idx] = False
                else:
                    return
            elif self.type == Param.Type_CHOICE:
                try:
                    ival = int(value)
                    if ival < 0:
                        self.valList[idx] = 0
                    elif ival >= len(self.citems):
                        self.valList[idx] = len(self.citems) -1
                    else:
                        self.valList[idx] = ival
                except:
                    try:
                        ival = self.citems.index(value)
                        self.valList[idx] = ival
                    except:
                        return
            else:
                self.valList[idx] = str(value)
        except:
            return

    def setMinmax(self, vminmax):
        """
        値域の設定

        [in] vminmax  設定する値域
        戻り値 -> 真偽値
        """
        if len(vminmax) < 2: return False
        try:
            if self.type == Param.Type_INT:
                if vminmax[0] > vminmax[1]: return False
                self.minmax[0] = int(vminmax[0])
                self.minmax[1] = int(vminmax[1])
            elif self.type == Param.Type_REAL:
                if vminmax[0] > vminmax[1]: return False
                self.minmax[0] = float(vminmax[0])
                self.minmax[1] = float(vminmax[1])
            else:
                return False
        except:
            return False
        return True

    def setSweepRange(self, vsweep):
        """
        レンジ・刻み幅の設定

        [in] vsweep  設定するレンジ・刻み幅
        戻り値 -> 真偽値
        """
        if len(vsweep) < 3: return False
        try:
            if self.type == Param.Type_INT or \
               self.type == Param.Type_CHOICE:
                if vsweep[0] > vsweep[1]: return False
                self.sweepRange[0] = int(vsweep[0])
                self.sweepRange[1] = int(vsweep[1])
                self.sweepRange[2] = int(vsweep[2])
            elif self.type == Param.Type_REAL:
                if vsweep[0] > vsweep[1]: return False
                self.sweepRange[0] = float(vsweep[0])
                self.sweepRange[1] = float(vsweep[1])
                self.sweepRange[2] = float(vsweep[2])
            else:
                return False
        except:
            return False
        return True

    def checkCascadeParam(self, pd):
        """
        影響を与えるパラメータのチェック

        [in] pd  パラメータ記述データ
        """
        if not pd or pd == []: return False
        for cp in self.cascadeParams:
            cp.checkDepCond(pd)
            continue # end of for(cp)
        return

    def checkDepCond(self, pd):
        """
        影響を受けるパラメータのチェック

        [in] pd  パラメータ記述データ
        戻り値 -> 真偽値
        """
        if not pd or pd == []: return False
        if self.depend_cond == None: return True
        dcond = pd.getParam(self.depend_cond.target)
        if not dcond:
            log.warn(LogMsg(0, 'no dependancy target: param=%s, target=%s' % \
                                (self.name, self.depend_cond.target)))
            return False
        dcond2 = pd.getParam(self.depend_cond.target2)
        if self.depend_cond.target2 and not dcond2:
            log.warn(LogMsg(0, 'no dependancy target: param=%s, target=%s' % \
                                (self.name, self.depend_cond.target2)))
            return False

        dep_state = None
        dep_ret = self.depend_cond.judge(dcond, dcond2)
        if dep_ret:
            dep_state = self.depend_cond.st_true
        else:
            dep_state = self.depend_cond.st_false
        if not dep_state:
            log.warn(LogMsg(0, 'invalid dependancy target: param=%s,' \
                                % self.name
                            + ' target=%s, target2=%s' \
                                % (self.depend_cond.target,
                                   str(self.depend_cond.target2))))
            return False

        if dep_state.command == pdi_desc.Statement.Com_Enable:
            self.disable = False
        elif dep_state.command == pdi_desc.Statement.Com_Disable:
            self.disable = True
        elif dep_state.command == pdi_desc.Statement.Com_SetVal:
            if self.setValue(dep_state.set_value):
                self.useRange = False
                self.disable = False
        elif dep_state.command == pdi_desc.Statement.Com_SetMinmax:
            if self.setMinmax(dep_state.set_minmax):
                self.disable = False
        elif dep_state.command == pdi_desc.Statement.Com_SetSweep:
            if self.setSweepRange(dep_state.set_sweep):
                self.useRange = True
                self.disable = False
        elif dep_state.command == pdi_desc.Statement.Com_Pass:
            pass
        else:
            log.warn(LogMsg(0, 'invalid dependancy statement: param=%s,' \
                                % self.name
                            + ' target=%s, target2=%s' \
                                % (self.depend_cond.target,
                                   str(self.depend_cond.target2))))
            return False
        return True

    def isValidValue(self, val):
        """
        パラメータ値としての有効性判定

        [in] val  判定値
        戻り値 -> 真偽値
        """
        if self.type == Param.Type_INT:
            if self.minmax[0] != None and val < self.minmax[0]: return False
            if self.minmax[1] != None and val > self.minmax[1]: return False
            if self.useExcept:
                if self.useExceptList:
                    for x in self.excepts:
                        if val == x: return False
                elif self.exceptRange[0] !=None and self.exceptRange[1] !=None:
                    if val >=self.exceptRange[0] and val <=self.exceptRange[1]:
                        return False
            return True
        if self.type == Param.Type_REAL:
            delta = 1e-12
            if self.minmax[0] != None and val < self.minmax[0] - delta:
                return False
            if self.minmax[1] != None and val > self.minmax[1] + delta:
                return False
            if self.useExcept:
                if self.useExceptList:
                    for x in self.excepts:
                        if abs(val - x) < delta: return False
                elif self.exceptRange[0] !=None and self.exceptRange[1] !=None:
                    if val >= self.exceptRange[0] - delta and \
                            val <= self.exceptRange[1] + delta:
                        return False
            return True
        if self.type == Param.Type_BOOL:
            return True
        if self.type == Param.Type_STRING:
            return True
        if self.type == Param.Type_CHOICE:
            if type(val) == type(0):
                if val < 0 or val >= len(self.citems): return False
                if self.useExcept:
                    if self.useExceptList:
                        for x in self.excepts:
                            if val == x: return False
                    elif self.exceptRange[0] != None and \
                         self.exceptRange[1] != None:
                        if val >= self.exceptRange[0] and \
                           val <= self.exceptRange[1]:
                            return False
            else:
                if not val in self.citems: return False
            return True
        return False
    
    def generateValueList(self):
        """
        パラメータサーベイ時のパラメータ値リストの生成

        戻り値 -> パラメータ値リスト
        """
        vl = []
        if self.valList == []: return vl
        if self.type == Param.Type_INT or self.type == Param.Type_REAL:
            if self.useRange:
                if self.sweepRange[0] != None and self.sweepRange[1] != None \
                        and self.sweepRange[2] != None:
                    delta = 0
                    if self.type == Param.Type_REAL:
                        delta = self.sweepRange[2] / 100.0
                    v = self.sweepRange[0]
                    if self.isValidValue(v):
                        vl.append(v)
                    while v < self.sweepRange[1]:
                        v += self.sweepRange[2]
                        if v > self.sweepRange[1] + delta:
                            break
                        if self.isValidValue(v):
                            vl.append(v)
                        continue # end of while(v)
                    if self.sweepRange[1] - v > delta:
                        if self.isValidValue(v):
                            vl.append(v)
                else:
                    return vl
            else:
                for v in self.valList:
                    if self.isValidValue(v):
                        vl.append(v)
            return vl
        if self.type == Param.Type_BOOL:
            if self.useRange:
                vl = [True, False]
            else:
                vl = [self.valList[0],]
            return vl
        if self.type == Param.Type_STRING:
            vl = [self.valList[0],]
            return vl
        if self.type == Param.Type_CHOICE:
            if self.useRange:
                if self.sweepRange[0] != None and self.sweepRange[1] != None \
                        and self.sweepRange[2] != None:
                    v = self.sweepRange[0]
                    if self.isValidValue(v):
                        vl.append(self.citems[v])
                    while v < self.sweepRange[1]:
                        v += self.sweepRange[2]
                        if v > self.sweepRange[1]:
                            break
                        if self.isValidValue(v):
                            vl.append(self.citems[v])
                        continue # end of while(v)
                    if self.sweepRange[1] - v > 0:
                        if self.isValidValue(v):
                            vl.append(self.citems[v])
                else:
                    return vl
            else:
                for v in self.valList:
                    if self.isValidValue(v):
                        vl.append(self.citems[v])
            return vl

        return vl

    def calcCaseNum(self):
        """
        パラメータサーベイ時のパラメータケース数の計算

        戻り値 -> パラメータケース数
        """
        if self.type == Param.Type_INT or self.type == Param.Type_REAL or \
           self.type == Param.Type_CHOICE:
            c = 0
            if self.useRange:
                if self.sweepRange[0] != None and self.sweepRange[1] != None \
                        and self.sweepRange[2] != None:
                    delta = 0
                    if self.type == Param.Type_REAL:
                        delta = self.sweepRange[2] / 100.0
                    v = self.sweepRange[0]
                    if self.isValidValue(v):
                        c += 1
                    while v < self.sweepRange[1]:
                        v += self.sweepRange[2]
                        if v > self.sweepRange[1] + delta:
                            break
                        if self.isValidValue(v):
                            c += 1
                        continue # end of while(v)
                    if self.sweepRange[1] - v > delta:
                        if self.isValidValue(v):
                            c += 1
                else:
                    return 0
            else:
                for v in self.valList:
                    if self.isValidValue(v):
                        c += 1
            return c
        if self.type == Param.Type_BOOL:
            if self.useRange:
                return 2
            else:
                return 1
        if self.type == Param.Type_STRING:
            if self.valList == [] or self.valList[0] == '':
                return 0
            else:
                return 1
        return 0

    def parseXML(self, xnp, group=''):
        """
        XMLの<param>ノードのパース

        [in] xnp    <param>ノードのXMLデータ
        [in] group  <param>ノードが所属するパラメータグループ名
        戻り値 -> 真偽値
        """
        if not xnp.nodeType == xnp.ELEMENT_NODE or \
                not xnp.tagName == 'param':
            return False
        
        if not xnp.hasAttribute('name') or not xnp.hasAttribute('type'):
            log.error(LogMsg(42, '<param> tag without name nor type '
                             + 'attribute found, ignored'))
            return True

        if xnp.hasAttribute('disable'):
            val = xnp.getAttribute('disable').lower()
            if val in ['true', 'yes']:
                self.disable = True
                self.disable_gui = True
            elif val in ['false', 'no']:
                self.disable = False
                self.disable_gui = False

        p = self
        p.group = group
        p.name = xnp.getAttribute('name')
        ltype = xnp.getAttribute('type')
        if ltype == 'int':
            p.type = Param.Type_INT
            p.arithPrec = 0
        elif ltype == 'real':
            p.type = Param.Type_REAL
            p.arithPrec = 6
        elif ltype == 'bool':
            p.type = Param.Type_BOOL
        elif ltype == 'string':
            p.type = Param.Type_STRING
        elif ltype == 'choice':
            p.type = Param.Type_CHOICE
        else:
            log.error(LogMsg(43, '<param> tag with invalid type: %s' % ltype
                             + ', ignored'))
            return True

        for cur in xnp.childNodes:
            if cur.nodeType == cur.TEXT_NODE:
                p.desc = p.desc + conv_text(cur.data.strip())
                continue
            if cur.nodeType == cur.ELEMENT_NODE:
                if cur.tagName == 'item':
                    if p.type != Param.Type_CHOICE:
                        continue
                    if not cur.hasChildNodes():
                        continue
                    if cur.firstChild.nodeType != cur.TEXT_NODE:
                        continue
                    p.citems.append(conv_text(cur.firstChild.data.strip()))
                    continue
                if cur.tagName == 'minmax' or cur.tagName == 'range':
                    if p.type != Param.Type_INT and p.type != Param.Type_REAL:
                        continue
                    if cur.hasAttribute('min'):
                        val = cur.getAttribute('min')
                        if p.type == Param.Type_INT:
                            p.minmax[0] = int(val)
                        else:
                            p.minmax[0] = float(val)
                    if cur.hasAttribute('max'):
                        val = cur.getAttribute('max')
                        if p.type == Param.Type_INT:
                            p.minmax[1] = int(val)
                        else:
                            p.minmax[1] = float(val)
                    continue
                if cur.tagName == 'value':
                    if not cur.hasChildNodes():
                        continue
                    if cur.firstChild.nodeType != cur.TEXT_NODE:
                        continue
                    val = conv_text(cur.firstChild.data.strip())
                    try:
                        if p.type == Param.Type_INT or \
                           p.type == Param.Type_CHOICE:
                            vals = val.split()
                            p.valList = [0]*len(vals)
                            for i in range(len(vals)):
                                p.valList[i] = int(vals[i])
                            continue
                        if p.type == Param.Type_REAL:
                            vals = val.split()
                            p.valList = [0]*len(vals)
                            for i in range(len(vals)):
                                p.valList[i] = float(vals[i])
                            continue
                        if p.type == Param.Type_BOOL:
                            val = val.lower()
                            if val in ['true', 'yes']:
                                p.valList = [True]
                            elif val in ['false', 'no']:
                                p.valList = [False]
                            continue
                        if p.type == Param.Type_STRING:
                            p.valList = [val]
                            continue
                    except Exception, e:
                        log.error(LogMsg(44, 'invalid <value> tag found'))
                        log.error(str(e))
                        continue
                    continue
                if cur.tagName == 'depend':
                    if not cur.hasAttribute('target'):
                        log.error(LogMsg(45, '<depend> tag without '
                                         + 'target attribute found, ignored'))
                        continue
                    targ = cur.getAttribute('target')
                    targ2 = None
                    if cur.hasAttribute('target2'):
                        targ2 = cur.getAttribute('target2')
                    for cur2 in cur.childNodes:
                        if cur2.nodeType != cur.ELEMENT_NODE:
                            continue
                        if cur2.tagName == 'cond':
                            if not self.parseCond(cur2, targ, targ2):
                                log.error(LogMsg(46, 'invalid <cond> tag found,'
                                                 + ' ignored'))
                                #return False
                            continue
                        continue
                    continue
                if cur.tagName == 'useRange':
                    if p.type == Param.Type_STRING:
                        continue
                    if not cur.hasChildNodes():
                        continue
                    if cur.firstChild.nodeType != cur.TEXT_NODE:
                        continue
                    val = conv_text(cur.firstChild.data.strip()).lower()
                    if val in ['true', 'yes']:
                        p.useRange = True
                    elif val in ['false', 'no']:
                        p.useRange = False
                    continue
                if cur.tagName == 'sweepRange':
                    if p.type != Param.Type_INT and \
                       p.type != Param.Type_REAL and \
                       p.type != Param.Type_CHOICE:
                        continue
                    if cur.hasAttribute('min'):
                        val = cur.getAttribute('min')
                        if p.type == Param.Type_INT or \
                           p.type == Param.Type_CHOICE:
                            p.sweepRange[0] = int(val)
                        else:
                            p.sweepRange[0] = float(val)
                    if cur.hasAttribute('max'):
                        val = cur.getAttribute('max')
                        if p.type == Param.Type_INT or \
                           p.type == Param.Type_CHOICE:
                            p.sweepRange[1] = int(val)
                        else:
                            p.sweepRange[1] = float(val)
                    if cur.hasAttribute('delta'):
                        val = cur.getAttribute('delta')
                        if p.type == Param.Type_INT or \
                           p.type == Param.Type_CHOICE:
                            p.sweepRange[2] = int(val)
                        else:
                            p.sweepRange[2] = float(val)
                    continue
                if cur.tagName == 'arithPrect':
                    if not cur.hasChildNodes():
                        continue
                    if cur.firstChild.nodeType != cur.TEXT_NODE:
                        continue
                    val = conv_text(cur.firstChild.data.strip())
                    if p.type == Param.Type_REAL:
                        vals = val.split()
                        try:
                            ndp = int(vals[0])
                            if ndp >= 0:
                                p.arithPrec = ndp
                        except:
                            pass
                    continue
                if cur.tagName == 'useExcept':
                    if p.type != Param.Type_INT and \
                       p.type != Param.Type_REAL and \
                       p.type != Param.Type_CHOICE:
                        continue
                    if not cur.hasChildNodes():
                        continue
                    if cur.firstChild.nodeType != cur.TEXT_NODE:
                        continue
                    val = conv_text(cur.firstChild.data.strip()).lower()
                    if val in ['true', 'yes']:
                        p.useExcept = True
                    elif val in ['false', 'no']:
                        p.useExcept = False
                    continue
                if cur.tagName == 'except':
                    if p.type != Param.Type_INT and \
                       p.type != Param.Type_REAL and \
                       p.type != Param.Type_CHOICE:
                        continue
                    self.useExceptList = True
                    if not cur.hasChildNodes():
                        continue
                    if cur.firstChild.nodeType != cur.TEXT_NODE:
                        continue
                    val = conv_text(cur.firstChild.data.strip())
                    try:
                        if p.type == Param.Type_INT or \
                           p.type == Param.Type_CHOICE:
                            vals = val.split()
                            p.excepts = [0]*len(vals)
                            for i in range(len(vals)):
                                p.excepts[i] = int(vals[i])
                            continue
                        if p.type == Param.Type_REAL:
                            vals = val.split()
                            p.excepts = [0]*len(vals)
                            for i in range(len(vals)):
                                p.excepts[i] = float(vals[i])
                            continue
                    except Exception, e:
                        log.error(LogMsg(47, 'invalid <except> tag found'))
                        log.error(str(e))
                        continue
                    continue
                if cur.tagName == 'exceptRange':
                    self.useExceptList = False
                    if p.type != Param.Type_INT and \
                       p.type != Param.Type_REAL and \
                       p.type != Param.Type_CHOICE:
                        continue
                    if cur.hasAttribute('min'):
                        val = cur.getAttribute('min')
                        if p.type == Param.Type_INT or \
                           p.type == Param.Type_CHOICE:
                            p.exceptRange[0] = int(val)
                        else:
                            p.exceptRange[0] = float(val)
                    if cur.hasAttribute('max'):
                        val = cur.getAttribute('max')
                        if p.type == Param.Type_INT or \
                           p.type == Param.Type_CHOICE:
                            p.exceptRange[1] = int(val)
                        else:
                            p.exceptRange[1] = float(val)
                    continue
                continue # end of ELEMENT node
            continue # end of for(cur)

        return True

    def parseCond(self, xnp, target, target2=None):
        """
        XMLの<cond>ノードのパース

        [in] xnp     <cond>ノードのXMLデータ
        [in] target  <cond>ノードの親の<depend>ノードのtarget属性値
        [in] target2 <cond>ノードの親の<depend>ノードのtarget2属性値
        戻り値 -> 真偽値
        """
        if not xnp.nodeType == xnp.ELEMENT_NODE or \
                not xnp.tagName == 'cond':
            return False

        # create cond class object
        c = Cond()

        # parse <cond> node
        if not c.parseXML(xnp, self, target, target2):
            return False

        self.depend_cond = c
        return True

    def outputXML(self, ofp, ofst=0):
        """
        XMLの<param>ノードの出力

        [in] ofp  出力先ファイル
        [in] ofst  オフセット量
        戻り値 -> 真偽値
        """
        ofs = ' ' * ofst
        ofs2 = ' ' * (ofst+2)
        ofs4 = ' ' * (ofst+4)

        if self.type == Param.Type_INT:
            ts = 'int'
        elif self.type == Param.Type_REAL:
            ts = 'real'
        elif self.type == Param.Type_BOOL:
            ts = 'bool'
        elif self.type == Param.Type_STRING:
            ts = 'string'
        elif self.type == Param.Type_CHOICE:
            ts = 'choice'
        else:
            return False

        try:
            if self.disable and self.disable_gui:
                ofp.write(ofs + '<param name="%s" type="%s" disable="yes">\n' \
                              % (self.name, ts))
            else:
                ofp.write(ofs + '<param name="%s" type="%s">\n' \
                              % (self.name, ts))
        except:
            return False

        # description
        if self.desc != '':
            ofp.write(ofs2 + self.desc + '\n')

        # minmax
        if self.type == Param.Type_INT or self.type == Param.Type_REAL:
            if self.minmax[0] != None or self.minmax[1] != None:
                ofp.write(ofs2 + '<range')
                if self.minmax[0] != None:
                    ofp.write(' min="%s"' % str(self.minmax[0]))
                if self.minmax[1] != None:
                    ofp.write(' max="%s"' % str(self.minmax[1]))
                ofp.write('/>\n')

        # citems
        if self.type == Param.Type_CHOICE:
            for item in self.citems:
                ofp.write(ofs2 + '<item>%s</item>\n' % item)

        # valList
        if self.type == Param.Type_BOOL or self.type == Param.Type_STRING:
            if self.valList != []:
                ofp.write(ofs2 + '<value>%s</value>\n' % str(self.valList[0]))
            else:
                ofp.write(ofs2 + '<value></value>\n')
        elif len(self.valList) > 0:
            ofp.write(ofs2 + '<value>\n')
            for v in self.valList:
                ofp.write(ofs4 + str(v) + '\n')
            ofp.write(ofs2 + '</value>\n')

        # useRange
        if self.type != Param.Type_STRING:
            ofp.write(ofs2 + '<useRange>%s</useRange>\n' % str(self.useRange))

        # sweepRange
        if self.type == Param.Type_INT or self.type == Param.Type_REAL or \
           self.type == Param.Type_CHOICE:
            if self.sweepRange[0] != None or self.sweepRange[1] != None or \
                    self.sweepRange[2] != None:
                ofp.write(ofs2 + '<sweepRange')
                if self.sweepRange[0] != None:
                    ofp.write(' min="%s"' % str(self.sweepRange[0]))
                if self.sweepRange[1] != None:
                    ofp.write(' max="%s"' % str(self.sweepRange[1]))
                if self.sweepRange[2] != None:
                    ofp.write(' delta="%s"' % str(self.sweepRange[2]))
                ofp.write('/>\n')

        # arithPrec
        if self.type == Param.Type_REAL and self.arithPrec != 6:
            ofp.write(ofs2 + '<arithPrec>%d</arithPrec>\n' % self.arithPrec)

        # useExcept
        if self.type == Param.Type_INT or self.type == Param.Type_REAL or \
           self.type == Param.Type_CHOICE:
            ofp.write(ofs2 + '<useExcept>%s</useExcept>\n' % \
                          str(self.useExcept))

        # except
        if self.type == Param.Type_INT or self.type == Param.Type_REAL or \
           self.type == Param.Type_CHOICE:
            if self.useExceptList and len(self.excepts) > 0:
                ofp.write(ofs2 + '<except>\n')
                for v in self.excepts:
                    ofp.write(ofs4 + str(v) + '\n')
                ofp.write(ofs2 + '</except>\n')
            elif self.exceptRange[0] != None or self.exceptRange[1] != None:
                ofp.write(ofs2 + '<exceptRange')
                if self.exceptRange[0] != None:
                    ofp.write(' min="%s"' % str(self.exceptRange[0]))
                if self.exceptRange[1] != None:
                    ofp.write(' max="%s"' % str(self.exceptRange[1]))
                ofp.write('/>\n')

        # depend_cond
        if self.depend_cond != None:
            ofp.write(ofs2 + '<depend target="%s"' % self.depend_cond.target)
            if self.depend_cond.target2:
                ofp.write(' target2="%s"' % self.depend_cond.target2)
            ofp.write('>\n')
            if not self.depend_cond.outputXML(ofp, ofst+4):
                return False
            ofp.write(ofs2 + '</depend>\n')

        ofp.write(ofs + '</param>\n')
        return True

#----------------------------------------------------------------------
# utils
def decompParamCL(pl, s):
    """
    コマンドライン指定のパラメータ記述形式の分解
      記述形式 ::= パラメータ名:値1[,値2,...]
              ::= パラメータ名:最小値/最大値/刻み幅
    [in] pl パラメータリスト
    [in] s  パラメータ記述文字列
    戻り値 -> 真偽値
    """
    if not s or len(s) < 3:
        raise Exception('invalid param argument: null')
    ss = s.strip()
    pname = ''
    toks = ss.split(':')
    if len(toks) < 2:
        raise Exception('invalid param argument: invalid format')
    pname = toks[0]
    param = None
    for p in pl:
        if p.name == pname:
            param = p
            break
        continue # end of for(p)
    if not param:
        raise Exception('invalid param argument: param named %s not exist' \
                            % pname)
    ss = toks[1]
    if param.type == Param.Type_STRING:
        param.valList = [ss,]
        return True
    elif param.type == Param.Type_BOOL:
        toks = ss.split(',')
        valList = []
        for val in toks:
            val = val.lower()
            if val in ['true', 'yes']:
                valList.append(True)
            elif val in ['false', 'no']:
                valList.append(False)
            else:
                raise Exception('invalid param argument: param %s is boolean' \
                                    % pname)
            continue # end of for(val)
        if True in valList and False in valList:
            param.useRange = True
        elif True in valList:
            param.valList = [True,]
            param.useRange = False
        elif False in valList:
            param.valList = [False,]
            param.useRange = False
        return True
    elif param.type == Param.Type_CHOICE:
        try:
            val = int(ss)
            if val < 0 or val >= len(param.citems):
                raise Exception()
            param.valList = [val,]
            return True
        except:
            if ss == 'ALL':
                param.useRange = True
            elif ss in param.citems:
                for i in range(len(param.citems)):
                    if ss == param.citems[i]:
                        param.valList = [i,]
                        param.useRange = False
                        return True
                    continue # end of for(i)
                raise Exception('invalid param argument: '
                                '%s not found in param %s items' % (ss, pname))
    else:
        sweepRange = [None, None, None]
        toks = ss.split('/')
        try:
            if len(toks) == 3:
                if param.type == Param.Type_INT or \
                   param.type == Param.Type_CHOICE:
                    sweepRange[0] = int(toks[0])
                    sweepRange[1] = int(toks[1])
                    sweepRange[2] = int(toks[2])
                else:
                    sweepRange[0] = float(toks[0])
                    sweepRange[1] = float(toks[1])
                    sweepRange[2] = float(toks[2])
                param.useRange = True
                param.sweepRange = sweepRange
                return True
            else:
                valList = []
                toks = ss.split(',')
                for t in toks:
                    if param.type == Param.Type_INT or \
                       param.type == Param.Type_CHOICE:
                        valList.append(int(t))
                    else:
                        valList.append(float(t))
                    continue # end of for(t)
                param.useRange = False
                param.valList = valList
                return True
        except:
            if param.type == Param.Type_CHOICE:
                if ss == 'ALL':
                    param.useRange = True
                elif ss in param.citems:
                    for i in range(len(param.citems)):
                        if ss == param.citems[i]:
                            param.valList = [i,]
                            param.useRange = False
                            return True
                        continue # end of for(i)
                raise Exception('invalid param argument: %s not found '
                                'in param %s items' % (ss, pname))
            else:
                raise Exception('invalid param argument: %s: %s' % (pname, ss))

    return True
