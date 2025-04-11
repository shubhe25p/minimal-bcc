#!/bin/bash
64;2500;0c
set +x

# This for someone at NERSC with root to run
# gcc write.c -o write

exe=./write

mkdir -p /global/homes/c/cookbg/ebpf-tmp
mkdir -p $SCRATCH/ebpf-tmp
mkdir -p /global/cfs/cdirs/nstaff/cookbg/ebpf-tmp

f_home=/global/homes/c/cookbg/ebpf-tmp/test.$(date +%s).dat
f_scratch=$SCRATCH/ebpf-tmp/test.$(date +%s)
f_cfs=/global/cfs/cdirs/nstaff/cookbg/ebpf-tmp/test.$(date +%s).dat

$exe $f_home 4096
$exe $f_scratch $((128 * 1024 * 1024))
$exe $f_cfs $((8 * 1024 * 1024))


python3 read.py $f_home
python3 read.py $f_scratch
python3 read.py $f_cfs
