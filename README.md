# OS: Linux Kernel 6.4

## Distribution: OpenSUSE Leap 15.6

Reason for OpenSUSE was because of some strange segfaults and binary stripping in Ubuntu Jammy 22.04 both with apt package manager and manual install. (See Issue: https://github.com/bpftrace/bpftrace/issues/954)

## Running the code on OpenSUSE

- Environment should have python3 installed
- Next step is setting up bcc. For openSUSE Leap 42.2 (and later) and Tumbleweed, bcc is already included in the official repo. Just install the packages with zypper.
```
sudo zypper ref
sudo zypper in bcc-tools bcc-examples
```
- running fs-latency.py, this file will track latency on all read latency on all filesystems
```
sudo python3 fs-latency.py
```
- similarly for running vfs-count.py, this bcc code will track the count of vfs read write open and link and unlink requets per second 
```
sudo python3 vfs-count.py
```
-- If you run and get an error saying that something like kernel headers not found it is because The default installation command installs kernel headers at a weird place and not in /lib/modules/$(uname -r), thus bcc might break. Manually copy the folders from the wrong folder (also in /lib/modules/) to the right one, it works

let me know if you still have any error.

