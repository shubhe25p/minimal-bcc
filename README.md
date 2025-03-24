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
  
- To run fs-latency.py, which tracks read latency on all filesystems:
  ```
  sudo python3 fs-latency.py
  ```
- To run vfs-count.py, which tracks the count of VFS read, write, open, link, and unlink requests per second:
  ```
  sudo python3 vfs-count.py
  ```
- If you encounter an error indicating that kernel headers are not found, it may be because the default installation command places kernel headers in an unusual location rather than in /lib/modules/$(uname -r). Manually copy the folders from the incorrect location (also in /lib/modules/) to the correct one to resolve this issue.

Let me know if you encounter any errors.
