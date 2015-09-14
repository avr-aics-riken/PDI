#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
xpdi_moea_cheetah.py
MOEAモジュールとしてcheetahを実行するインターフェース。
"""
import os, sys
import getopt
import subprocess

moea_comm = 'cheetah.sh'
try:
    moea_comm = os.environ['MOEA_COMMAND']
except:
    pass


def usage():
    print 'usage: %s [-h|--help] [-x casedir] [-i interface_dir]\n' \
        % os.path.basename(sys.argv[0]) \
        + '\t -p population -c cur_gen -n max_gen [-m moea_comm]\n' \
        + '\t [--cfg-moea=moea_cfg] [--cfg-mop=mop_cfg] [-s rand_seed]\n' \
        + '\t [--nohistory] [--noduplicate]'
    return


# main routine
if __name__ == '__main__':
    case_dir = '.'
    inter_dir = 'interface'
    population = 0
    cur_gen = -1
    max_gen = 0
    moea_cfg = 'cfg/moea.cfg'
    mop_cfg = 'cfg/mop.cfg'
    rand_seed = -1.0
    nohist = False
    nodupl = False

    myname = os.path.basename(sys.argv[0])

    # parse args
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hx:i:p:c:n:s:m:',
                                   ['help', 'cfg-moea=', 'cfg-mop=',
                                    'nohistory', 'noduplicate'])
    except getopt.GetoptError, e:
        usage()
        sys.exit(1)
    for o, p in opts:
        if o == '-h' or o == '--help':
            usage()
            sys.exit(0)
        if o == '-x':
            case_dir = p
            continue
        if o == '-i':
            inter_dir = p
            continue
        if o == '-p':
            try:
                val = int(p)
            except:
                print '%s: invalid population specified: %s' % (myname, p) \
                    + ' ignore.'
                continue
            population = val
            continue
        if o == '-c':
            try:
                val = int(p)
            except:
                print '%s: invalid cur_gen specified: %s' % (myname, p) \
                    + ' ignore.'
                continue
            if val < 0:
                print '%s: invalid cur_gen specified: %d' % (myname, val) \
                    + ' ignore.'
                continue
            cur_gen = val
            continue
        if o == '-n':
            try:
                val = int(p)
            except:
                print '%s: invalid max_gen specified: %s' % (myname, p) \
                    + ' ignore.'
                continue
            if val < 0:
                print '%s: invalid max_gen specified: %d' % (myname, val) \
                    + ' ignore.'
                continue
            max_gen = val
            continue
        if o == '-m':
            moea_comm = val
            continue
        if o == '--cfg-moea':
            moea_cfg = val
            continue
        if o == '--cfg-mop':
            mop_cfg = val
            continue
        if o == '-s':
            try:
                val = float(p)
            except:
                print '%s: Invalid rand_seed specified: %s' % (myname, p) \
                    + ' ignore.'
                continue
            if val < 0.0 or val > 1.0:
                print '%s: invalid rand_seed specified: %f' % (myname, val) \
                    + ' ignore.'
                continue
            rand_seed = val
            continue
        if o == '--nohistory':
            nohist = True
            continue
        if o == '--duplicate':
            nodupl = True
            continue
        continue # end of for(o,p)

    if population < 1:
        print '%s: no population specified.' % myname
        sys.exit(2)
    if cur_gen < 0 or max_gen < 1 or cur_gen >= max_gen:
        print '%s: invalid generation specified.' % myname
        sys.exit(3)
    if rand_seed < 0.0:
        import random
        rand_seed = random.random()

    # chdir to case_dir
    if case_dir != '.':
        try:
            os.chdir(case_dir)
        except Exception, e:
            print '%s: can not chdir to %s' % (myname, case_dir)
            sys.exit(4)

    # exec moea
    TMPL_MOEA = '{moea_exe} --popsize={popSize} --inter-dir={inter_dir} ' \
        + '--ngen={maxGen} --currentGen={curGen} --seed={seed} ' \
        + '--cfg-file={moea_cfg} --mop-cfg-file={mop_cfg}'

    comm = TMPL_MOEA.format(moea_exe=moea_comm, popSize=population,
                            maxGen=max_gen, curGen=cur_gen,
                            moea_cfg=moea_cfg, mop_cfg=mop_cfg,
                            inter_dir=inter_dir, seed=rand_seed)
    if nohist:
        comm += ' --nohistory'
    if nodupl:
        comm += ' --noduplicate'
    print '%s: info: exec moea: %s' % (myname, comm)
    try:
        ret = subprocess.call(comm.split())
    except Exception, e:
        print '%s: command execution failed: %s' % (myname, str(e))
        sys.exit(5)

    # done
    sys.exit(0)
