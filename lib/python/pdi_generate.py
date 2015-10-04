#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC/PF PDIサブシステム
ソルバー入力ファイル生成機能
"""

import sys, os
import shutil
import datetime
from subprocess import check_call

try:
    import pdi_log
    log = pdi_log._log
    from pdi import *
    from pdi_desc import *
    from pdi_tmpl import *
except Exception, e:
    sys.exit(str(e))

def GetSweepParamList(core):
    """
    スイープパラメータ値リストの生成

    [in] core  PDIコアデータ
    戻り値 -> スイープパラメータ値リスト
    """
    if not core or not core.pd:
        return None
    spl = []
    for p in core.pd.plist:
        if not p.disable and p.calcCaseNum() > 1:
            spl.append(p)
        continue # end of for(p)
    return spl

def GetParamArray(sweepLst): 
    """
    パラメータスイープ組み合わせ配列の生成

    [in] sweepLst  スイープパラメータ値リスト
    戻り値 -> パラメータスイープ組み合わせ配列
    """
    sweepArr = [[]]
    for x in sweepLst:
        t = []
        for y in x:
            for i in sweepArr:
                t.append(i+[y])
        sweepArr = t
        continue # end of for(x)
    return sweepArr

def GetBaseJobName(wdPattern):
    wdname = wdPattern
    wdname = wdname.replace('#D', '')
    wdname = wdname.replace('#J', '')
    while wdname.find('%P') != -1:
        wdname = wdname.replace('%P', '')
    while wdname.find('%Q') != -1:
        wdname = wdname.replace('%Q', '')
    xwd = wdname.split('_', 1)
    job = xwd[0]
    if job == '': job = 'job'
    return job

def GetWkDirName(wdPattern, dn=0, scn=0, sc=[], spl=[]):
    """
    サブケースワークディレクトリ名の展開

    [in] wdPattern  ワークディレクトリ名パターン
    [in] dn  ワークディレクトリ通番
    [in] scn  サブケース通番
    [in] sc  サブケースのパラメータリスト
    [in] spl  スイープパラメータ値リスト
    戻り値 -> サブケースワークディレクトリ名
    """
    wdname = wdPattern
    if spl == []:
        import re
        wdname = wdname.replace('#D', '')
        wdname = wdname.replace('#J', '')
        wdname = wdname.replace('%P', '')
        wdname = wdname.replace('%Q', '')
        pat = re.compile('.+_[0-9]+')
        res = pat.search(wdname)
        if res and res.group() == wdname:
            pass
        else:
            wdname = wdname + '_0'
        return wdname
    wdname = wdname.replace('#D', '_'+str(dn))
    wdname = wdname.replace('#J', '_'+str(scn))
    while wdname.find('%P') != -1:
        pattern = ''
        for p in sc:
            pattern += '_'+str(p)
        wdname = wdname.replace('%P', pattern)
    while wdname.find('%Q') != -1:
        pattern = ''
        i = 0
        for p in sc:
            pattern += '_' + spl[i].name + str(p)
            i += 1
        wdname = wdname.replace('%Q', pattern)
    return wdname

def GetTemplBase(tmpl):
    """
    テンプレートファイルのベース名の取得

    [in] tmpl  テンプレートファイル名
    戻り値 -> テンプレートファイルのベース名
    """
    tmplBase = tmpl
    if tmplBase.endswith('.template'):
        tmplBase = tmplBase[:-9]
    if tmplBase.endswith('.tmpl'):
        tmplBase = tmplBase[:-5]
    if tmplBase.endswith('.tmp') or tmplBase.endswith('.tpl'):
        tmplBase = tmplBase[:-4]
    return tmplBase

def GetParamfileName(pfPattern, tmplBase, dn=0, scn=0, tn=0, cpdn=0):
    """
    パラメータファイル名の展開

    [in] pfPattern  パラメータファイル名パターン
    [in] tmplBase  テンプレートファイルベース名
    [in] dn  ワークディレクトリ通番
    [in] scn  サブケース通番
    [in] tn  テンプレートファイル番号
    [in] cpdn  単一ディレクトリ内サブケース番号
    戻り値 -> 真偽値
    """
    paramfile = pfPattern
    paramfile = paramfile.replace('%T', tmplBase)
    paramfile = paramfile.replace('#D', '_'+str(dn))
    paramfile = paramfile.replace('#J', '_'+str(scn))
    paramfile = paramfile.replace('#T', '_'+str(tn))
    paramfile = paramfile.replace('#S', '_'+str(cpdn))
    return paramfile

def CreateScriptFile(core, wdnl=[], path='pdi_generated.lua'):
    """
    ワークフロー用スクリプトファイル生成

    [in] core  PDIコアデータ
    [in] wdnl  ディレクトリ名リスト
    [in] path  スクリプトファイル名
    戻り値 -> 真偽値
    """
    if core == None: return False
    if core.batch_mode and not core.batch_out_scr:
        return True # no need to create scriptfile

    xpath = path

    # get job basename
    job = GetBaseJobName(core.wdPattern)

    # get solver command
    solver_comm = core.solver_comm
    if solver_comm == [] or solver_comm[0] == '':
        comm = 'run.sh'
    else:
        comm = solver_comm[0]

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
                tmplBase = GetTemplBase(os.path.basename(core.templ_pathes[0]))
            comm_args = comm_args.replace('%T', tmplBase)

    commStr = comm
    if comm_args != '':
        commStr += ' ' + comm_args

    dt = str(datetime.datetime.today())
    ts2 = '  '
    ts4 = '    '
    if wdnl == []:
        numSubCase = 1
    else:
        numSubCase = len(wdnl)

    try:
        ofp = open(xpath, "w")
        ofp.write('-- Parame sweep workflow created by PDI: %s --\n' % str(dt))
        ofp.write('--  need to be set LUA_PATH for hpcpf and dxjob.\n')
        ofp.write('\n')
    except Exception, e:
        log.error(LogMsg(210, 'create %s failed.' % xpath))
        log.error(str(e))
        return False

    ofp.write('require("hpcpf")\n')
    ofp.write('function EXEC_PARAMSWEEP(...)\n')
    ofp.write(ts2 + 'local pathsep = getSeparator()\n')
    ofp.write(ts2 + 'local dxjob = require("dxjob")\n')
    ofp.write(ts2 + 'local ex = ...\n')
    ofp.write(ts2 + 'local dj = dxjob.new(ex)\n')
    ofp.write('\n')

    # exec solver in LUA
    if wdnl == []:
        jobnm = job + '_0'
        ofp.write(ts2 + 'local ' + jobnm + ' = {\n')
        ofp.write(ts4 + 'name = \'' + jobnm + '\',\n')
        ofp.write(ts4 + 'path = \'' + jobnm + '\',\n')
        ofp.write(ts4 + 'job = \'' + commStr + '\',\n')
        ofp.write(ts4 + 'core = ex.cores,\n')
        ofp.write(ts4 + 'node = ex.nodes\n')
        ofp.write(ts2 + '}\n')
        ofp.write(ts2 + 'dj:AddJob(%s)\n' % jobnm)
        ofp.write('\n')
    else:
        for p in range(numSubCase):
            jobnm = job + '_%d' % p
            ofp.write(ts2 + 'local ' + jobnm + ' = {\n')
            ofp.write(ts4 + 'name = \'' + jobnm + '\',\n')
            ofp.write(ts4 + 'path = \'' + wdnl[p] + '\',\n')
            ofp.write(ts4 + 'job = \'' + commStr + '\',\n')
            ofp.write(ts4 + 'core = ex.cores,\n')
            ofp.write(ts4 + 'node = ex.nodes\n')
            ofp.write(ts2 + '}\n')
            ofp.write(ts2 + 'dj:AddJob(%s)\n' % jobnm)
            ofp.write('\n')
            continue # end of for(p)

    ofp.write(ts2 + 'dj:GenerateBootSh()\n')
    ofp.write(ts2 + 'dj:SendCaseDir()\n')
    ofp.write(ts2 + 'dj:SubmitAndWait()\n')
    ofp.write(ts2 + 'dj:GetCaseDir()\n')
    ofp.write('\n')
    ofp.write('end\n') # end of function EXEC_PARAMSWEEP(...)

    # done
    ofp.close()
    return True


CWF_LUA = """
require('hpcpf')

-- exec environment
local ex = ...
local caseDir = ex.caseDir
print('Case dir = ' .. caseDir)

-- pdi jobs
require('pdi_generated')
EXEC_PARAMSWEEP(ex)

print('Case finished')
return ex.outputFiles
"""

def CreateCWF(core, path='cwf.lua', force=False):
    """
    ケースワークフローファイルの生成

    [in] core  PDIコアデータ
    [in] path  ケースワークフローファイルのパス
    [in] force  存在する場合上書きするか
    戻り値 -> 真偽値
    """
    if not core:
        log.error(LogMsg(220, 'create CWF failed: invalid args'))
        return False
    if core.batch_mode and not core.batch_out_scr:
        return True # no need to create scriptfile

    if not force:
        if os.path.exists(path):
            return True

    dt = str(datetime.datetime.today())
    try:
        cwf = open(path, 'w')
        cwf.write('-- Case workflow created by PDI: %s --\n' % str(dt))
        cwf.write('--  need to be set LUA_PATH for hpcpf and dxjob.\n')
        cwf.write(CWF_LUA)
        cwf.close()
    except:
        log.error(LogMsg(221, 'create CWF failed: %s' % path))
        return False
    
    return True
    

def GenerateParams(core, progress=None, plcsv='param_list.csv'):
    """
    ソルバー入力ファイル生成

    [in] core  PDIコアデータ
    [in] progress  Progressダイアログ
    [in] plcsv  パラメータリストCSVファイルパス
    """
    if not core or not core.pd:
        raise Exception('invalid PDI core')
    caseNum = core.getTotalCaseNum()
    if caseNum < 1:
        raise Exception('total subcase number less than 1')
    spl = GetSweepParamList(core)

    plf = None
    if plcsv and plcsv != '':
        try:
            plf = open(plcsv, 'w')
            plf.write('%d, %d\n' % (0, core.moea.maxGeneration))
        except Exception, e:
            log.error(LogMsg(220, 'create %s failed.' % plcsv))
            raise

    exec_dir = os.path.basename(core.exec_dir)
    try:
        in_dat_files = os.listdir('input_data')
    except:
        in_dat_files = []

    (keepGoing, skip) = (True, False)

    if spl == []: # subcase number is 1, not sweep
        wdname = GetWkDirName(core.wdPattern)
        ### print 'mkdir: dirname='+wdname
        if progress:
            (keepGoing, skip) = \
                progress.Update(0, 'creating %s/...' % \
                                    os.path.join(exec_dir, wdname))
            if not keepGoing: return
        if not os.path.exists(wdname):
            try:
                os.makedirs(wdname)
                log.info(LogMsg(0, 'mkdir: ' + wdname))
            except Exception, e:
                log.error(LogMsg(201, 'create subcase dir failed: ' + wdname))
                raise e
        else:
            log.info(LogMsg(0, 'subcase dir exists: ' + wdname))
        for tf in core.templ_pathes:
            tmplBase = GetTemplBase(os.path.basename(tf))
            paramfile = GetParamfileName(core.pfPattern, tmplBase)
            ### print '  create paramfile='+paramPath
            paramPath = os.path.join(wdname, paramfile)
            if not ConvTmpl(tf, paramPath, core.pd):
                log.error(LogMsg(62, 'template conversion failed, '
                                 'template=%s, target=%s' % (tf, paramPath)))
            continue # end of for(tf)
        # copy input_data/* into wdname/
        for idfn in in_dat_files:
            srcname = os.path.join('input_data', idfn)
            dstname = os.path.join(wdname, idfn)
            if os.path.isdir(srcname):
                shutil.copytree(srcname, dstname)
            else:
                shutil.copy2(srcname, dstname)
        if progress:
            (keepGoing, skip) = \
                progress.Update(1, 'creating %s/... done.' % \
                                    os.path.join(exec_dir, wdname))
        # create script file in Lua
        CreateScriptFile(core)

        # output param_list.csv
        if plf:
            plf.write('0\n')
            plf.write('%s\n' % wdname)
            plf.close()
        return

    sweepLst = []
    for p in spl:
        pvl = p.generateValueList()
        sweepLst.append(pvl)
        continue # end of for(p)

    sweepArr = GetParamArray(sweepLst)
    if sweepArr == [[]]:
        raise Exception(u'パラメータスイープ組み合わせ配列の生成に失敗しました')

    if plf:
        plf.write('%d' % len(spl))
        for p in spl:
            plf.write(', %s' % p.name)
        plf.write('\n')

    # subcase directory loop
    wdnl = []
    dn = 0
    scn = 0
    # for sc in sweepArr:
    while scn < len(sweepArr):
        sc = sweepArr[scn]
        # create directory
        wdname = GetWkDirName(core.wdPattern, dn, scn, sc, spl)
        wdnl.append(wdname)
        ### print 'mkdir: dirname='+wdname
        if progress:
            (keepGoing, skip) = \
                progress.Update(dn, 'creating %s/...' % \
                                    os.path.join(exec_dir, wdname))
            if not keepGoing: break
        if not os.path.exists(wdname):
            try:
                os.makedirs(wdname)
                log.info(LogMsg(0, 'mkdir: ' + wdname))
            except Exception, e:
                log.error(LogMsg(201, 'create subcase dir failed: ' + wdname))
                continue
        else:
            log.info(LogMsg(0, 'subcase dir exists: ' + wdname))
        
        # in directory loop
        for cpdn in range(core.casesPerDir):
            tn = 0
            # template file loop
            for tf in core.templ_pathes:
                tmplBase = GetTemplBase(os.path.basename(tf))
                paramfile = GetParamfileName(core.pfPattern, tmplBase,
                                             dn, scn, tn, cpdn)
                ### print '  create paramfile='+paramfile
                paramPath = os.path.join(wdname, paramfile)
                xpl = {}
                for p, v in zip(spl, sc):
                    xpl[p.name] = v
                if not ConvTmpl(tf, paramPath, core.pd, xpl):
                    log.error(LogMsg(62, 'template conversion failed, '
                                     'template=%s, target=%s' % (tf,paramPath)))

                tn += 1
                continue # end of for(tf)

            # copy input_data/* into wdname/
            for idfn in in_dat_files:
                srcname = os.path.join(os.path.join('input_data', idfn))
                dstname = os.path.join(os.path.join(wdname, idfn))
                if os.path.isdir(srcname):
                    shutil.copytree(srcname, dstname)
                else:
                    shutil.copy2(srcname, dstname)

            # output param_list.csv
            if plf:
                plf.write(wdname)
                for p in sc:
                    plf.write(', %s' % str(p))
                plf.write('\n')

            scn += 1
            if scn >= len(sweepArr):
                break
            sc = sweepArr[scn]
            continue # end of for(cpdn)
        dn += 1
        if progress:
            (keepGoing, skip) = \
                progress.Update(dn, 'creating %s/... done.' % \
                                    os.path.join(exec_dir, wdname))
            if not keepGoing: break
        continue # end of while(scn)

    if plf: plf.close()

    # create script file in Lua
    CreateScriptFile(core, wdnl)

    # done
    return
