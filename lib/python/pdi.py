#! /usr/bin/env python
# -*- coding: utf-8 -*-
u"""
HPC/PF PDIサブシステム

  コマンドライン
   pdi [-h|--help] [-v] [--no_all] [--no_cwf] [-b|-B] [-x case_dir]
       [-d descfile] [-t templfile [-t templfile ...]] [-o out_pattern]
       [-p param_name:param_value [-p param_name:param_value ...]]

    -h, --help
      ヘルプを表示して終了する。
    -v
      バージョン番号を表示して終了する。
    --no_all
      GUIモードにおいて「_All_」ページを作成しない。
      ただし、パラメータ記述ファイル中に<group>タグが一つも存在しない場合は
      作成する。
    --no_cwf
      パラメータ設定ファイル生成時にケースワークフロー(cwf.lua)を生成しない
    -b
      バッチモードで動作
    -B
      バッチモードで動作(Luaスクリプトファイルは生成しない)
    -x case_dir
      ケースディレクトリ指定
    -d descfile
      パラメータ記述ファイルを指定する
    -t templfile
      パラメータテンプレートファイルを指定する(複数指定可)
    -o out_pattern
      出力先ディレクトリ・ファイル名のパターン指定
    -p param_name:param_value
      パラメータ名・パラメータ値の直接指定(複数指定可)

  環境変数
    $HPCPF_HOME  HPC/PFインストールディレクトリ
    $HPCPF_PREF_DIR  プリファレンスディレクトリ(省略時は $HOME/.hpcpf/)
    $HPCPF_PDI_SNAPSHOT  スナップショットファイル名(省略時は'snap_params.pdi')

  参照ファイル
    $HPCPF_PREF_DIR/PDI.conf  プリファレンスファイル(JSON)
    $HPCPF_HOME/conf/PDI_log.conf  ログ設定ファイル
"""

_version_ = '1.4.6 (201601)'


#----------------------------------------------------------------------
# imports system library
import sys, os
import getopt
import codecs
import json
from xml.dom import minidom

#----------------------------------------------------------------------
# setup environments

try:
    home = os.environ['HOME']
except:
    home = None
if not home:
    try:
        home = os.environ['HOMEPATH']
    except:
        home = '.'
hpcpf_prefdir = os.path.join(home, '.hpcpf')
try:
    hpcpf_prefdir = os.environ['HPCPF_PREF_DIR']
except:
    pass
hpcpf_pref = os.path.join(hpcpf_prefdir, 'PDI.conf')

hpcpf_home = ''
hpcpf_conf_dir = ''
hpcpf_pref0 = ''
try:
    hpcpf_home = os.environ['HPCPF_HOME']
    hpcpf_conf_dir = os.path.join(hpcpf_home, 'conf')
    hpcpf_pref0 = os.path.join(hpcpf_conf_dir, 'PDI.conf')
except:
    pass
hpcpf_pref1 = ''
try:
    mypath = os.path.abspath(sys.argv[0]) # pdi.py
    if mypath.endswith('.exe'): # for py2exe
        mypath = os.path.dirname(mypath)
    mydir = os.path.dirname(mypath) # python
    mydir = os.path.dirname(mydir) # lib
    mydir = os.path.dirname(mydir)
    mydir = os.path.join(mydir, 'conf')
    hpcpf_pref1 = os.path.join(mydir, 'PDI.conf')
except:
    pass

cfg = None
try:
    cfg = json.loads(open(hpcpf_pref, 'r').read())
except:
    try:
        cfg = json.loads(open(hpcpf_pref0, 'r').read())
    except:
        try:
            cfg = json.loads(open(hpcpf_pref1, 'r').read())
        except:
            pass
if cfg == None:
    cfg = json.loads("""{
      "solver_cfg": {
        "none": [[], ""]
      }
    }""")


#----------------------------------------------------------------------
# setup snapshot filename
pdi_dotf = 'snap_params.pdi'
try:
    pdi_dotf_env = os.environ['HPCPF_PDI_SNAPSHOT']
    pdi_dotf = pdi_dotf_env
except:
    pass

#----------------------------------------------------------------------
# setup logging system
try:
    from pdi_log import *
    log = LogSetup(hpcpf_conf_dir)
    if not log:
        sys.exit('PDI: logging initialize failed, exit.')
except Exception, e:
    sys.exit('PDI: ' + str(e))

#----------------------------------------------------------------------
# imports pdi library
try:
    from pdi_desc import *
    from pdi_param import *
except Exception, e:
    log.error(LogMsg(51, 'pdi_desc/pdi_param module import failed'))
    log.error(e)
    sys.exit(51)
try:
    from pdi_tmpl import *
except Exception, e:
    log.error(LogMsg(61, 'pdi_tmpl module import failed'))
    log.error(e)
    sys.exit(61)
try:
    from pdi_moea import *
except Exception, e:
    log.error(LogMsg(61, 'pdi_moea module import failed'))
    log.error(e)
    sys.exit(71)


#----------------------------------------------------------------------
class Core:
    """
    HPC/PF PDIサブシステムの、設定パラメータおよびサーベイパラメータを
    保持するデータクラスです。
    """
    def __init__(self):
        """
        初期化
        """
        self.batch_mode = False
        self.batch_out_scr = True
        self.no_all = False
        self.no_cwf = False
        self.exec_dir = '.'
        self.desc_path = ''
        self.templ_pathes = []
        self.out_pattern = 'job%P/%T'
        self.pd = None

        self.wdNum = 1
        self.wdPattern = 'job%P'
        self.casesPerDir = 1
        self.pfPattern = '%T'

        self.moeaMode = False
        self.moea = MOEA()

        self.solver_type = ''
        self.solver_comm = []
        return

    def getTotalCaseNum(self):
        """
        パラメータケース数の計算

        戻り値 -> パラメータケース数
        """
        if not self.pd:
            return -1
        totalCaseNum = 1
        for p in self.pd.plist:
            if p.disable: continue
            c = p.calcCaseNum()
            totalCaseNum *= c
            continue #end of for(p)
        return totalCaseNum

    def adjustWdnAndCpd(self):
        """
        パラメータケース数に基づくwdNumとcasesPerDirの調整
        casesPerDirが優先

        戻り値 -> 真偽値.変更の有無.
        """
        changed = False
        cn = self.getTotalCaseNum()
        if self.casesPerDir <= 1:
            self.wdNum = 1
            self.casesPerDir = 1
            changed = True
        wdn = cn / self.casesPerDir
        if cn % self.casesPerDir > 0: wdn += 1
        if self.wdNum != wdn:
            self.wdNum = wdn
            changed = True
        return changed

    def setOutputPattern(self, out_pat):
        """
        ソルバ入力パラメータファイルの出力パターン設定
        work directory patternとparameter file patternに分解して設定する

        [in] out_pat  出力パターン
        戻り値 -> 真偽値
        """
        ox = out_pat.replace('\\', '/').split('/')
        if len(ox) == 2:
            if ox[1] == '':
                log.error(LogMsg(101, 'invalid out_pattern specified: '
                                 + out_pat))
                return False
            self.out_pattern = out_pat
            self.wdPattern = ox[0]
            self.pfPattern = ox[1]
        elif len(ox) == 1:
            if ox[0] == '':
                log.error(LogMsg(101, 'invalid out_pattern specified: '
                                 + out_pat))
                return False
            self.out_pattern = out_pat
            self.wdPattern = ''
            self.pfPattern = ox[0]
        else:
            log.error(LogMsg(101, 'invalid out_pattern specified: ' + out_pat))
            return False
        return True

    def setWdPattern(self, wd_pat):
        """
        ソルバ入力パラメータファイルの出力ディレクトリパターン設定

        [in] wd_pat  出力ディレクトリパターン
        戻り値 -> 真偽値
        """
        if wd_pat == self.wdPattern: return True
        self.wdPattern = wd_pat
        if self.wdPattern != '':
            self.out_pattern = self.wdPattern + '/' + self.pfPattern
        else:
            self.out_pattern = self.pfPattern
        return True

    def setPfPattern(self, pf_pat):
        """
        ソルバ入力パラメータファイルの出力ファイル名パターン設定

        [in] pf_pat  出力ファイル名パターン
        戻り値 -> 真偽値
        """
        if pf_pat == self.pfPattern: return True
        self.pfPattern = pf_pat
        if self.wdPattern != '':
            self.out_pattern = self.wdPattern + '/' + self.pfPattern
        else:
            self.out_pattern = self.pfPattern
        return True

    def setExecDir(self, path):
        """
        ケースディレクトリの設定.
        設定されるとカレントワーキングディレクトリを移動します.

        [in] path  ケースディレクトリパス
        戻り値 -> 真偽値
        """
        if self.exec_dir == path or path == '.':
            return True
        cwd0 = os.getcwd()
        try:
            os.chdir(path)
            self.exec_dir = os.getcwd()
            log.info(LogMsg(0, 'chdir to execution directory: '
                            + self.exec_dir))
        except Exception, e:
            log.error(LogMsg(20, 'can not chdir to execution directory: '
                                 + self.exec_dir))
            self.exec_dir = cwd0
            os.chdir(self.exec_dir)
            return False
        return True

    def loadXML(self, path, snapshot=False):
        """
        パラメータ記述ファイルのロード

        [in] path  ロードするパラメータ記述データファイルのパス
        [in] snapshot  スナップショットフラグ
        戻り値 -> 真偽値
        """
        pd_org = self.pd
        desc_path_org = self.desc_path
        try:
            xdom = minidom.parse(path)
            xnp = xdom.documentElement
            if xnp.tagName != 'hpcpf_paramdesc':
                log.error(LogMsg(41, 'no <hpcpf_paramdesc> tag in '
                                 + 'param description file: ' + path))
                return False
            if snapshot:
                attr = xnp.getAttribute('classification')
                if attr != 'snapshot':
                    log.warn(LogMsg(0, 'non snapshot <hpcpf_paramdesc> '
                                    + 'tag of param description file: ' + path))

            self.pd = ParamDesc()

            for cur in xnp.childNodes:
                if cur.nodeType != cur.ELEMENT_NODE: continue
                if cur.tagName == 'group':
                    if not self.pd.parseGroup(cur):
                        raise Exception('parse <group> node failed')
                    continue
                if cur.tagName == 'param':
                    if not self.pd.parseParam(cur):
                        raise Exception('parse <param> node failed')
                    continue
                if cur.tagName == 'survey':
                    if not self.parseSurvey(cur):
                        raise Exception('parse <survey> node failed')
                    continue
                if cur.tagName == 'snapshot':
                    if not self.parseSnapshot(cur):
                        raise Exception('parse <snapshot> node failed')
                    continue
                continue # end of for(cur)

            # check snapshot
            if snapshot:
                if desc_path_org == '':
                    log.info(LogMsg(0, 'snapshot %s is loaded without '
                                    'param desc file' % path))
                elif os.path.basename(desc_path_org) \
                        != os.path.basename(self.desc_path):
                    log.warn(LogMsg(0, 'snapshot %s is not based on loaded '
                                    'param desc file: %s, ignored.'
                                    % (path, self.desc_path)))
                    self.pd = pd_org
        except Exception, e:
            log.error(LogMsg(60, 'load param_desc XML failed'))
            log.error(str(e))
            self.pd = pd_org
            return False

        # check depend_cond
        for p in self.pd.plist:
            if not p.depend_cond or not p.depend_cond.target:
                continue
            targParam = self.pd.getParam(p.depend_cond.target)
            if not targParam:
                p.depend_cond = None
                continue
            targParam.cascadeParams.append(p)
            targParam2 = self.pd.getParam(p.depend_cond.target2)
            if targParam2:
                targParam2.cascadeParams.append(p)
            if not p.checkDepCond(self.pd):
                p.depend_cond = None
                targParam.cascadeParams.remove(p)
                if targParam2:
                    targParam2.cascadeParams.remove(p)
            continue # end of for(p)

        if not snapshot:
            self.desc_path = path
            log.info(LogMsg(0, 'loaded param_desc: %s' % self.desc_path))
        else:
            log.info(LogMsg(0, 'updated param_desc: %s' % path))

        return True

    def parseSurvey(self, xnp):
        """
        <survey>ノードのパース

        [in] xnp  <survey>ノードのXMLデータ
        戻り値 -> 真偽値
        """
        if not xnp.nodeType == xnp.ELEMENT_NODE or \
                not xnp.tagName == 'survey':
            return False
        try:
            for cur in xnp.childNodes:
                if not cur.hasChildNodes(): continue
                if cur.firstChild.nodeType != cur.TEXT_NODE: continue
                if cur.tagName == 'wdNum':
                    val = int(cur.firstChild.data.strip())
                    if val < 1:
                        self.wdNum = 1
                    else:
                        self.wdNum = val
                    continue
                if cur.tagName == 'wdPattern':
                    self.wdPattern = cur.firstChild.data.strip()
                    continue
                if cur.tagName == 'casesPerDir':
                    val = int(cur.firstChild.data.strip())
                    if val < 1:
                        self.casesPerDir = 1
                    else:
                        self.casesPerDir = val
                    continue
                if cur.tagName == 'pfPattern':
                    self.pfPattern = cur.firstChild.data.strip()
                    continue
                if cur.tagName == 'moeaMode':
                    val = cur.firstChild.data.strip().lower()
                    if val == 'true' or val == 'yes':
                        self.moeaMode = True
                    elif val == 'false' or val == 'no':
                        self.moeaMode = False
                    continue
                if cur.tagName == 'moea':
                    self.moea.parseXML(cur)
                    continue
                if cur.tagName == 'solver_type':
                    self.setupSolverHints(cur.firstChild.data.strip())
                    continue
                continue # end of for(cur)
        except Exception, e:
            log.error(LogMsg(62, 'parse <survey> tag error occured'))
            log.error(str(e))
            return False
        return True

    def parseSnapshot(self, xnp):
        """
        <snapshot>ノードのパース

        [in] xnp    <snapshot>ノードのXMLデータ
        戻り値 -> 真偽値
        """
        if not xnp.nodeType == xnp.ELEMENT_NODE or \
                not xnp.tagName == 'snapshot':
            return False
        self.desc_path = ''
        self.templ_pathes = []
        self.out_pattern = ''
        try:
            for cur in xnp.childNodes:
                if not cur.hasChildNodes(): continue
                if cur.firstChild.nodeType != cur.TEXT_NODE: continue
                if cur.tagName == 'desc_path':
                    self.desc_path = cur.firstChild.data.strip()
                    if not os.path.exists(self.desc_path):
                        log.warn(LogMsg(0, 'invalid desc_path specified: '
                                        'not exists: %s' % str(self.desc_path)))
                    continue
                if cur.tagName == 'templ_path':
                    val = cur.firstChild.data.strip()
                    if not val in self.templ_pathes:
                        if not os.path.exists(val):
                            log.error(LogMsg(22, 'invalid template file '
                                             'specified: %s' % str(val)))
                            continue
                        self.templ_pathes.append(val)
                    continue
                if cur.tagName == 'out_pattern':
                    #self.setOutputPattern(cur.firstChild.data.strip())
                    self.out_pattern = cur.firstChild.data.strip()
                    continue
                continue # end of for(cur)
        except Exception, e:
            log.error(LogMsg(63, 'parse <snapshot> tag error occured'))
            log.error(str(e))
            return False
        self.adjustWdnAndCpd()
        return True
  
    def saveXML(self, path, snapshot=False):
        """
        パラメータ記述ファイルのセーブ

        [in] path  セーブするパラメータ記述データファイルのパス
        戻り値 -> 真偽値
        """
        try:
            ofp = codecs.open(path, 'w', 'utf-8')
        except Exception, e:
            log.error(LogMsg(50, 'can not open param description file: %s' \
                                 % path))
            log.error(str(e))
            return False
        ofp.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        if snapshot:
            ofp.write('<hpcpf_paramdesc classification="snapshot">\n')
        else:
            ofp.write('<hpcpf_paramdesc>\n')

        grpList = self.pd.getGroupList()
        for g in grpList:
            ofp.write('  <group name="%s">\n' % g)
            for p in self.pd.plist:
                if p.group != g: continue
                p.outputXML(ofp, ofst=4)
                continue # end of for(p)
            ofp.write('  </group>\n')
            continue # end of for(g)

        for p in self.pd.plist:
            if p.group != '': continue
            p.outputXML(ofp, ofst=2)
            continue # end of for(p)

        cwd = os.getcwd() # cwd == exec_dir
        ofp.write('  <snapshot>\n')
        if self.desc_path != '' and not 'snap_params.pdi' in self.desc_path:
            xdp = self.desc_path
            if xdp.startswith(cwd):
                xdp = xdp[len(cwd)+1:]
            ofp.write('    <desc_path>%s</desc_path>\n' % xdp)
        for tp in self.templ_pathes:
            xtp = tp
            if xtp.startswith(cwd):
                xtp = xtp[len(cwd)+1:]
            ofp.write('    <templ_path>%s</templ_path>\n' % xtp)
        if self.out_pattern != '':
            ofp.write('    <out_pattern>%s</out_pattern>\n' % self.out_pattern)
        ofp.write('  </snapshot>\n')

        ofp.write('  <survey>\n')
        if self.wdNum != 1:
            ofp.write('    <wdNum>%d</wdNum>\n' % self.wdNum)
        if self.wdPattern != '':
            ofp.write('    <wdPattern>%s</wdPattern>\n' % self.wdPattern)
        if self.casesPerDir != 1:
            ofp.write('    <casesPerDir>%d</casesPerDir>\n' % self.casesPerDir)
        if self.pfPattern != '':
            ofp.write('    <pfPattern>%s</pfPattern>\n' % self.pfPattern)
        ofp.write('    <moeaMode>%s</moeaMode>\n' % str(self.moeaMode))
        self.moea.outputXML(ofp, 4)
        if self.solver_type != '':
            ofp.write('    <solver_type>%s</solver_type>\n' % self.solver_type)
        ofp.write('  </survey>\n')

        ofp.write('</hpcpf_paramdesc>\n')
        ofp.close()
        return True

    def setupSolverHints(self, st):
        """
        ソルバータイプ指定によるパラメータ設定

        [in]st    ソルバータイプ文字列
        """
        if self.solver_type == st:
            return
        if st == 'none':
            self.solver_type = ''
            return
        global cfg
        if cfg == None: return
        try:
            solver_cfg = cfg['solver_cfg']
            solver = solver_cfg[st]
            self.solver_comm = solver[0]
            self.pfPattern = solver[1]
        except:
            raise Exception('unknown solver type specified: ' + st)
            return

        self.solver_type = st
        return
       

#----------------------------------------------------------------------
# util functions
def usage():
    """
    usage文字列の出力
    """
    print __doc__
    return

def usage1():
    """
    help文字列の出力
    """
    print 'PDI ',
    version()
    print __doc__
    return

def version():
    """
    version文字列の出力
    """
    print 'version ' + _version_
    return


#----------------------------------------------------------------------
# main routine
if __name__ == '__main__':
    """
    PDIサブシステム メインルーチン

    """
    #log.setLevel(logging.DEBUG)
    log.info(LogMsg(0, 'starting PDI'))

    # prepare PDI core
    core = Core()

    # check arguments
    param_vals = []
    add_templs = []
    out_pat = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvbBx:d:t:o:p:',
                                   ['help', 'no_all', 'no-all',
                                    'no_cwf', 'no-cwf'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for o, p in opts:
        if o == '-h':
            usage()
            sys.exit(0)
        if o == '--help':
            usage1()
            sys.exit(0)
        if o == '-v':
            version()
            sys.exit(0)
        if o == '-b':
            core.batch_mode = True
            core.batch_out_scr = True
            continue
        if o == '-B':
            core.batch_mode = True
            core.batch_out_scr = False
        if o in ['--no_all', '--no-all']:
            core.no_all = True
            continue
        if o in ['--no_cwf', '--no-cwf']:
            core.no_cwf = True
            continue
        if o == '-x':
            if not os.path.exists(p):
                log.error(LogMsg(20, 'invalid execution directory specified: '
                                 + str(p)))
                continue
            if not core.setExecDir(p):
                continue
            continue
        if o == '-d':
            if not os.path.exists(p):
                log.error(LogMsg(21, 'invalid description file specified: '
                                 + str(p)))
                continue
            pl = os.path.split(p)
            if pl[0] == '':
                path = os.path.join(core.exec_dir, p)
            else:
                path = p
            core.desc_path = path
            continue
        if o == '-t':
            if not os.path.exists(p):
                log.error(LogMsg(22, 'invalid template file specified: %s' \
                                     % str(p)))
                continue
            pl = os.path.split(p)
            if pl[0] == '':
                path = os.path.join(core.exec_dir, p)
            else:
                path = p
            add_templs.append(path)
            log.info(LogMsg(0, 'add templ_path: %s' % path))
            continue
        if o == '-o':
            out_pat = p
            continue
        if o == '-p':
            param_vals.append(p)
            continue

    # load description
    if core.desc_path != '':
        try:
            pd_org = ParamDesc(core.desc_path)
        except Exception, e:
            log.error(LogMsg(52, 'load parameter description file failed: '
                             + core.desc_path + '\n' + str(e)))
            sys.exit(52)
        core.pd = pd_org
        log.info(LogMsg(0, 'loaded param_desc: %s' % core.desc_path))

    # check snapshot file
    if os.path.exists(pdi_dotf):
        mtime_snap = os.stat(pdi_dotf).st_mtime
        mtime_desc = 0
        if core.desc_path != '':
            mtime_desc = os.stat(core.desc_path).st_mtime
        if mtime_desc > mtime_snap:
            log.warn(LogMsg(0, '%s is newer than %s/%s, ignore snapshot.\n'
                            % (core.desc_path, core.exec_dir, pdi_dotf)))
        else:
            try:
                if not core.loadXML(pdi_dotf, snapshot=True):
                    raise Exception('load snapshot file failed: ' + pdi_dotf)
            except Exception, e:
                log.warn(LogMsg(0, 'load %s/%s file failed\n'
                                % (core.exec_dir, pdi_dotf)))
                log.warn(str(e))

    # set out_pattern
    if out_pat != None:
        if core.setOutputPattern(out_pat):
            log.info(LogMsg(0, 'set out_pattern: %s' % out_pat))

    # add templates
    for t in add_templs:
        core.templ_pathes.append(t)
        continue # end of for(t)

    # update param_vals
    for pv in param_vals:
        try:
            if not decompParamCL(core.pd.plist, pv):
                raise Exception('decomposition param_val arg: %s', pv)
        except Exception, e:
            log.warn(LogMsg(0, str(e)))
        continue # end of for(pv)

    # main process
    if not core.batch_mode:
        # launch GUI
        import pdi_guiApp
        app = pdi_guiApp.pdiApp()
        app.setCore(core)

        # role main loop
        app.MainLoop()

        # save snapshot
        if core.desc_path != '':
            try:
                if not core.saveXML(pdi_dotf, snapshot=True):
                    raise Exception('save snapshot file failed: ' + pdi_dotf)
                log.info(LogMsg(0, 'snapshot-ed in %s/%s'
                                % (core.exec_dir, pdi_dotf)))
            except Exception, e:
                log.warn(LogMsg(0, 'snapshot into %s/%s failed\n'
                                % (core.exec_dir, pdi_dotf) + str(e)))
    else:
        # batch mode, convert template
        if core.templ_pathes == []:
            log.error(LogMsg(63, 'no template specified in batch mode'))
            sys.exit(63)
        try:
            import pdi_generate
            pdi_generate.GenerateParams(core)
        except Exception, e:
            log.error(LogMsg(62, 'template conversion failed'))
            log.error(e)
            sys.exit(62)

    # epilogue
    log.info(LogMsg(0, 'ended PDI'))
    sys.exit(0)
