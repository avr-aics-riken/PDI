#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム

  コマンドライン
   pdi.py [-h|--help] [-v] [--no_all] [-b] [-x case_dir]
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
    -b
      バッチモードで動作
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

  参照ファイル
    $HPCPF_PREF_DIR/PDI.conf  プリファレンスファイル
    $HPCPF_HOME/conf/PDI_log.conf  ログ設定ファイル
"""

_version_ = '1.5 (201408)'


#----------------------------------------------------------------------
# imports system library
import sys, os
import getopt
import codecs
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
        self.no_all = False
        self.exec_dir = '.'
        self.desc_path = ''
        self.templ_pathes = []
        self.out_pattern = 'job%P/%T'
        self.pd = None

        self.wdNum = 1
        self.wdPattern = 'job%P'
        self.casesPerDir = 1
        self.pfPattern = '%T'
        self.enableSuspender = False
        self.generationLoop = False
        self.jobSuspender = ''
        self.maxGeneration = 1
        self.curGeneration = 0
        self.generator = ''
        self.sfPattern = ''

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
        ox = out_pat.split('/')
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
                    return True
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

        # increment curGeneration
        if snapshot:
            if self.generationLoop and self.batch_mode:
                self.curGeneration += 1
                log.info(LogMsg(0, 'curGeneration incremented: %d' \
                                    % self.curGeneration))
            else:
                self.curGeneration = 0
        else:
            self.desc_path = path
            log.info(LogMsg(0, 'loaded param_desc: %s' % self.desc_path))

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
                if cur.tagName == 'enableSuspender':
                    val = cur.firstChild.data.strip()
                    if val == 'True' or val == 'yes' or val == 'Yes':
                        self.enableSuspender = True
                    elif val == 'False' or val == 'no' or val == 'No':
                        self.enableSuspender = False
                    continue
                if cur.tagName == 'generationLoop':
                    val = cur.firstChild.data.strip()
                    if val == 'True' or val == 'yes' or val == 'Yes':
                        self.generationLoop = True
                    elif val == 'False' or val == 'no' or val == 'No':
                        self.generationLoop = False
                    continue
                if cur.tagName == 'jobSuspender':
                    self.jobSuspender = cur.firstChild.data.strip()
                    continue
                if cur.tagName == 'maxGeneration':
                    val = int(cur.firstChild.data.strip())
                    if val < 1:
                        self.maxGeneration = 1
                    else:
                        self.maxGeneration = val
                    continue
                if cur.tagName == 'curGeneration':
                    val = int(cur.firstChild.data.strip())
                    if val < 0:
                        self.curGeneration = 0
                    else:
                        self.curGeneration = val
                    continue
                if cur.tagName == 'generator':
                    self.generator = cur.firstChild.data.strip()
                    continue
                if cur.tagName == 'sfPattern':
                    self.sfPattern = cur.firstChild.data.strip()
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
        if self.desc_path != '':
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
        ofp.write('    <enableSuspender>%s</enableSuspender>\n' \
                      % str(self.enableSuspender))
        ofp.write('    <generationLoop>%s</generationLoop>\n' \
                      % str(self.generationLoop))
        if self.jobSuspender != '':
            ofp.write('    <jobSuspender>%s</jobSuspender>\n' \
                          % self.jobSuspender)
        ofp.write('    <maxGeneration>%d</maxGeneration>\n' \
                      % self.maxGeneration)
        ofp.write('    <curGeneration>%d</curGeneration>\n' \
                      % self.curGeneration)
        if self.generator != '':
            ofp.write('    <generator>%s</generator>\n' % self.generator)
        if self.sfPattern != '':
            ofp.write('    <sfPattern>%s</sfPattern>\n' % self.sfPattern)
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
        supported = ['FFB_LES3C_MPI', 'FFB_LES3C',
                     'FFB_LES3X_MPI', 'FFB_LES3X',
                     'FFV_C',
                     'OpenFOAM_icoFoam',
                     'HREMOP',
                     'none']
        if self.solver_type == st:
            return
        if st == 'none':
            self.solver_type = ''
            return
        stx = st.split('_')
        if stx[0] == '':
            raise Exception('no solver type specified')

        if stx[0] == 'FFB':
            if len(stx) < 2:
                stx.append('LES3C') # default is LES3C
            if stx[1] == 'LES3C':
                if len(stx) > 2 and stx[2] == 'MPI':
                    self.solver_comm = ['run_les3c_mpi.sh']
                else:
                    self.solver_comm = ['run_les3c.sh']
                self.pfPattern = 'PARMLES3C'
            elif stx[1] == 'LES3X':
                if len(stx) > 2 and stx[2] == 'MPI':
                    self.solver_comm = ['run_les3x_mpi.sh']
                else:
                    self.solver_comm = ['run_les3x.sh']
                self.pfPattern = 'PARMLES3X'
            else:
                #self.solver_comm = []
                raise Exception('unknown solver type specified: ' + st)
        elif stx[0] == 'FFV':
            self.solver_comm = ['run_ffv.sh', '%T']
            self.pfPattern = '%T'
        elif stx[0] == 'OpenFOAM':
            self.solver_comm = ['run_openfoam.sh']
            self.pfPattern = '%T'
        elif stx[0] == 'HREMOP':
            self.solver_comm = ['run_hremop.sh']
            self.pfPattern = '%T'
        else:
            #self.solver_comm = []
            raise Exception('unknown solver type specified: ' + st)
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
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvbx:d:t:o:p:',
                                   ['help', 'no_all'])
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
            continue
        if o == '--no_all':
            core.no_all = True
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
            if core.setOutputPattern(p):
                log.info(LogMsg(0, 'set out_pattern: %s' % p))
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

    # check .pdi_params
    if os.path.exists('.pdi_params'):
        mtime_snap = os.stat('.pdi_params').st_mtime
        mtime_desc = 0
        if core.desc_path != '':
            mtime_desc = os.stat(core.desc_path).st_mtime
        if mtime_desc > mtime_snap:
            log.warn(LogMsg(0, '%s is newer than %s/.pdi_params, ignore.\n'
                            % (core.desc_path, core.exec_dir)))
        else:
            try:
                if not core.loadXML('.pdi_params', snapshot=True):
                    raise Exception('load .pdi_params file failed')
            except Exception, e:
                log.warn(LogMsg(0, 'load %s/.pdi_params file failed\n'
                                % core.exec_dir))
                log.warn(str(e))

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
    if core.desc_path != '':
        try:
            if not core.saveXML('.pdi_params', snapshot=True):
                raise Exception('save .pdi_params file failed')
            log.info(LogMsg(0, 'snapshot-ed in %s/.pdi_params' % core.exec_dir))
        except Exception, e:
            log.warn(LogMsg(0, 'snapshot into %s/.pdi_params failed\n'
                            % core.exec_dir + str(e)))
    log.info(LogMsg(0, 'ended PDI'))
    sys.exit(0)
