#! /usr/bin/env python
# -*- coding: utf-8 -*-
u"""
ffvc_eval_2Dcyl.py
FFVCの角柱周り流れ問題について、角柱2のForceの時間的最大値または平均値を得る。
各サブケースディレクトリ(wkd_base*)配下のhistory_forceファイル(history)を読み、
tm_range[0]〜tm_range[1]の時刻のF_xおよびF_yの絶対値の最大値(または平均)を求め、
inter_dir/pop_objs_eval.txtに出力する。
"""
import os,sys
import getopt
import glob
import random


myname = os.path.basename(sys.argv[0])

def GetMaxForce(hist, tm_range):
    """
    ヒストリーファイルからの力の絶対値の最大値を取得する。

    [in] hist  ヒストリーファイルのパス
    [in] tm_range  対象とする時間レンジ(開始、終了；Noneの場合は制限なし)
    戻り値 -> 力の絶対値の最大値(Fx, Fy)
    """
    if tm_range == None or type(tm_range) != list:
        tm_range = [None, None]

    # open history file
    try:
        ifp = open(hist, 'r')
    except Exception, e:
        print '%s: open failed: %s' % (myname, hist)
        return None

    # get max force
    data_found = False
    max_force = [0.0, 0.0]
    for l in ifp:
        if len(l) < 1: continue
        if l[0] == '#': continue
        if l.startswith('Column_Data'): continue
        line = l.strip().split()
        if len(line) < 4: continue
        try:
            tm = float(line[1])
        except:
            continue
        if tm_range[1] != None and tm > tm_range[1]: break
        elif tm_range[0] != None and tm < tm_range[0]: continue
        try:
            fx = abs(float(line[2]))
            fy = abs(float(line[3]))
        except Exception, e:
            data_found = False
            break
        if fx != fx or fy != fy: # nan check
            data_found = False
            break
        if max_force[0] < fx:
            max_force[0] = fx
        if max_force[1] < fy:
            max_force[1] = fy
        data_found = True
        continue # end of for(l)

    ifp.close()
    if not data_found:
        return None
    return max_force

def GetAveForce(hist, tm_range):
    """
    ヒストリーファイルからの力の絶対値の平均値を取得する。

    [in] hist  ヒストリーファイルのパス
    [in] tm_range  対象とする時間レンジ(開始、終了；Noneの場合は制限なし)
    戻り値 -> 力の絶対値の平均値(Fx, Fy)
    """
    if tm_range == None or type(tm_range) != list:
        tm_range = [None, None]

    # numpy
    try:
        import numpy as np
    except Exception, e:
        print str(e)
        return None

    # load history file by numpy
    try:
        dat = np.loadtxt(hist, skiprows=2)
    except Exception, e:
        print myname + ': load history file failed: ' + str(e)
        return None
    if True in np.isnan(dat):
        print myname + ': load history file: %s contains NaN' % hist
        return None

    # get average force
    if tm_range[0] != None:
        wkd1 = dat[np.where(dat[:, 1] >= tm_range[0])]
    else:
        wkd1 = dat
    if len(wkd1) > 0 and tm_range[1] != None:
        wkd2 = wkd1[np.where(wkd1[:, 1] <= tm_range[1])]
    else:
        wkd2 = wkd1
    if len(wkd2) < 1:
        print myname + ': load history file: %s contains no data in (%s, %s)' \
            % (hist, str(tm_range[0]), str(tm_range[1]))
        return None # no data exists

    ave_force = [0.0, 0.0]
    ave_force[0] = np.average(np.abs(wkd2[:, 2]))
    ave_force[1] = np.average(np.abs(wkd2[:, 3]))
    return ave_force

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
    print 'usage: %s [-h|--help] [-x casedir] [-w wkd_base] [-m]\n' % myname \
        + '\t [-t tm_start] [-T tm_end] [-i interface_dir] [-p population]\n' \
        + '\t [-O | -C]\n' \
        + '\t(tm_start, tm_end < 0.0 means unlimited)'
    return

# main routine
if __name__ == '__main__':
    case_dir = '.'
    wkd_base = 'job_'
    history_fn = 'history_force_cyl_2.txt'
    tm_range = [5.0, 10.0]
    inter_dir = 'interface'
    population = -1
    calc_max = False

    # parse args
    param_vals = []
    add_templs = []
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hx:w:mt:T:i:p:OC')
    except getopt.GetoptError, e:
        if '--help' in str(e):
            usage()
            sys.exit(0)
        print '%s: %s' % (sys.argv[0], str(e))
        sys.exit(1)
    for o, p in opts:
        if o == '-h':
            usage()
            sys.exit(0)
        if o == '-x':
            case_dir = p
            continue
        if o == '-w':
            wkd_base = p
            continue
        if o == '-m':
            calc_max = True
            continue
        if o == '-t':
            try:
                t = float(p)
            except:
                print '%s: invalid tm_start specified: %s, ignore' % (myname, p)
            if t < 0.0:
                tm_range[0] = None
            else:
                tm_range[0] = t
            continue
        if o == '-T':
            try:
                t = float(p)
            except:
                print '%s: invalid tm_end specified: %s' % (myname, p)
            if t < 0.0:
                tm_range[1] = None
            else:
                tm_range[1] = t
            continue
        if o == '-i':
            inter_dir = p
            continue
        if o == '-p':
            try:
                population = int(p)
            except:
                print '%s: invalid population specified: %s' % (myname, p)
            continue
        if o == '-O':
            print '2'
            sys.exit(0)
        if o == '-C':
            print '1'
            sys.exit(0)
        continue # end of for(o,p)
    if tm_range[0] != None and tm_range[1] != None and \
            tm_range[0] >= tm_range[1]:
        print '%s: invalid time range specified: %f, %f' % \
            (myname, tm_range[0], tm_range[1])
        sys.exit(2)
        
    # subcase dir list
    subcase_lst = GetDirList(wkd_base, case_dir)
    if population < 0:
        population = len(subcase_lst)
        print '%s: population=%d' % (myname, population)
    elif population != len(subcase_lst):
        print '%s: population(%d) and subcase number(%d) mismatch, abort.' % \
            (myname, population, len(subcase_lst))
        sys.exit(2)

    # open output file (pop_objs_eval.txt)
    ofn = os.path.join(case_dir, inter_dir, 'pop_objs_eval.txt')
    ofn2 = os.path.join(case_dir, inter_dir, 'pop_cons_eval.txt')
    try:
        ofp = open(ofn, 'w')
        ofp2 = open(ofn2, 'w')
    except Exception, e:
        print '%s: open failed: %s' % (myname, str(e))
        sys.exit(3)

    # process history files
    for sd in subcase_lst:
        hist_path = os.path.join(case_dir, sd, history_fn)
        if calc_max:
            force = GetMaxForce(hist_path, tm_range)
        else:
            force = GetAveForce(hist_path, tm_range)
        if force == None:
            ofp.write('%f %f\n' % (999.0, 999.0))
            ofp2.write('%f\n' % -1.0)
        else:
            ofp.write('%f %f\n' % (force[0], force[1]))
            ofp2.write('%f\n' % 1.0)
        continue # end of for(sd)

    # epilogue
    ofp.close()
    ofp2.close()
    sys.exit(0)

