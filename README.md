# OS: Linux Kernel 6.4

## Distribution: OpenSUSE Leap 15.6

The reason for choosing OpenSUSE is due to strange segfaults and binary stripping issues in Ubuntu Jammy 22.04, both with the apt package manager and manual installation. (See Issue: https://github.com/bpftrace/bpftrace/issues/954)

## Running the Code on OpenSUSE

- Ensure Python3 is installed.
- Set up BCC. For OpenSUSE Leap 42.2 (and later) and Tumbleweed, BCC is included in the official repository. Install the packages with zypper:
  ```sh
  sudo zypper ref
  sudo zypper in bcc-tools bcc-examples
  ```

- To run catch-mpiio.py, which catches MPI_File_open calls made by IOR and prints filename, fdmode and count. It needs the absolute path to the libmpi file:
  ```
  sudo python3 catch-mpiio.py -l /path/to/libmpi.so
  ```

-> Sample output for catch-mpiio.py:
```
  > ec2-user@ip-172-31-30-35:~/ebpf-nersc> sudo python3 catch_mpiio.py
Using libmpi path: /usr/lib64/mpi/gcc/openmpi4/lib64/libmpi.so.40
Tracing MPIIO open calls()... Hit Ctrl-C to end.
^C     COUNT Testfile-name          fdmode
         1 "testFile.00000002"           37
         1 "testFile.00000001"           37
         1 "testFile.00000003"           37
         1 "testFile.00000000"           37
         2 "testFile.00000002"            2
         2 "testFile.00000001"            2
         2 "testFile.00000000"            2
         2 "testFile.00000003"            2
         3 "testFile.00000002"           34
         3 "testFile.00000003"           34
         3 "testFile.00000000"           34
         3 "testFile.00000001"           34
  ```
- To run fs-latency.py, which tracks read latency on all filesystems:
  ```
  sudo python3 fs-latency.py
  ```
-> Sample output for fs-latency.py
```
  ec2-user@ip-172-31-30-35:~/ebpf-nersc> sudo python3 fs-latency.py
  Tracing FileSystem I/O... Hit Ctrl-C to end.
  ^C

  Histogram of latency requested in read() calls per fs:

  File System b'/':
  Total Reads: 71
       usecs      : count     distribution
         2 -> 3          : 27       |****************************************
         4 -> 7          : 1        |*
         8 -> 15         : 16       |***********************
        16 -> 31         : 22       |********************************
        32 -> 63         : 3        |****
        64 -> 127        : 2        |**
```
- To run vfs-count.py, which tracks the count of VFS read, write, open, link, and unlink requests per second:
  ```
  sudo python3 vfs-count.py
  ```

-> Sample output for vfs-count.py
```
ec2-user@ip-172-31-30-35:~/ebpf-nersc> sudo python3 vfs_count.py
TIME         READ/s  WRITE/s  FSYNC/s   OPEN/s CREATE/s UNLINK/s  MKDIR/s  RMDIR/s
23:33:48:      3759       10        0       15        0        0        0        0
23:33:49:         2        3        0        0        0        0        0        0
23:33:50:         2        3        0        0        0        0        0        0
23:33:51:         2        3        0        0        0        0        0        0
23:33:52:         2        3        0        0        0        0        0        0
23:33:53:         2        3        0        0        0        0        0        0
23:33:54:         2        3        0        0        0        0        0        0
23:33:55:         2        3        0        0        0        0        0        0
23:33:56:         2        3        0        0        0        0        0        0
23:33:57:         2        3        0        0        0        0        0        0
23:33:58:        16        3        0       11        0        0        0        0
^C23:33:58:         6        7        0        0        0        0        0        0
```

**NOTE: If you encounter an error while running the scripts above like this**
  ```
  ec2-user@ip-172-31-30-35:~/ebpf-nersc> sudo python3 fs-latency.py
  modprobe: FATAL: Module kheaders not found in directory /lib/modules/6.4.0-150600.23.25-default
  Unable to find kernel headers. Try rebuilding kernel with CONFIG_IKHEADERS=m (module) or installing the kernel development package for your running kernel version.
  chdir(/lib/modules/6.4.0-150600.23.25-default/build): No such file or directory
  Traceback (most recent call last):
  File "fs-latency.py", line 107, in <module>
    b = BPF(text=bpf_text)
  File "/usr/lib/python3.6/site-packages/bcc/__init__.py", line 479, in __init__
    raise Exception("Failed to compile BPF module %s" % (src_file or "<text>"))
  Exception: Failed to compile BPF module <text>
  ```

**It is because the default installation command places kernel headers in an unusual location rather than in /lib/modules/$(uname -r) which is where BCC will search. Manually copy the folders (build and source) from the incorrect location (also in /lib/modules/) to the correct one to resolve this issue.**


Let me know if you encounter any errors.
