#!/bin/bash
xpath=`dirname "$0"`
dir0=`(cd "$xpath" && pwd)`
xarch=`uname -sm | sed -e 's/ /./g'`
export LD_LIBRARY_PATH=${dir0}:$LD_LIBRARY_PATH
export DYLD_LIBRARY_PATH=${dir0}:$DYLD_LIBRARY_PATH
exec ${dir0}/moea.${xarch} $*
