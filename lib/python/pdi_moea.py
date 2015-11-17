#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
MOEAインターフェース
"""

import sys, os
import shutil
import datetime
import random
import subprocess
import glob
try:
    import pdi_log
    log = pdi_log._log
    LogMsg = pdi_log.LogMsg
    from pdi_param import *
    from pdi_generate import GetBaseJobName, GetTemplBase
    from xml.dom import minidom
except Exception, e:
    sys.exit('PDI: ' + str(e))


class MOEA(object):
    """
    HPC/PF PDIサブシステムの、MOEA用のサーベイパラメータを保持する
    データクラスです。
    """
    def __init__(self):
        """
        初期化
        """
        self.population = 1
        self.maxGeneration = 1
        self.evaluator = ''
        self.optimizer = ''
        self.randSeed = -1.0 # random.random()
        self.crossoverRate = 0.9
        self.mutationRate = -1.0
        self.etaCrossover = 25
        self.etaMutation = 20
        self.history = True
        self.duplicate = True
        self.comm_path = ''

        self.setup_comm_path()
        return

    def setup_comm_path(self):
        mypath = os.path.abspath(sys.argv[0])
        if mypath.endswith('.exe'): # for py2exe
            mypath = os.path.dirname(mypath)
        mydir = os.path.dirname(mypath) # python
        mydir = os.path.dirname(mydir) # lib
        mydir = os.path.dirname(mydir)
        self.comm_path = os.path.join(mydir, 'bin')
        self.optimizer = os.path.join(self.comm_path, 'xpdi_moea_cheetah')
        return

    def parseXML(self, xnp):
        """
        XMLの<moea>ノードのパース

        [in] xnp     <moea>ノードのXMLデータ
        戻り値 -> 真偽値
        """
        if not xnp.nodeType == xnp.ELEMENT_NODE or \
                not xnp.tagName == 'moea':
            return False

        for cur in xnp.childNodes:
            if cur.nodeType != cur.ELEMENT_NODE: continue
            if cur.tagName == 'population':
                valStr = conv_text(cur.firstChild.data.strip())
                try:
                    val = int(valStr)
                except:
                    continue
                if val < 1:
                    continue
                self.population = val
                continue
            if cur.tagName == 'maxGeneration':
                valStr = conv_text(cur.firstChild.data.strip())
                try:
                    val = int(valStr)
                except:
                    continue
                if val < 1:
                    continue
                self.maxGeneration = val
                continue
            if cur.tagName == 'evaluator':
                valStr = conv_text(cur.firstChild.data.strip())
                self.evaluator = valStr
                continue
            if cur.tagName == 'optimizer':
                valStr = conv_text(cur.firstChild.data.strip())
                self.optimizer = valStr
                continue
            if cur.tagName == 'randSeed':
                valStr = conv_text(cur.firstChild.data.strip())
                try:
                    val = float(valStr)
                except:
                    continue
                if val < 0.0 or val > 1.0:
                    continue
                self.randSeed = val
                continue
            if cur.tagName == 'crossoverRate':
                valStr = conv_text(cur.firstChild.data.strip())
                try:
                    val = float(valStr)
                except:
                    continue
                if val < 0.0 or val > 1.0:
                    continue
                self.crossoverRate = val
                continue
            if cur.tagName == 'mutationRate':
                valStr = conv_text(cur.firstChild.data.strip())
                try:
                    val = float(valStr)
                except:
                    continue
                if val < 0.0 or val > 1.0:
                    continue
                self.mutationRate = val
                continue
            if cur.tagName == 'etaCrossover':
                valStr = conv_text(cur.firstChild.data.strip())
                try:
                    val = int(valStr)
                except:
                    continue
                if val < 5 or val > 40:
                    continue
                self.etaCrossover = val
                continue
            if cur.tagName == 'etaMutation':
                valStr = conv_text(cur.firstChild.data.strip())
                try:
                    val = int(valStr)
                except:
                    continue
                if val < 5 or val > 50:
                    continue
                self.etaMutation = val
                continue
            if cur.tagName == 'history':
                valStr = conv_text(cur.firstChild.data.strip()).lower()
                if valStr == 'true' or valStr == 'yes':
                    self.history = True
                elif valStr == 'false' or valStr == 'no':
                    self.history = False
                continue
            if cur.tagName == 'duplicate':
                valStr = conv_text(cur.firstChild.data.strip()).lower()
                if valStr == 'true' or valStr == 'yes':
                    self.duplicate = True
                elif valStr == 'false' or valStr == 'no':
                    self.duplicate = False
                continue
            continue # end of for(cur)

        return True

    def outputXML(self, ofp, ofst=0):
        """
        XMLの<moea>ノードの出力

        [in] ofp  出力先ファイル
        [in] ofst  オフセット量
        戻り値 -> 真偽値
        """
        ofs = ' ' * ofst
        ofs2 = ' ' * (ofst+2)

        try:
            ofp.write(ofs + '<moea>\n')
        except:
            return False

        ofp.write(ofs2 + '<population>%d</population>\n' % self.population)
        ofp.write(ofs2 + '<maxGeneration>%d</maxGeneration>\n' \
                      % self.maxGeneration)
        if self.evaluator != '':
            ofp.write(ofs2 + '<evaluator>%s</evaluator>\n' % self.evaluator)
        if self.optimizer != '':
            ofp.write(ofs2 + '<optimizer>%s</optimizer>\n' % self.optimizer)
        if not self.randSeed < 0.0:
            ofp.write(ofs2 + '<randSeed>%f</randSeed>\n' % self.randSeed)
        if self.crossoverRate != 0.9:
            ofp.write(ofs2 + '<crossoverRate>%f</crossoverRate>\n' \
                          % self.crossoverRate)
        if not self.mutationRate < 0.0:
            ofp.write(ofs2 + '<mutationRate>%f</mutationRate>\n' \
                          % self.mutationRate)
        if self.etaCrossover != 25:
            ofp.write(ofs2 + '<etaCrossover>%d</etaCrossover>\n' \
                          % self.etaCrossover)
        if self.etaMutation != 20:
            ofp.write(ofs2 + '<etaMutation>%d</etaMutation>\n' \
                          % self.etaMutation)
        ofp.write(ofs2 + '<history>%s</history>\n' % str(self.history))
        ofp.write(ofs2 + '<duplicate>%s</duplicate>\n' % str(self.duplicate))

        ofp.write(ofs + '</moea>\n')
        return True

    def getDesignVariableList(self, pd):
        """
        設計変数のリストを返す

        [in] pd  パラメータ記述データ
        戻り値 -> 設計変数のリスト
        """
        retLst = []
        if not pd:
            return retLst
        for p in pd.plist:
            if p.disable: continue
            if p.type != Param.Type_INT and p.type != Param.Type_REAL:
                continue
            if not p.useRange:
                continue
            if p.sweepRange[0] == None or p.sweepRange[1] == None:
                continue
            if p.sweepRange[0] >= p.sweepRange[1]:
                continue
            retLst.append(p)
            continue #end of for(p)
        return retLst

    def getDesignVariableNum(self, pd):
        """
        設計変数の個数の計算

        [in] pd  パラメータ記述データ
        戻り値 -> 設計変数の個数
        """
        return len(self.getDesignVariableList(pd))

    def prepareMoeaEnv(self, core, progress=None):
        """
        MOEA実行環境の準備

        [in] core  PDI Coreデータ
        [in] progress  Progressダイアログ
        """
        if not core or not core.pd:
            raise Exception('invalid PDI core')
        if core.moea.population < 1:
            raise Exception('invalid population: %d' % core.moea.population)

        (keepGoing, skip) = (True, False)

        # get design variables
        designVars = self.getDesignVariableList(core.pd)
        num_vars = len(designVars)
        if num_vars < 1:
            raise Exception('no design variable parameter specified.')

        # get nObjs, nCons
        if self.evaluator == '':
            raise Exception('no evaluator specified.')
        if progress:
            (keepGoing, skip) = \
                progress.Update(0, 'getting nObjs and nCons ...')
            if not keepGoing: return
        num_objs = 0
        try:
            evalPathLst = self.evaluator.split()
            if sys.platform == 'win32' or sys.platform == 'win64':
                evalPathLst[0] = evalPathLst[0].replace('/', '\\')
                if evalPathLst[0].endswith('ffvc_eval_2Dcyl'):
                    evalPathLst[0] += '.bat'
            else:
                evalPathLst[0] = evalPathLst[0].replace('\\', '/')
            proc = subprocess.Popen(evalPathLst[0:1] + ['-O'],
                                    stdout=subprocess.PIPE)
            res = proc.communicate()[0]
            num_objs = int(res)
        except Exception, e:
            raise Exception('invalid evaluator specified, '
                            + 'invalid nObjs returned.')
        num_cons = 0
        try:
            proc = subprocess.Popen(evalPathLst[0:1] + ['-C'],
                                    stdout=subprocess.PIPE)
            res = proc.communicate()[0]
            num_cons = int(res)
        except Exception, e:
            pass

        # interface dir
        #inter_dir = os.path.join(core.exec_dir, 'interface')
        if progress:
            (keepGoing, skip) = \
                progress.Update(0, 'creating interface dir ...')
            if not keepGoing: return
        inter_dir = 'interface'
        try:
            if os.path.exists(inter_dir):
                if os.path.isfile(inter_dir):
                    os.remove(inter_dir)
                    os.mkdir(inter_dir)
            else:
                os.mkdir(inter_dir)
        except Exception, e:
            raise Exception('can not prepare interface dir: %s' % inter_dir)

        # output dir
        #out_dir = os.path.join(core.exec_dir, 'moea_out')
        if progress:
            (keepGoing, skip) = \
                progress.Update(0, 'creating moea output dir ...')
            if not keepGoing: return
        out_dir = 'moea_out'
        try:
            if os.path.exists(out_dir):
                if os.path.isfile(out_dir):
                    os.remove(out_dir)
                    os.mkdir(out_dir)
            else:
                os.mkdir(out_dir)
        except Exception, e:
            raise Exception('can not prepare moea output dir: %s' % out_dir)

        # cfg dir
        #cfg_dir = os.path.join(core.exec_dir, 'cfg')
        if progress:
            (keepGoing, skip) = \
                progress.Update(0, 'creating config dir ...')
            if not keepGoing: return
        cfg_dir = 'cfg'
        try:
            if os.path.exists(cfg_dir):
                if os.path.isfile(cfg_dir):
                    os.remove(cfg_dir)
                    os.mkdir(cfg_dir)
            else:
                os.mkdir(cfg_dir)
        except Exception, e:
            raise Exception('can not prepare moea config dir: %s' % cfg_dir)

        # moea.cfg
        if progress:
            (keepGoing, skip) = \
                progress.Update(0, 'creating moea config file ...')
            if not keepGoing: return
        moea_cfg = os.path.join(cfg_dir, 'moea.cfg')
        try:
            ofp = open(moea_cfg, 'w')
        except Exception, e:
            raise Exception('can not create moea config file: %s' % moea_cfg)
        ofp.write('mop-cfg-file=cfg/mop.cfg\n')
        ofp.write('output-dir=./moea_out\n')
        ofp.close()

        # mop.cfg
        if progress:
            (keepGoing, skip) = \
                progress.Update(0, 'creating mop config file ...')
            if not keepGoing: return
        mop_cfg = os.path.join(cfg_dir, 'mop.cfg')
        try:
            ofp = open(mop_cfg, 'w')
        except Exception, e:
            raise Exception('can not create mop config file: %s' % mop_cfg)
        ofp.write('mopName=hpcpf_moea\n')
        ofp.write('nObjs=%d\n' % num_objs)
        ofp.write('nCons=%d\n' % num_cons)
        ofp.write('nVars=%d\n' % num_vars)
        ofp.write('\n')
        for v in designVars:
            ofp.write('lbound=%s\n' % str(v.sweepRange[0]))
            ofp.write('ubound=%s\n' % str(v.sweepRange[1]))
            ofp.write('digitsPrec=%d\n' % v.arithPrec)
            ofp.write('\n')
            continue # end of for(v)
        ofp.close()

        # get jobname
        job_base = GetBaseJobName(core.wdPattern)

        # file list in 'input_data'
        if progress:
            (keepGoing, skip) = \
                progress.Update(0, 'creating input data dir ...')
            if not keepGoing: return
        try:
            in_dat_files = os.listdir('input_data')
        except:
            in_dat_files = []

        # delete old subcase directories
        old_jd_lst = [os.path.basename(r) \
            for r in glob.glob(os.path.join(core.exec_dir, job_base) + '*')]
        if len(old_jd_lst):
            for d in old_jd_lst:
                shutil.rmtree(d, True)

        # create subcase directories [population]
        for i in range(core.moea.population):
            #wkdn = os.path.join(core.exec_dir, job_base + '_%d' % i)
            wkdn = job_base + '_%d' % i
            if progress:
                (keepGoing, skip) = \
                    progress.Update(i + 1, 'creating %s ...' % wkdn)
                if not keepGoing: break
            try:
                if os.path.exists(wkdn):
                    if os.path.isfile(wkdn):
                        os.remove(wkdn)
                        os.mkdir(wkdn)
                else:
                    os.mkdir(wkdn)
                # copy from input_data
                for idfn in in_dat_files:
                    srcname = os.path.join(os.path.join('input_data', idfn))
                    dstname = os.path.join(os.path.join(wkdn, idfn))
                    if os.path.isdir(srcname):
                        shutil.copytree(srcname, dstname)
                    else:
                        shutil.copy2(srcname, dstname)
            except Exception, e:
                raise Exception('can not create subcase dir: %s' % wkdn)
            continue # end of for(i)

        # done
        return

    def GenerateParams(self, core, path='pdi_generated.lua'):
        """
        MOEA用のジョブセット生成

        [in] core  PDI Coreデータ
        [in] path  スクリプトファイル名
        """
        if not core or not core.pd:
            raise Exception('invalid PDI core')
        if core.batch_mode and not core.batch_out_scr:
            return True # no need to create pdi_generated.lua
        if core.moea.population < 1:
            raise Exception('invalid population: %d' % core.moea.population)

        solver_comm = core.solver_comm
        if solver_comm == [] or solver_comm[0] == '':
            #comm = os.path.join('.', 'run.sh')
            comm = './' + 'run.sh'
        else:
            #comm = os.path.join('.', solver_comm[0])
            comm = './' + solver_comm[0]
        comm_args = ''
        if len(solver_comm) > 1:
            for x in solver_comm[1:]:
                if x == solver_comm[1]:
                    comm_args += x
                else:
                    comm_args += ' '+x
                continue # end of for(x)
            if comm_args.find('%T') != -1:
                tmplBase = ''
                if len(core.templ_pathes) > 0:
                    tmplBase \
                        = GetTemplBase(os.path.basename(core.templ_pathes[0]))
                comm_args = comm_args.replace('%T', tmplBase)
        commStr = comm
        if comm_args != '':
            commStr += ' ' + comm_args

        job_base = GetBaseJobName(core.wdPattern)
        dt = str(datetime.datetime.today())
        try:
            ofp = open(path, 'w')
            ofp.write('-- created by PDI: %s --\n' % str(dt))
            ofp.write('\n')
        except Exception, e:
            raise e

        # define solver jobs
        ofp.write('function GET_JOBS(...)\n')
        ofp.write('local ex = ...\n')
        ofp.write('jobs = {}\n\n')
        for p in range(core.moea.population):
            jobnm = job_base + '_%d' % p
            ofp.write('%s = {\n' % jobnm)
            ofp.write('  name = \'' + jobnm + '\',\n')
            ofp.write('  path = \'' + jobnm + '\',\n')
            ofp.write('  job = \'' + commStr + '\',\n')
            ofp.write('  core = ex.cores,\n')
            ofp.write('  node = ex.nodes\n')
            ofp.write('}\n')
            ofp.write('jobs["%s"] = %s\n\n' % (jobnm, jobnm))
            continue # end of for(p)

        ofp.write('return jobs\n')
        ofp.write('end\n')
        
        # done
        ofp.close()
        return

    def CreateCWF(self, core, path='cwf.lua'):
        """
        MOEA用CWFの生成

        [in] core  PDI Coreデータ
        [in] path  CWFファイル名
        """
        if not core or not core.pd:
            raise Exception('invalid PDI core')
        if core.batch_mode and not core.batch_out_scr:
            return True # no need to create cwf.lua
        if core.moea.population < 1:
            raise Exception('invalid population: %d' % core.moea.population)

        dt = str(datetime.datetime.today())
        try:
            ofp = open(path, 'w')
            ofp.write('-- CWF created by PDI: %s --\n' % str(dt))
            ofp.write('--  need to be set LUA_PATH for hpcpf and dxjob.\n')
            ofp.write('\n')
        except Exception, e:
            raise e

        ofp.write('require("hpcpf")\n')
        ofp.write('\n')
        ofp.write('local ex = ...\n')
        ofp.write('local dxjob = require("dxjob")\n')
        ofp.write('local dj = dxjob.new(ex)\n')
        ofp.write('\n')
        ofp.write('require("pdi_generated")\n')
        ofp.write('jobs = GET_JOBS(ex)\n')
        ofp.write('\n')

        # LUA generation loop
        ofp.write('for i = 0, %d do\n' % core.moea.maxGeneration)
        ofp.write('  print(string.format("---- LOOP %d START ----", i))\n')

        # exec moea via optimizer in LUA
        optimPathLst = core.moea.optimizer.replace('\\', '/').split()
        if sys.platform == 'win32' or sys.platform == 'win64':
            if optimPathLst[0].endswith('xpdi_moea_cheetah'):
                optimPathLst[0] += '.bat'
        ofp.write('  local comm = "%s"\n' % ' '.join(optimPathLst))
        ofp.write('  comm = comm .. " -x " .. ex.caseDir\n')
        ofp.write('  comm = comm .. " -p %d"\n' % core.moea.population)
        ofp.write('  comm = comm .. string.format(" -c %d", i)\n')
        ofp.write('  comm = comm .. " -n %d"\n' % core.moea.maxGeneration)
        if not core.moea.history:
            ofp.write('  comm = comm .. " --nohistory"\n')
        if not core.moea.duplicate:
            ofp.write('  comm = comm .. " --noduplicate"\n')
        ofp.write('  print("EXEC: " .. comm)\n')
        ofp.write('  local ret = os.execute(comm)\n')
        ofp.write('  \n')

        # exec genparam for solver in LUA
        job_base = GetBaseJobName(core.wdPattern)
        genpPath = os.path.join(self.comm_path, 'xpdi_genparam').replace('\\', '/')
        if sys.platform == 'win32' or sys.platform == 'win64':
            genpPath += '.bat'
        ofp.write('  comm = "%s"\n' % genpPath)
        ofp.write('  comm = comm .. " -x " .. ex.caseDir\n')
        ofp.write('  comm = comm .. " -w %s"\n' % job_base)
        ofp.write('  comm = comm .. " -f %s"\n' % core.pfPattern)
        ofp.write('  comm = comm .. " -d %s"\n' % core.desc_path)
        for t in core.templ_pathes:
            ofp.write('  comm = comm .. " -t %s"\n' % t)
        designVars = self.getDesignVariableList(core.pd)
        for v in designVars:
            ofp.write('  comm = comm .. " -p %s"\n' % v.name)
        ofp.write('  print("EXEC: " .. comm)\n')
        ofp.write('  ret = os.execute(comm)\n')
        ofp.write('  \n')

        # exec solver in LUA
        ofp.write('  for k, j in pairs(jobs) do\n')
        ofp.write('    dj:AddJob(j)\n')
        ofp.write('  end\n')
        ofp.write('  \n')
        ofp.write('  dj:GenerateBootSh()\n')
        ofp.write('  dj:SendCaseDir()\n')
        ofp.write('  dj:SubmitAndWait()\n')
        ofp.write('  dj:GetCaseDir()\n')
        ofp.write('  dj:Cancel() -- clear jobque\n')
        ofp.write('  \n')

        # exec evaluator in LUA
        evalPathLst = core.moea.evaluator.replace('\\', '/').split()
        if sys.platform == 'win32' or sys.platform == 'win64':
            if evalPathLst[0].endswith('ffvc_eval_2Dcyl'):
                evalPathLst[0] += '.bat'
        ofp.write('  if i ~= %d then\n' % core.moea.maxGeneration)
        ofp.write('    comm = "%s"\n' % ' '.join(evalPathLst))
        ofp.write('    comm = comm .. " -x " .. ex.caseDir\n')
        ofp.write('    comm = comm .. " -w %s"\n' % job_base)
        ofp.write('    comm = comm .. " -p %d"\n' % core.moea.population)
        ofp.write('    print("EXEC: " .. comm)\n')
        ofp.write('    ret = os.execute(comm)\n')
        ofp.write('  end\n') # end of if

        ofp.write('  print(string.format("---- LOOP %d END ----", i))\n')
        ofp.write('end -- end of for(i)\n') # end of LUA for(i)

        ofp.write('\n')
        ofp.write('print(\'Case finished\')\n')
        ofp.write('return ex.outputFiles\n')

        # done
        ofp.close()
        return
