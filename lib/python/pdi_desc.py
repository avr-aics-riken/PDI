#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
パラメータ記述データ
"""

import sys, os
import codecs
try:
    import pdi_log
    log = pdi_log._log
    LogMsg = pdi_log.LogMsg
    from pdi_param import *
    from pdi_cond import *
    from xml.dom import minidom
except Exception, e:
    sys.exit('PDI: ' + str(e))

#----------------------------------------------------------------------
# class

class ParamDesc(object):
    """
    ParamDescクラス
    パラメータ記述データファイルの内容を表現するクラスです。

    メンバ変数
      (string)path    パラメータ記述データファイルのパス
      (Param[])plist  パラメータ記述データのリスト
    """
    def __init__(self, path=None):
        """
        初期化

        [in] path  パラメータ記述データファイルのパス(指定されればロードする)
        """
        self.path = ''
        self.plist = []
        if path:
            if not self.load(path):
                self.path = ''
                self.plist = []
                return
        return

    def __str__(self):
        """
        値の文字列化

        戻り値 -> 文字列
        """
        ret = str(self.__class__) + '(path=' + self.path + \
            ', #plist=%d)' % len(self.plist)
        for p in self.plist:
            ret = ret + '\n %s' % str(p)
        return ret

    def getParam(self, name):
        """
        パラメータ検索

        [in] name  検索するパラメータ名
        戻り値 -> パラメータ
        """
        if not name:
            return None
        for p in self.plist:
            if p.name == name:
                return p
        return None

    def getGroupList(self):
        """
        グループリスト取得

        戻り値 -> グループリスト
        """
        grpList = []
        for p in self.plist:
            if not p.group == '' and not p.group in grpList:
                grpList += [p.group,]
            continue
        return grpList

    def load(self, path):
        """
        パラメータ記述ファイルのロード

        [in] path  ロードするパラメータ記述データファイルのパス
        戻り値 -> 真偽値
        """
        # initialize
        self.path = ''
        self.plist = []

        # parse XML
        try:
            xdom = minidom.parse(path)
            xnp = xdom.documentElement
            if xnp.tagName != 'hpcpf_paramdesc':
                log.error(LogMsg(41, 'no <hpcpf_paramdesc> tag in '
                                 + 'param description file: ' + path))
                return False
        except Exception, e:
            log.error(LogMsg(40, 'can not open param description file: %s' \
                                 % path))
            log.error(str(e))
            return False

        # parse XML tree
        for cur in xnp.childNodes:
            if cur.nodeType != cur.ELEMENT_NODE: continue
            if cur.tagName == 'group':
                if not self.parseGroup(cur):
                    return False
                continue
            if cur.tagName == 'param':
                if not self.parseParam(cur):
                    return False
                continue
            continue

        # check depend_cond
        for p in self.plist:
            if not p.depend_cond or not p.depend_cond.target:
                continue
            targParam = self.getParam(p.depend_cond.target)
            if not targParam:
                p.depend_cond = None
                continue
            targParam.cascadeParams.append(p)
            targParam2 = self.getParam(p.depend_cond.target2)
            if targParam2:
                targParam2.cascadeParams.append(p)
            if not p.checkDepCond(self):
                p.depend_cond = None
                targParam.cascadeParams.remove(p)
                if targParam2:
                    targParam2.cascadeParams.remove(p)
            continue # end of for(p)

        self.path = path
        return True


    def parseGroup(self, xnp):
        """
        <group>ノードのパース

        [in] xnp  <group>ノードのXMLデータ
        戻り値 -> 真偽値
        """
        if not xnp.nodeType == xnp.ELEMENT_NODE or \
                not xnp.tagName == 'group':
            return False

        if not xnp.hasAttribute('name'):
            log.error(LogMsg(41, '<group> tag without name attribute found, '
                             + 'ignored'))
            return False
        cur_group = xnp.getAttribute('name')

        for cur in xnp.childNodes:
            if cur.nodeType != cur.ELEMENT_NODE: continue
            if cur.tagName == 'param':
                if not self.parseParam(cur, group=cur_group):
                    return False
                continue
            continue

        return True

    def parseParam(self, xnp, group=''):
        """
        <param>ノードのパース

        [in] xnp    <param>ノードのXMLデータ
        [in] group  <param>ノードが所属するパラメータグループ名
        戻り値 -> 真偽値
        """
        if not xnp.nodeType == xnp.ELEMENT_NODE or \
                not xnp.tagName == 'param':
            return False

        # create Param class object
        p = Param()

        # and, parse XML node
        if not p.parseXML(xnp, group):
            return False

        # add to param-list
        self.plist = self.plist + [p]
        return True

    def save(self, path=None):
        """
        パラメータ記述ファイルのセーブ

        [in] path  セーブするパラメータ記述データファイルのパス
        戻り値 -> 真偽値
        """
        xpath = path
        if not xpath: xpath = self.path
        if not xpath: return False
        try:
            ofp = codecs.open(xpath, 'w', 'utf-8')
        except Exception, e:
            log.error(LogMsg(50, 'can not open param description file: %s' \
                                 % path))
            log.error(str(e))
            return False
        #ofp.write('<hpcpf_paramdesc classification="snapshot">\n')
        ofp.write('<hpcpf_paramdesc>\n')

        grpList = self.getGroupList()
        for g in grpList:
            ofp.write('  <group name="%s">\n' % g)
            for p in self.plist:
                if p.group != g: continue
                p.outputXML(ofp, ofst=4)
                continue # end of for(p)
            ofp.write('  </group>\n')
            continue # end of for(g)

        for p in self.plist:
            if p.group != '': continue
            p.outputXML(ofp, ofst=2)
            continue # end of for(p)

        ofp.write('</hpcpf_paramdesc>\n')
        ofp.close()
        return True
