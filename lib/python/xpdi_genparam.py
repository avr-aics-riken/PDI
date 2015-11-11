#! /usr/bin/env python
# -*- coding: utf-8 -*-
u"""
xpdi_genparam.py
MOEA計算実行時にサブケース毎の入力パラメータファイルを生成する。
inter_dir/pop_vars_eval.txtとparam_tmplおよびparam_descから
各サブケースディレクトリ(wkd_base*)配下に入力パラメータファイル(param_fn)を
生成する。
入力パラメータファイルの生成には、PDIをバッチモードで使用する。
"""
import os, sys
import getopt
import glob
import random
import subprocess
try:
    from pdi_desc import *
    from pdi_param import *
    from pdi_tmpl import *
except:
    print '%s: import PDI module failed.' % sys.argv[0]
    sys.exit(-1)

mypath = os.path.abspath(sys.argv[0])
if mypath.endswith('.exe'): # for py2exe
    mypath = os.path.dirname(mypath)
mydir = os.path.dirname(mypath) # python
mydir = os.path.dirname(mydir) # lib
mydir = os.path.dirname(mydir)
pdi_comm = os.path.join(mydir, 'bin', 'pdi')
if sys.platform == 'win32' or sys.platform == 'win64':
    pdi_comm += '.bat'
try:
    pdi_comm = os.environ['PDI_COMMAND']
except:
    pass


def GetDirList(base, dir='.'):
    """
    ディレクトリのリスト(dir/base*)を返す

    [in] base  リストアップするディレクトリのベース名
    [in] dir  ターゲットディレクトリ
    戻り値 -> ディレクトリのリスト
    """
    arg = os.path.join(dir, base) + '*'
    lst = [os.path.basename(r) for r in glob.glob(arg)]
    dic = {}
    for l in lst:
        ll = l.split('_')
        try:
            x = int(ll[-1])
        except:
            x = int(random.random() * 10000)
        dic[x] = l
        continue # end of for(l)
    return dic.values()

def usage():
    print 'usage: %s [-h|--help] [-x casedir] [-w wkd_base] [-f paramfile]\n'\
        % os.path.basename(sys.argv[0]) \
        + '\t[-i interface_dir] -d descfile [-t templfile]+ ' \
        + '[-p param_name]+'
    return

# main routine
if __name__ == '__main__':
    case_dir = '.'
    wkd_base = 'job_'
    param_fn = '%T'
    inter_dir = 'interface'
    desc_path = None
    tmpl_pathes = []
    param_args = []

    myname = os.path.basename(sys.argv[0])
    # parse args
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hx:w:f:i:d:t:p:')
    except getopt.GetoptError, e:
        if '--help' in str(e):
            usage()
            sys.exit(0)
        print '%s: %s' % (myname, str(e))
        sys.exit(1)
    for o, p in opts:
        if o == '-h' or o == '--help':
            usage()
            sys.exit(0)
        if o == '-x':
            case_dir = p
            continue
        if o == '-w':
            wkd_base = p
            continue
        if o == '-f':
            param_fn = p
            continue
        if o == '-i':
            inter_dir = p
            continue
        if o == '-d':
            desc_path = p
            continue
        if o == '-t':
            tmpl_pathes.append(p)
            continue
        if o == '-p':
            param_args.append(p)
            continue
        continue # end of for(o,p)
    if desc_path == None:
        print '%s: no descfile specified.' % sys.argv[0]
        sys.exit(1)
    if len(tmpl_pathes) < 1:
        print '%s: no templfile specified.' % sys.argv[0]
        sys.exit(1)
    num_vars = len(param_args)
    if num_vars < 1:
        print '%s: no parameter specified.' % sys.argv[0]
        sys.exit(1)

    # load paramdesc file and check params
    descPath = os.path.join(case_dir, desc_path)
    try:
        pd = ParamDesc(descPath)
    except Exception, e:
        print '%s: descfile load failed: %s' % (sys.argv[0], descPath)
        sys.exit(2)
    for pn in param_args:
        param = pd.getParam(pn) 
        if param == None:
            print '%s: param named %s not exists.' % (sys.argv[0], pn)
            sys.exit(2)
        if param.type != Param.Type_INT and param.type != Param.Type_REAL:
            print '%s: type of param %s is not INT nor REAL.' % (sys.argv[0],pn)
            sys.exit(2)
        continue # end of for(pn)

    # subcase dir list
    subcase_lst = GetDirList(wkd_base, case_dir)
    population = len(subcase_lst)

    # open input file (pop_vars_eval.txt)
    ifn = os.path.join(case_dir, inter_dir, 'pop_vars_eval.txt')
    try:
        ifp = open(ifn, 'r')
    except Exception, e:
        print '%s: open failed: %s' % (myname, str(e))
        sys.exit(3)

    # read variables from input file
    vars_lst = [] # population x num_vars
    ln = 0
    for l in ifp:
        ln += 1
        if len(l) < 1: continue
        line = l.strip().split()
        if num_vars != len(line):
            print '%s: invalid design variable file(#of vars mismatch): %s:%d' \
                % (myname, ifn, ln)
            ifp.close()
            sys.exit(3)
        try:
            var_arr = [float(x) for x in line]
        except:
            print '%s: invalid line found in design variable file: %s:%d:' \
                % (myname, ifn, ln) + ' : ignore.'
            continue
        vars_lst.append(var_arr)
        continue # end of for(l)
    ifp.close()
    if population > len(vars_lst):
        print myname \
            + ': population in design variable file less than #of subcases'\
            + ' using %d' % len(vars_lst)
    elif population < len(vars_lst):
        print myname \
            + ': population in design variable file greater than #of subcases'
        sys.exit(3)

    # create paramfile(s)
    for idx in range(population):
        scd = subcase_lst[idx]
        comm = '%s -B -x %s -d %s' % (pdi_comm, case_dir, desc_path)
        # template file(s)
        for tf in tmpl_pathes:
            comm += ' -t %s' % tf
        # out_pattern
        out_pattern = os.path.join(scd, param_fn)
        comm += ' -o %s' % out_pattern
        # parameter list
        for i in range(num_vars):
            pval = vars_lst[idx][i]
            comm += ' -p %s:%s' % (param_args[i], str(pval))
        # DEBUG
        print '%s: info: exec pdi: %s' % (myname, comm)
        try:
            ret = subprocess.call(comm.split())
        except Exception, e:
            print '%s: pdi execution failed: %s' % (myname, str(e))
            sys.exit(4)            
        continue # end of for(idx)

    # done
    sys.exit(0)

