#! /bin/bash
# -*- coding: utf-8 -*-
#
# HPC/PF PDIサブシステム
# pdi起動コマンドインターフェース
#
# copyright (c) 2014 IIS, Tokyo Univ., Japan
#
if [ "x$1" == "x" ]; then
    echo usage: `basename $0` param_descfile.pdi
    exit 1
fi

if [ "x${HPCPF_HOME}" == "x" ]; then
  #echo FATAL: environment variable HPCPF_HOME not set.
  #exit 1
  export HPCPF_HOME=$HOME
fi

xpath=`dirname "$0"`
dir0=`(cd "$xpath" && pwd)`
PDI_DIR=`dirname "$dir0"`
export PYTHONPATH=${PDI_DIR}/lib/python:$PYTHONPATH

# for MacOSX
#export VERSIONER_PYTHON_VERSION=2.5
export VERSIONER_PYTHON_PREFER_32_BIT=yes

datadir=`dirname $1`
datafile=`basename $1`
cd "${datadir}"
exec python ${PDI_DIR}/lib/python/pdi.py -d "${datafile}"
