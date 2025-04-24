 from __future__ import print_function
 from bcc import BPF
 from time import sleep, strftime
 import os
 import subprocess
 import signal
 import sys
 
 bpf_text = """
 #include <linux/sched.h>
 
 struct pid_info {
     u32 tgid;
     char comm[TASK_COMM_LEN];
 };
 
 BPF_HASH(read_start, u32, u64);
 BPF_HASH(iops_latency, u32, u64);
 BPF_HASH(iops_tgid_cnt, struct pid_info, u64);
 
 TRACEPOINT_PROBE(syscalls, sys_enter_read)
 {
     u32 tgid = bpf_get_current_pid_tgid() >> 32;
     u64 ts = bpf_ktime_get_ns();
     read_start.update(&tgid, &ts);
     return 0;
 }
 
 TRACEPOINT_PROBE(syscalls, sys_exit_read) {
     u64 *start_ts, latency;
     u64 zero = 0, *count, *prev_lat;
     
     struct pid_info key ={};
     bpf_get_current_comm(&key.comm, sizeof(key.comm));
     u32 tgid = bpf_get_current_pid_tgid() >> 32;
     key.tgid = tgid;
     
     // fetch timestamp and calculate delta
     start_ts = read_start.lookup(&tgid);
     if (start_ts == 0) {
         return 0;   // missed issue
     }
     prev_lat = iops_latency.lookup_or_init(&tgid, &zero);
     latency = bpf_ktime_get_ns() - *start_ts;
 
     latency /= 1000;  // convert to microseconds
     
     (*prev_lat) += latency;
 
     count = iops_tgid_cnt.lookup_or_init(&key, &zero);
     (*count)++;
     read_start.delete(&tgid);
     return 0;
 }
 """
 # load BPF program
 b = BPF(text=bpf_text)
 
 print("Tracing IO operations per microseconds... Hit Ctrl-C to end.")
 
 
 def signal_ignore(signal, frame):
     print()
 
 signal.signal(signal.SIGINT, signal_ignore)
 
 # Wait until Ctrl+C
 signal.pause()
 
 rlat = b["iops_latency"]
 rcnt = b["iops_tgid_cnt"]
 
 print(f"{'PID':<8} {'Command':<20} {'Latency (µs)':<15} {'Count':<5}")
 print("-" * 50)
 for k, v in rcnt.items():
     pid = k.tgid
     comm = k.comm.decode()
     cnt = v.value
     latency = rlat[k].value
     print(f"{pid:<8} {comm:<20} {latency:<15} {cnt:<5}")
