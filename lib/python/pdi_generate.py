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
        wdname = wdname.replace('#D', '')
        wdname = wdname.replace('#J', '')
        wdname = wdname.replace('%P', '')
        wdname = wdname.replace('%Q', '')
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

def CreateScriptFile(core, wdnl=[], path='paramsweep_wf', fmt='lua',
                     interval=5):
    """
    ワークフロー用スクリプトファイル生成

    [in] core  PDIコアデータ
    [in] wdnl  ディレクトリ名リスト
    [in] path  スクリプトファイル名
    [in] fmt   スクリプトファイル名拡張子
    [in] interval   スクリプトファイル中のジョブ終了チェック間隔(sec)
    戻り値 -> 真偽値
    """
    xpath = path
    if len(fmt) > 1: xpath += '.' + fmt
    if len(xpath) < 1:
        log.error(LogMsg(210, 'create script file failed: invalid args'))
        return False
    if not core:
        log.error(LogMsg(210, 'create script file failed: invalid args'))
        return False

    # get jobname
    wdname = core.wdPattern
    wdname = wdname.replace('#D', '')
    wdname = wdname.replace('#J', '')
    while wdname.find('%P') != -1:
        wdname = wdname.replace('%P', '')
    while wdname.find('%Q') != -1:
        wdname = wdname.replace('%Q', '')
    xwd = wdname.split('_', 1)
    job = xwd[0]
    if job == '': job = 'job'

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
    if wdnl == []:
        numSubCase = 1
    else:
        numSubCase = len(wdnl)

    try:
        ofp = open(xpath, "w")
        ofp.write('-- created by PDI: %s --\n' % str(dt))
        ofp.write('\n')
        ofp.write('-- listup jobs\n')
        ofp.write('jobs = {}\n')
        if wdnl == []:
            ofp.write('jobs[1] = {path = "%s_0", job = "%s"}\n' % \
                          (job, commStr))
        else:
            for case in range(numSubCase):
                ofp.write('jobs[%d] = {path = "%s", job = "%s"}\n' % \
                              (case+1, wdnl[case], commStr))
                continue # end of for(case)
        ofp.write('-- listup jobs end\n')
        ofp.close()
        os.chmod(xpath, 0744)
    except Exception, e:
        log.error(LogMsg(210, 'create %s failed.' % xpath))
        log.error(str(e))
        return False

    # register to CIF via PJM
    pjm_comm = ['pjm_set_file_in_case', '..', os.path.basename(os.getcwd()),
                'script_file', path, xpath,]
    try:
        pass ## check_call(pjm_comm)
    except Exception, e:
        log.error(LogMsg(220, 'add %s to CIF failed: call PJM failed' % xpath))
        log.error(str(e))

    # export generator/suspender path
    cwd = os.getcwd() # cwd == exec_dir
    if not core.generationLoop:
        try:
            os.remove('generator_prog')
        except:
            pass
    else:
        try:
            exf = open('generator_prog', 'w')
            xgp = core.generator
            if xgp.startswith(cwd): xgp = xgp[len(cwd)+1:]
            exf.write(xgp)
            exf.close()
        except:
            log.warn(LogMsg(0, 'export generator path to '
                            '%s/generator_prog failed' % core.exec_dir))

    if not core.enableSuspender:
        try:
            os.remove('job_suspender_prog')
        except:
            pass
    else:
        try:
            exf = open('job_suspender_prog', 'w')
            xsp = core.jobSuspender
            if xsp.startswith(cwd): xsp = xsp[len(cwd)+1:]
            exf.write(xsp)
            exf.close()
        except:
            log.warn(LogMsg(0, 'export job suspender path to '
                            '%s/job_suspender_prog failed' % core.exec_dir))
    return True

def AddParamsToCIF(core, fileId=None):
    """
    ケース情報ファイルへのパラメータファイル群の登録

    [in] core  PDIコアデータ
    [in] fileId  ファイルID(Noneの場合は世代番号を元に生成)
    戻り値 -> 真偽値
    """
    if not core:
        log.error(LogMsg(220, 'add param files to CIF failed: invalid args'))
        return False

    # get dir_base
    wdname = core.wdPattern
    wdname = wdname.replace('#D', '*')
    wdname = wdname.replace('#J', '*')
    wdname = wdname.replace('%P', '*')
    wdname = wdname.replace('%Q', '*')
    wdname = wdname.replace('**', '*')

    # get param_file
    pfname = core.pfPattern
    pfname = pfname.replace('%T', '*')
    pfname = pfname.replace('#D', '*')
    pfname = pfname.replace('#J', '*')
    pfname = pfname.replace('#T', '*')
    pfname = pfname.replace('#S', '*')
    pfname = pfname.replace('**', '*')

    # call PJM API
    comm = ['pjm_set_file_in_case', '..', os.path.basename(os.getcwd()),
            'param_file', ]
    if fileId != None:
        comm.append(fileId)
    else:
        comm.append('gen%d' % core.curGeneration)
    comm.append('%s/%s' % (wdname, pfname))
    try:
        pass ## check_call(comm)
    except Exception, e:
        log.error(LogMsg(220, 'add param files to CIF failed: call PJM failed'))
        log.error(str(e))
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
            plf.write('%d, %d\n' % (core.curGeneration, core.maxGeneration))
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
            ### print '  create paramfile='+paramfile
            paramPath = os.path.join(wdname, paramfile)
            if not ConvTmpl(tf, paramPath, core.pd):
                log.error(LogMsg(62, 'template conversion failed, '
                                 'template=%s, target=%s' % (tf, paramPath)))
            continue # end of for(tf)
        # copy input_data/* into wdname/
        for idfn in in_dat_files:
            srcname = os.path.join(os.path.join('input_data', idfn))
            dstname = os.path.join(os.path.join(wdname, idfn))
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

        # add param files to CIF
        AddParamsToCIF(core)

        # output param_list.csv
        if plf:
            plf.write('0\n')
            if core.sfPattern == '':
                scorefile = 'SCORE'
            else:
                scorefile = GetParamfileName(core.sfPattern, '')
            plf.write('%s\n' % os.path.join(wdname, scorefile))
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
                if core.sfPattern == '':
                    scorefile = 'SCORE'
                else:
                    scorefile = GetParamfileName(core.sfPattern, '',
                                                 dn, scn, tn, cpdn)
                plf.write(os.path.join(wdname, scorefile))
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

    # add param files to CIF
    AddParamsToCIF(core)

    # done
    return
