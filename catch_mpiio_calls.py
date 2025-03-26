from __future__ import print_function
from bcc import BPF
from bcc.utils import printb
from time import sleep
import argparse
import os
from pathlib import Path

def valid_library_path(value):
    """Validates if the provided path exists and is a file"""
    filepath = Path(value)
    if not filepath.exists():
        msg = f'Error! File not found: {value}'
        raise argparse.ArgumentTypeError(msg)
    elif not filepath.is_file():
        msg = f'Error! Not a valid file: {value}'
        raise argparse.ArgumentTypeError(msg)
    else:
        return str(filepath)

parser = argparse.ArgumentParser(description="BPF program for tracing MPI_File_open")
parser.add_argument('--libmpi', '-l', type=valid_library_path, 
                      default="/usr/lib64/mpi/gcc/openmpi4/lib64/libmpi.so.40",
                      help='Full path to the libmpi.so library (default: /usr/lib64/mpi/gcc/openmpi4/lib64/libmpi.so.40)')
args = parser.parse_args()
    
    # Validate the default path if no custom path was provided
try:
    args.libmpi = valid_library_path(args.libmpi)
except argparse.ArgumentTypeError as e:
    print(e)
    exit(1)

# load BPF program
b = BPF(text="""
#include <uapi/linux/ptrace.h>

struct key_t {
    char testFileName[32];
    int fdmode;
};
BPF_HASH(counts, struct key_t);

int count(struct pt_regs *ctx) {
    if (!PT_REGS_PARM1(ctx))
        return 0;

    struct key_t k = {};
    u64 zero = 0, *val;
    bpf_probe_read(&k.testFileName, sizeof(k.testFileName), (void *)PT_REGS_PARM2(ctx));
    k.fdmode = PT_REGS_PARM3(ctx);
    // could also use `counts.increment(key)`
    val = counts.lookup_or_try_init(&k, &zero);
    if (val) {
      (*val)++;
    }
    return 0;
};
""")



print(f"Using libmpi path: {args.libmpi}")
b.attach_uprobe(name=args.libmpi, sym="MPI_File_open", fn_name="count")
# header

print("Tracing MPIIO open calls()... Hit Ctrl-C to end.")

# sleep until Ctrl-C
try:
    sleep(99999999)
except KeyboardInterrupt:
    pass

# print output
print("%10s %5s %15s" % ("COUNT", "Testfile-name", "fdmode"))
counts = b.get_table("counts")
for k, v in sorted(counts.items(), key=lambda counts: counts[1].value):
    print("%10d \"%s\" %12d" % (v.value, k.testFileName.decode('utf-8').encode('unicode_escape').decode('utf-8'), k.fdmode))
