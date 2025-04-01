#!/bin/bash

# This for someone at NERSC with root to run
# gcc write.c -o write

./write /global/homes/c/cookbg/ebpf-tmp/test.$(date +%s).dat 4096
./write /mscratch/sd/c/cookbg/ebpf-tmp/test.$(date +%s).dat $((128 * 1024 * 1024))
./write /global/cfs/cdirs/nstaff/cookbg/ebpf-tmp/test.$(date +%s).dat $((8 * 1024 * 1024))
