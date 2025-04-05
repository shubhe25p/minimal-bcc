from bcc import BPF
import signal
from collections import defaultdict
import argparse

examples = """examples:
    ./fs-write-latency             # trace sync file I/O per filesystem (default)
    ./fs-write-latency -n ior      # trace processes named 'ior'
    ./fs-write-latency -p 42       # trace PID 42 only
"""
parser = argparse.ArgumentParser(
    description="Trace sync file I/O synchronous file write per FS",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=examples)
parser.add_argument("-p", "--pid", type=int, metavar="PID", dest="tgid",
    help="trace this PID only")
parser.add_argument("-n", "--name", metavar="COMM", dest="comm",
    help="trace this proc only")

args = parser.parse_args()
tgid = args.tgid
comm = args.comm

def generate_comm_string():
    # Initialize an empty list to store the formatted parts
    comm_parts = []
    
    # Loop through each character in the input string and its index
    for i, char in enumerate(comm):
        # Append the formatted string to the list
        comm_parts.append(f"fs_info.comm[{i}] == '{char}'")
    
    # Join all parts with " && " and return the result
    return " && ".join(comm_parts)




bpf_text = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>
#include <linux/fs.h>
#include <linux/dcache.h>
#include <linux/mount.h>

struct fs_stat_t {
    u64 bucket;
    u64 ts;
    u64 delta_us;
    u64 throughput;
    u32 pid;
    u32 sz;
    char fstype[32];
    char name[DNAME_INLINE_LEN];
    char comm[TASK_COMM_LEN];
};



BPF_HASH(write_start, pid_t, struct fs_stat_t);
BPF_HASH(fs_latency_hist, struct fs_stat_t, u64);
// BPF_PERF_OUTPUT(events);

static int trace_rw_entry(struct pt_regs *ctx, struct file *file,
    char __user *buf, size_t count)
{
    u32 tgid = bpf_get_current_pid_tgid() >> 32;
    if (TGID_FILTER)
        return 0;

    u32 pid = bpf_get_current_pid_tgid();

    // skip I/O lacking a filename
    struct dentry *de = file->f_path.dentry;
    int mode = file->f_inode->i_mode;
    if (de->d_name.len == 0)
        return 0;

    // store size and timestamp by pid
    struct fs_stat_t fs_info = {};
    bpf_get_current_comm(&fs_info.comm, sizeof(fs_info.comm));
    if (COMM_FILTER)
        return 0;

    fs_info.pid=pid;
    fs_info.sz=count;

    // grab file system type
    const char* fstype_name = file->f_inode->i_sb->s_type->name;
    bpf_probe_read_kernel(&fs_info.fstype, sizeof(fs_info.fstype), fstype_name);

    // grab file name
    struct qstr d_name = de->d_name;
    bpf_probe_read_kernel(&fs_info.name, sizeof(fs_info.name), d_name.name);
    

    fs_info.ts = bpf_ktime_get_ns();
    write_start.update(&pid, &fs_info);
    return 0;
}

int trace_write_entry(struct pt_regs *ctx, struct file *file,
    char __user *buf, size_t count)
{
   
     // skip non-sync I/O; see kernel code for __vfs_write()
    if (!(file->f_op->write_iter))
        return 0;

    return trace_rw_entry(ctx, file, buf, count);
}

int trace_write_return(struct pt_regs *ctx)
{
    u64 zero = 0, *count;
    u32 pid = bpf_get_current_pid_tgid();
    struct fs_stat_t *fs_info = write_start.lookup(&pid);
    if (fs_info == 0)
        return 0;
    

    u64 latency = bpf_ktime_get_ns() - fs_info->ts;
    latency /= 1000;  // convert to microseconds
    fs_info->bucket = bpf_log2l(latency);
    fs_info->delta_us = latency;
    fs_info->throughput = (fs_info->sz/latency);
    count = fs_latency_hist.lookup_or_init(fs_info, &zero);
    (*count)++;
    write_start.delete(&pid);
    // events.perf_submit(ctx, fs_info, sizeof(*fs_info));
    return 0;   
}


"""

if args.tgid:
    bpf_text = bpf_text.replace('TGID_FILTER', 'tgid != %d' % tgid)
else:
    bpf_text = bpf_text.replace('TGID_FILTER', '0')
if args.comm:
    target_str = generate_comm_string()
    bpf_text = bpf_text.replace('COMM_FILTER', target_str)
else:
    bpf_text = bpf_text.replace('COMM_FILTER', '0')


b = BPF(text=bpf_text)
try:
    b.attach_kprobe(event="__vfs_write", fn_name="trace_write_entry")
    b.attach_kretprobe(event="__vfs_write", fn_name="trace_write_return")
except Exception:
    print('Current kernel does not have __vfs_write, try vfs_write instead')
    b.attach_kprobe(event="vfs_write", fn_name="trace_write_entry")
    b.attach_kretprobe(event="vfs_write", fn_name="trace_write_return")

print("Tracing FileSystem I/O... Hit Ctrl-C to end.")


print("\nHistogram of latency requested in write() calls per fs:")


# print("%-8s %-14s %-6s %1s %-7s %7s %s" % ("TIME(s)", "COMM", "TID", "FSTYPE",
#     "BYTES", "LAT(ms)", "FILENAME"))
    
# start_ts = time.time()
# def print_event(cpu, data, size):
#     event = b["events"].event(data)

#     ms = float(event.delta_us) / 1000
#     fname = event.name.decode('utf-8', 'replace')
#     fstype = event.fstype.decode('utf-8', 'replace')

#     print("%-8.3f %-14.14s %-6s %1s %-7s %7.2f %s" % (
#         time.time() - start_ts, event.comm.decode('utf-8', 'replace'),
#         event.pid, fstype, event.bucket, ms, fname))

# b["events"].open_perf_buffer(print_event)
# while 1:
#     try:
#         b.perf_buffer_poll()
#     except KeyboardInterrupt:
#         exit()

def signal_ignore(signal, frame):
    print()

signal.signal(signal.SIGINT, signal_ignore)

# Wait until Ctrl+C
signal.pause()


histogram = b.get_table("fs_latency_hist")

fs_hist = defaultdict(lambda: defaultdict(int))

for k, v in histogram.items():
    fsname = k.fstype
    bucket = k.bucket
    count = v.value
    fs_hist[fsname][bucket] += count

for fs, buckets in fs_hist.items():
    print(f"\nFile System {fs}:")


    total_count = sum(buckets.values())
    print(f"Total Writes: {total_count}")
    
    # Prepare data for printing
    sorted_buckets = sorted(buckets.items())
    max_bucket = max(buckets.keys())
    
    # Print the histogram header
    print("       usecs      : count     distribution")

    # Calculate the maximum count for scaling the histogram bars
    max_count = max(buckets.values())
    width = 40  # Adjust the width of the histogram bars as needed

    for b, c in sorted_buckets:
        # Compute the bucket range based on log2 boundaries
        low = (1 << b) if b > 0 else 0
        high = (1 << (b + 1)) - 1
        bar_len = int(c * width / max_count) if max_count > 0 else 0
        bar = '*' * bar_len
        print(f"{low:>10} -> {high:<10} : {c:<8} |{bar}")
