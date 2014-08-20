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
    from xml.dom import minidom
except Exception, e:
    sys.exit('PDI: ' + str(e))
try:
    import pdi_desc
except Exception, e:
    log.error(LogMsg(51, 'pdi_desc module import failed'))
    log.error(e)


#----------------------------------------------------------------------
# class Statement

class Statement(object):
    """
    Statementクラス
    パラメータ依存条件における真文または偽文を記述するクラスです。

    メンバ変数
      (enum)command  コマンド種別
      (void)set_value  SetValコマンドの設定値
      (void[2])set_minmax  SetMinmaxコマンドの設定値
    """

    (Com_Enable, Com_Disable, Com_SetVal, Com_SetMinmax, Com_SetSweep,
     Com_Pass) = range(6)

    def __init__(self):
        """
        初期化
        """
        self.command = Statement.Com_Pass
        self.set_value = 0
        self.set_minmax = [None, None]
        self.set_sweep = [None, None, None]
        return

    def __str__(self):
        """
        文字列化

        戻り値 -> 文字列
        """
        if self.command == Statement.Com_Enable:
            return 'enable'
        elif self.command == Statement.Com_Disable:
            return 'disable'
        elif self.command == Statement.Com_SetVal:
            return 'set val=%s' % str(self.set_value)
        elif self.command == Statement.Com_SetMinmax:
            return 'set minmax="%s,%s"' % \
                (str(self.set_minmax[0]), str(self.set_minmax[1]))
        elif self.command == Statement.Com_SetSweep:
            return 'set sweep="%s,%s,%s"' % \
                (str(self.set_sweep[0]),
                 str(self.set_sweep[1]), str(self.set_sweep[2]))
        return 'pass'


#----------------------------------------------------------------------
# class Cond

class Cond(object):
    """
    Condクラス
    パラメータ依存条件を記述するクラスです。
    パラメータ記述データファイルの<depend>および<cond>タグに対応します。

    メンバ変数
      (string)target       依存パラメータ名
      (enum)cond_op        依存条件判定演算子
      (string)cond_value   依存条件判定値
      (enum)cond_joinOp    依存条件との連結演算子
      (string)target2      依存パラメータ名2
      (enum)cond_op2       依存条件判定演算子2
      (string)cond_value2  依存条件判定値2
      (Statement)st_true   依存条件真文への参照
      (Statement)st_false  依存条件偽文への参照
    """

    (Op_EQ, Op_LT, Op_GT, Op_LE, Op_GE, Op_NE) = range(6)
    def GetCondOp(self, con_tok):
        if not con_tok: return None
        if   con_tok == '==': return Cond.Op_EQ
        elif con_tok == 'EQ': return Cond.Op_EQ
        elif con_tok == '<':  return Cond.Op_LT
        elif con_tok == 'LT': return Cond.Op_LT
        elif con_tok == '>':  return Cond.Op_GT
        elif con_tok == 'GT': return Cond.Op_GT
        elif con_tok == '<=': return Cond.Op_LE
        elif con_tok == 'LE': return Cond.Op_LE
        elif con_tok == '>=': return Cond.Op_GE
        elif con_tok == 'GE': return Cond.Op_GE
        elif con_tok == '!=': return Cond.Op_NE
        elif con_tok == 'NE': return Cond.Op_NE
        return None

    (Op_AND, Op_OR) = range(2)
    def GetCondOp2(self, con_tok):
        if not con_tok: return None
        if   con_tok == '&&':  return Cond.Op_AND
        elif con_tok == 'AND': return Cond.Op_AND
        elif con_tok == '||':  return Cond.Op_OR
        elif con_tok == 'OR':  return Cond.Op_OR
        return None


    def __init__(self):
        """
        初期化
        """
        self.target = None
        self.cond_op = Cond.Op_EQ
        self.cond_value = ''
        self.cond_joinOp = None
        self.target2 = None
        self.cond_op2 = Cond.Op_EQ
        self.cond_value2 = ''
        self.st_true = None
        self.st_false = None
        return

    def getCondValue(self, dcond =None):
        """
        依存条件判定値の取得

        [in] dcond  依存パラメータ
        戻り値 -> 依存条件判定値
        """
        if not dcond:
            return self.cond_value
        try:
            if dcond.type == pdi_desc.Param.Type_INT:
                return int(self.cond_value)
            elif dcond.type == pdi_desc.Param.Type_REAL:
                return float(self.cond_value)
            else:
                return str(self.cond_value)
        except:
            return self.cond_value

    def getCondValue2(self, dcond =None):
        """
        依存条件判定値2の取得

        [in] dcond  依存パラメータ
        戻り値 -> 依存条件判定値
        """
        if not dcond:
            return self.cond_value2
        try:
            if dcond.type == pdi_desc.Param.Type_INT:
                return int(self.cond_value2)
            elif dcond.type == pdi_desc.Param.Type_REAL:
                return float(self.cond_value2)
            else:
                return str(self.cond_value2)
        except:
            return self.cond_value2

    def judge(self, dcond =None, dcond2 =None):
        """
        依存条件判定

        [in] dcond  依存パラメータ
        [in] dcond2 依存パラメータ2
        戻り値 -> 真偽値
        """
        if not dcond:
            return False
        val1 = dcond.getValue()
        val2 = self.getCondValue(dcond)
        if self.cond_op == Cond.Op_EQ:
            ret1 = (val1 == val2)
        elif self.cond_op == Cond.Op_LT:
            ret1 = (val1 < val2)
        elif self.cond_op == Cond.Op_GT:
            ret1 = (val1 > val2)
        elif self.cond_op == Cond.Op_LE:
            ret1 = (val1 <= val2)
        elif self.cond_op == Cond.Op_GE:
            ret1 = (val1 <= val2)
        elif self.cond_op == Cond.Op_NE:
            ret1 = (val1 != val2)
        else:
            return False
        if dcond2 == None or self.cond_joinOp == None:
            return ret1
        val1 = dcond2.getValue()
        val2 = self.getCondValue2(dcond2)
        if self.cond_op2 == Cond.Op_EQ:
            ret2 = (val1 == val2)
        elif self.cond_op2 == Cond.Op_LT:
            ret2 = (val1 < val2)
        elif self.cond_op2 == Cond.Op_GT:
            ret2 = (val1 > val2)
        elif self.cond_op2 == Cond.Op_LE:
            ret2 = (val1 <= val2)
        elif self.cond_op2 == Cond.Op_GE:
            ret2 = (val1 <= val2)
        elif self.cond_op2 == Cond.Op_NE:
            ret2 = (val1 != val2)
        else:
            return ret1
        if self.cond_joinOp == Cond.Op_AND:
            return (ret1 and ret2)
        elif self.cond_joinOp == Cond.Op_OR:
            return (ret1 or ret2)
        return False

    def parseXML(self, xnp, param, target, target2=None):
        """
        XMLの<cond>ノードのパース

        [in] xnp     <cond>ノードのXMLデータ
        [in] param   <cond>ノードを含む<param>ノードのパラメータデータ
        [in] target  <cond>ノードの親の<depend>ノードのtarget属性値
        [in] target2 <cond>ノードの親の<depend>ノードのtarget2属性値
        戻り値 -> 真偽値
        """
        if not xnp.nodeType == xnp.ELEMENT_NODE or \
                not xnp.tagName == 'cond':
            return False
        if not param or not target:
            return False

        if not xnp.hasChildNodes():
            return False
        if xnp.firstChild.nodeType != xnp.TEXT_NODE:
            return False
        toks = xnp.firstChild.data.split('?')
        if len(toks) < 2:
            return False
        toks2 = toks[1].split(':')
        if len(toks2) < 2:
            return False
        con_str = toks[0]
        (tru_str, fal_str) = (toks2[0].strip(), toks2[1].strip())

        c = self
        c.target = target

        # decomp condition
        con_tok = con_str.split()
        if len(con_tok) < 3 or con_tok[0] != 'VAL':
            return False
        xop = self.GetCondOp(con_tok[1])
        if xop == None: return False
        c.cond_op = xop
        c.cond_value = con_tok[2]
        # optional condition
        if target2 and len(con_tok) > 6 and con_tok[4][:3] == 'VAL':
            xop2 = self.GetCondOp2(con_tok[3])
            xop = self.GetCondOp(con_tok[5])
            if xop != None and xop2 != None:
                c.cond_joinOp = xop2
                c.cond_op2 = xop
                c.cond_value2 = con_tok[6]
                c.target2 = target2

        # decomp statements
        c.st_true = Statement()
        if tru_str == 'enable':
            c.st_true.command = Statement.Com_Enable
        elif tru_str == 'disable':
            c.st_true.command = Statement.Com_Disable
        elif tru_str.startswith('set'):
            st_tok = tru_str.split('=')
            if len(st_tok) < 2:
                return False
            st_tok0 = st_tok[0].split()
            st_tok[1] = st_tok[1].strip('" \t').replace(',', ' ')
            st_tok1 = st_tok[1].split()
            if len(st_tok0) < 2:
                return False
            if st_tok0[1] == 'value':
                c.st_true.command = Statement.Com_SetVal
                c.st_true.set_value = st_tok[1]
            elif st_tok0[1] == 'minmax' or st_tok0[1] == 'range':
                if len(st_tok1) < 2:
                    return False
                c.st_true.command = Statement.Com_SetMinmax
                c.st_true.set_minmax[0] = st_tok1[0]
                c.st_true.set_minmax[1] = st_tok1[1]
            elif st_tok0[1] == 'sweep':
                if len(st_tok1) < 3:
                    return False
                c.st_true.command = Statement.Com_SetSweep
                c.st_true.set_sweep[0] = st_tok1[0]
                c.st_true.set_sweep[1] = st_tok1[1]
                c.st_true.set_sweep[2] = st_tok1[2]
        else:
            c.st_true.command = Statement.Com_Pass

        c.st_false = Statement()
        if fal_str == 'enable':
            c.st_false.command = Statement.Com_Enable
        elif fal_str == 'disable':
            c.st_false.command = Statement.Com_Disable
        elif fal_str.startswith('set'):
            st_tok = fal_str.split('=')
            if len(st_tok) < 2:
                return False
            st_tok0 = st_tok[0].split()
            st_tok1 = st_tok[1].split()
            if len(st_tok0) < 2:
                return False
            if st_tok0[1] == 'value':
                c.st_false.command = Statement.Com_SetVal
                c.st_false.set_value = st_tok[1]
            elif st_tok0[1] == 'minmax' or st_tok0[1] == 'range':
                if len(st_tok1) < 2:
                    return False
                c.st_false.command = Statement.Com_SetMinmax
                c.st_false.set_minmax[0] = st_tok1[0]
                c.st_false.set_minmax[1] = st_tok1[1]
            elif st_tok0[1] == 'sweep':
                if len(st_tok1) < 3:
                    return False
                c.st_false.command = Statement.Com_SetSweep
                c.st_false.set_sweep[0] = st_tok1[0]
                c.st_false.set_sweep[1] = st_tok1[1]
                c.st_false.set_sweep[2] = st_tok1[2]
        else:
            c.st_false.command = Statement.Com_Pass

        param.depend_cond = c
        return True

    def outputXML(self, ofp, ofst=0):
        """
        XMLの<cond>ノードの出力

        [in] ofp  出力先ファイル
        [in] ofst  オフセット量
        戻り値 -> 真偽値
        """
        ofs = ' ' * ofst
        try:
            ofp.write(ofs + '<cond>')
        except:
            return False

        # condition
        if self.cond_op == Cond.Op_EQ:
            ofp.write('VAL == %s ' % str(self.cond_value))
        elif self.cond_op == Cond.Op_LT:
            ofp.write('VAL < %s ' % str(self.cond_value))
        elif self.cond_op == Cond.Op_GT:
            ofp.write('VAL > %s ' % str(self.cond_value))
        elif self.cond_op == Cond.Op_LE:
            ofp.write('VAL <= %s ' % str(self.cond_value))
        elif self.cond_op == Cond.Op_GE:
            ofp.write('VAL <= %s ' % str(self.cond_value))
        elif self.cond_op == Cond.Op_NE:
            ofp.write('VAL != %s ' % str(self.cond_value))
        else:
            return False
        # optional condition
        if self.cond_joinOp != None:
            if self.cond_joinOp == Cond.Op_AND:
                ofp.write('AND ')
            elif self.cond_joinOp == Cond.Op_OR:
                ofp.write('OR ')
            else:
                return False
            if self.cond_op2 == Cond.Op_EQ:
                ofp.write('VAL2 == %s ' % str(self.cond_value2))
            elif self.cond_op2 == Cond.Op_LT:
                ofp.write('VAL2 < %s ' % str(self.cond_value2))
            elif self.cond_op2 == Cond.Op_GT:
                ofp.write('VAL2 > %s ' % str(self.cond_value2))
            elif self.cond_op2 == Cond.Op_LE:
                ofp.write('VAL2 <= %s ' % str(self.cond_value2))
            elif self.cond_op2 == Cond.Op_GE:
                ofp.write('VAL2 <= %s ' % str(self.cond_value2))
            elif self.cond_op2 == Cond.Op_NE:
                ofp.write('VAL2 != %s ' % str(self.cond_value2))
            else:
                return False

        ofp.write('? ')

        # true statement
        if self.st_true:
            ofp.write('%s ' % str(self.st_true))
        else:
            ofp.write('pass ')

        ofp.write(': ')

        # false statement
        if self.st_false:
            ofp.write('%s' % str(self.st_false))
        else:
            ofp.write('pass')

        ofp.write('</cond>\n')
        return True
