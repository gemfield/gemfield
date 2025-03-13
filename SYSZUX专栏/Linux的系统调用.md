# 背景
系统调用（System Call）是用户态程序使用内核态服务的接口。为什么用户态调用内核态的能力需要有专门的接口呢？这进而在暗示我们，用户态和内核态有一些本质区别。那么这个本质区别是什么呢？以x86为例，CPU时刻处于4个ring中的某一个，称之为Current Privilege Level (CPL)，GDT中的Privl字段携带着这个信息，CS、SS寄存器的最低2bits也有这个信息： 

- 0b00 (ring 0)
- 0b01 (ring 1)
- 0b10 (ring 2)
- 0b11 (ring 3)

Linux使用了ring 0和ring 3，其中内核态为ring0，用户态为ring3。ring0和ring3的区别是什么呢？

## 1，ring0
ring0可以做一切事情。比如，内核态的代码具有硬件的所有访问权限，所有内核态的代码共享一个虚拟地址空间等。

## 2，ring3
在ring3状态下：

- 不能改变当前的ring值；
- 不能修改CR3寄存器，从而不能修改page tables，也就不能看到别的进程的地址空间；
- 不能使用LGDT、LLDT、LIDT指令，也就不能用来注册interrupt handlers；
- 不能使用LTR指令；
- 不能load、store control register；
- 不能使用lmsw、clts、invlpg、hlt、rdmsr、wrmsr、rdpmc；
- 不能使用 invd in cr0、wbinvd；

还有一些IO指令，R0可以毫无限制的使用，而R3使用就需要检查IO permission bitmap。这些指令有：

- cli、sti，关闭、打开中断；
- in，从硬件端口读；
- out，写硬件端口。

可以看得出来，用户态有诸多限制，设置两种不同的ring的目的也显而易见了，主要有两个：

- 防止犯错：程序之间相互干扰，或者程序的bug直接crash了宿主机系统等；
- 安全防范：这就是防止恶意程序了。

# 系统调用的过程
系统调用并不是让用户程序直接使用的，用户程序应该使用标准C库来享受系统调用提供的服务。这种系统调用和标准C库的混合所最终呈现出的接口就是我们说的Linux API（也即C库中和系统调用相关的API）。
用户态应用程序调用System Call的过程是：

- 应用程序调用C库函数（Linux API）；
- C库函数（Linux API） 将系统调用号存入 EAX；
- C库函数（Linux API） 把函数参数存入其它通用寄存器（%rdi、%rsi、%rdx、%r10、%r8、%r9）；
- C库函数（Linux API） 通过中断调用使系统进入内核态：x86上触发0x80 号中断（int 0x80），x86-64上触发syscall/sysenter；
- 内核中的中断处理函数根据系统调用号，调用对应的内核函数（系统调用）；
- 内核函数（系统调用）完成相应功能，将返回值存入 EAX，返回到内核中的中断处理函数；
- 内核中的中断处理函数返回到C库函数（Linux API） 中；
- C库函数（Linux API） 将 EAX 返回给应用程序。

我们以1号系统调用（write系统调用）来举个例子：
```c
//gemfield.S文件
.data

msg:
    .ascii "Hello, Gemfield!\n"
    len = . - msg

.text
    .global _start

_start:
    movq  $1, %rax
    movq  $1, %rdi
    movq  $msg, %rsi
    movq  $len, %rdx
    syscall

    movq  $60, %rax
    movq  $30, %rdi
    syscall
```
最后的syscall就是用来触发系统调用，syscall会导致如下的步骤：

- 将syscall后面的指令的地址保存到RCX寄存器；
- MSR_LSTAR(Model Specific Register_Long System Target Address Register)的值装载到RIP寄存器；这个寄存器上的值正是entry_SYSCALL_64函数的地址；
- 从rax寄存器读到$1，知道是write系统调用；
- 从rdi、rsi、rdx分别读到此次系统调用的三个参数：分别是File descriptor（gemfield.S中是$1，也就是标准输出stdout）、字符串的地址、字符串的长度；
- 执行完该系统调用后，我们又将进入下一个系统调用；
- 从rax寄存器读到$60，知道是exit系统调用；
- rdi读到此次系统调用的一个参数：返回值30。

编译并运行：
```bash
gemfield@CivilNet:~$ gcc -c gemfield.S
gemfield@CivilNet:~$ ld -o gemfield gemfield.o
gemfield@CivilNet:~$ ./gemfield 
Hello, Gemfield!
gemfield@CivilNet:~$ echo $?
30
```
我们也可以使用strace工具来看下gemfield程序中使用的系统调用：
```bash
gemfield@CivilNet:~$ strace ./gemfield
execve("./gemfield", ["./gemfield"], 0x7ffdc8af67b0 /* 71 vars */) = 0
write(1, "Hello, Gemfield!\n", 17Hello, Gemfield!
)      = 17
exit(30)                                = ?
+++ exited with 30 +++
```
可以看到一共用了三个系统调用，分别是execve、write、exit。我们之所以能够根据号码来找到对应的系统调用，是因为在Linux内核启动的时候，初始化并维护了一张表：sys_call_table。以x86-64为例，在arch/x86/entry/syscall_64.c中：
```c
const sys_call_ptr_t sys_call_table[] = {
#include <asm/syscalls_64.h>
};
```
大概有500多个系统调用。

最后，Gemfield需要强调的是，系统调用不是context switch，这是两个截然不同的概念。

# 系统调用有哪些
## 1，系统调用的数量
Linux的系统调用数量是变化的，具体来说体现在如下方面：

- 不同的CPU指令集架构，有不同的系统调用；
- 不同的内核版本，系统调用或许有增减；
- 有的系统调用压根就没用，就一直放在那里。

以Gemfield正在使用的5.11版本来说，这个系统调用有500多个。

## 2，系统调用的类别

- 进程控制
```
    1.1，创建进程；
    1.2，终止进程；
    1.3，运行进程；
    1.4，获取/设置进程的属性；
    1.5，时间、事件、信号的处理；
    1.6，分配和销毁内存；
```
- 文件管理
```
    2.1，创建、删除文件；
    2.2，打开、关闭文件；
    2.3，读写文件、重定位文件当前的读写位置；
    2.4，获取/设置文件属性。
```
- 设备管理
```
    3.1，申请、释放设备；
    3.2，读写设备、重定位设备当前的位置；
    3.3，获取/设置设备的属性；
    3.4，逻辑上绑定、解绑设备
```
- 信息维护
```
    4.1，获取/设置系统信息 (比如time、date、computer name等）；
    4.2，获取/设置进程、文件、设备的metadata (包括作者、打开者、创建日期时间等）；
```
- 通信
```
    5.1，创建、删除通信连接；
    5.2，发收消息；
    5.3，传递状态信息；
    5.4，绑定、解绑远端设备。
```
- 保护
```
    6.1，获取/设置文件权限。
```
# 3，系统调用的详细清单
以x86-64指令集架构为例，最新的Linux内核提供的系统调用有：
```
_llseek(2)                  1.2
_newselect(2)               2.0
accept(2)                   2.0
accept4(2)                  2.6.28
access(2)                   1.0
acct(2)                     1.0
add_key(2)                  2.6.10
adjtimex(2)                 1.0
alarm(2)                    1.0
arch_prctl(2)               2.6
bind(2)                     2.0
bpf(2)                      3.18
brk(2)                      1.0
capget(2)                   2.2
capset(2)                   2.2
chdir(2)                    1.0
chmod(2)                    1.0
chown(2)                    2.2 
chown32(2)                  2.4
chroot(2)                   1.0
clock_adjtime(2)            2.6.39
clock_getres(2)             2.6
clock_gettime(2)            2.6
clock_nanosleep(2)          2.6
clock_settime(2)            2.6
clone(2)                    1.0
clone3(2)                   5.3
close(2)                    1.0
close_range(2)              5.9
connect(2)                  2.0
copy_file_range(2)          4.5
creat(2)                    1.0
delete_module(2)            1.0
dup(2)                      1.0
dup2(2)                     1.0
dup3(2)                     2.6.27
epoll_create(2)             2.6
epoll_create1(2)            2.6.27
epoll_ctl(2)                2.6
epoll_pwait(2)              2.6.19
epoll_pwait2(2)             5.11
epoll_wait(2)               2.6
eventfd(2)                  2.6.22
eventfd2(2)                 2.6.27
execve(2)                   1.0
execveat(2)                 3.19
exit(2)                     1.0
exit_group(2)               2.6
faccessat(2)                2.6.16
faccessat2(2)               5.8
fadvise64(2)                2.6
fadvise64_64(2)             2.6
fallocate(2)                2.6.23
fanotify_init(2)            2.6.37
fanotify_mark(2)            2.6.37
fchdir(2)                   1.0
fchmod(2)                   1.0
fchmodat(2)                 2.6.16
fchown(2)                   1.0
fchown32(2)                 2.4
fchownat(2)                 2.6.16
fcntl(2)                    1.0
fcntl64(2)                  2.4
fdatasync(2)                2.0
fgetxattr(2)                2.6; 2.4.18
finit_module(2)             3.8
flistxattr(2)               2.6; 2.4.18
flock(2)                    2.0
fork(2)                     1.0
fremovexattr(2)             2.6; 2.4.18
fsconfig(2)                 5.2
fsetxattr(2)                2.6; 2.4.18
fsmount(2)                  5.2
fsopen(2)                   5.2
fspick(2)                   5.2
fstat(2)                    1.0
fstat64(2)                  2.4
fstatat64(2)                2.6.16
fstatfs(2)                  1.0
fstatfs64(2)                2.6
fsync(2)                    1.0
ftruncate(2)                1.0
ftruncate64(2)              2.4
futex(2)                    2.6
futimesat(2)                2.6.16
get_mempolicy(2)            2.6.6
get_robust_list(2)          2.6.17
get_thread_area(2)          2.6
getcpu(2)                   2.6.19
getcwd(2)                   2.2
getdents(2)                 2.0
getdents64(2)               2.4
getegid(2)                  1.0
getegid32(2)                2.4
geteuid(2)                  1.0
geteuid32(2)                2.4
getgid(2)                   1.0
getgid32(2)                 2.4
getgroups(2)                1.0
getgroups32(2)              2.4
getitimer(2)                1.0
getpeername(2)              2.0
getpgid(2)                  1.0
getpgrp(2)                  1.0
getpid(2)                   1.0
getppid(2)                  1.0
getpriority(2)              1.0
getrandom(2)                3.17
getresgid(2)                2.2
getresgid32(2)              2.4
getresuid(2)                2.2
getresuid32(2)              2.4
getrlimit(2)                1.0
getrusage(2)                1.0
getsid(2)                   2.0
getsockname(2)              2.0
getsockopt(2)               2.0
gettid(2)                   2.4.11
gettimeofday(2)             1.0
getuid(2)                   1.0
getuid32(2)                 2.4
getxattr(2)                 2.6; 2.4.18
init_module(2)              1.0
inotify_add_watch(2)        2.6.13
inotify_init(2)             2.6.13
inotify_init1(2)            2.6.27
inotify_rm_watch(2)         2.6.13
io_cancel(2)                2.6
io_destroy(2)               2.6
io_getevents(2)             2.6
io_pgetevents(2)            4.18
io_setup(2)                 2.6
io_submit(2)                2.6
io_uring_enter(2)           5.1
io_uring_register(2)        5.1
io_uring_setup(2)           5.1
ioctl(2)                    1.0
ioperm(2)                   1.0
iopl(2)                     1.0
ioprio_get(2)               2.6.13
ioprio_set(2)               2.6.13
ipc(2)                      1.0
kcmp(2)                     3.5
kexec_file_load(2)          3.17
kexec_load(2)               2.6.13
keyctl(2)                   2.6.10
kill(2)                     1.0
landlock_add_rule(2)        5.13
landlock_create_ruleset(2)  5.13
landlock_restrict_self(2)   5.13
landlock_add_rule(2)        5.13
lchown(2)                   1.0
lchown32(2)                 2.4
lgetxattr(2)                2.6; 2.4.18
link(2)                     1.0
linkat(2)                   2.6.16
listen(2)                   2.0
listxattr(2)                2.6; 2.4.18
llistxattr(2)               2.6; 2.4.18
lookup_dcookie(2)           2.6
lremovexattr(2)             2.6; 2.4.18
lseek(2)                    1.0
lsetxattr(2)                2.6; 2.4.18
lstat(2)                    1.0
lstat64(2)                  2.4
madvise(2)                  2.4
mbind(2)                    2.6.6
membarrier(2)               3.17
memfd_create(2)             3.17
migrate_pages(2)            2.6.16
mincore(2)                  2.4
mkdir(2)                    1.0
mkdirat(2)                  2.6.16
mknod(2)                    1.0
mknodat(2)                  2.6.16
mlock(2)                    2.0
mlock2(2)                   4.4
mlockall(2)                 2.0
mmap(2)                     1.0
mmap2(2)                    2.4
modify_ldt(2)               1.0
mount(2)                    1.0
move_mount(2)               5.2
move_pages(2)               2.6.18
mprotect(2)                 1.0
mq_getsetattr(2)            2.6.6
mq_notify(2)                2.6.6
mq_open(2)                  2.6.6
mq_timedreceive(2)          2.6.6
mq_timedsend(2)             2.6.6
mq_unlink(2)                2.6.6
mremap(2)                   2.0
msgctl(2)                   2.0
msgget(2)                   2.0
msgrcv(2)                   2.0
msgsnd(2)                   2.0
msync(2)                    2.0
munlock(2)                  2.0
munlockall(2)               2.0
munmap(2)                   1.0
name_to_handle_at(2)        2.6.39
nanosleep(2)                2.0
newfstatat(2)               2.6.16
nice(2)                     1.0
old_getrlimit(2)            2.4 
oldfstat(2)                 1.0
oldlstat(2)                 1.0
oldolduname(2)              1.0
oldstat(2)                  1.0
oldumount(2)                2.4.116       Name of the old umount(2) syscall on Alpha
olduname(2)                 1.0
open(2)                     1.0
open_by_handle_at(2)        2.6.39
open_tree(2)                5.2
openat(2)                   2.6.16
openat2(2)                  5.6
pause(2)                    1.0
perf_event_open(2)          2.6.31        Was perf_counter_open() in 2.6.31; renamed in 2.6.32
personality(2)              1.2
pidfd_getfd(2)              5.6
pidfd_send_signal(2)        5.1
pidfd_open(2)               5.3
pipe(2)                     1.0
pipe2(2)                    2.6.27
pivot_root(2)               2.4
pkey_alloc(2)               4.8
pkey_free(2)                4.8
pkey_mprotect(2)            4.8
poll(2)                     2.0.36; 2.2
ppoll(2)                    2.6.16
prctl(2)                    2.2
pread64(2)                           Added as "pread" in 2.2; renamed "pread64" in 2.6
preadv(2)                   2.6.30
preadv2(2)                  4.6
prlimit64(2)                2.6.36
process_madvise(2)          5.10
process_vm_readv(2)         3.2
process_vm_writev(2)        3.2
pselect6(2)                 2.6.16
ptrace(2)                   1.0
pwrite64(2)                       Added as "pwrite" in 2.2; renamed "pwrite64" in 2.6
pwritev(2)                  2.6.30
pwritev2(2)                 4.6
quotactl(2)                 1.0
quotactl_fd(2)              5.14
read(2)                     1.0
readahead(2)                2.4.13
readdir(2)                  1.0
readlink(2)                 1.0
readlinkat(2)               2.6.16
readv(2)                    2.0
reboot(2)                   1.0
recv(2)                     2.0
recvfrom(2)                 2.0
recvmsg(2)                  2.0
recvmmsg(2)                 2.6.33
removexattr(2)              2.6; 2.4.18
rename(2)                   1.0
renameat(2)                 2.6.16
renameat2(2)                3.15
request_key(2)              2.6.10
restart_syscall(2)          2.6
rmdir(2)                    1.0
rseq(2)                     4.18
rt_sigaction(2)             2.2
rt_sigpending(2)            2.2
rt_sigprocmask(2)           2.2
rt_sigqueueinfo(2)          2.2
rt_sigreturn(2)             2.2
rt_sigsuspend(2)            2.2
rt_sigtimedwait(2)          2.2
rt_tgsigqueueinfo(2)        2.6.31
sched_get_affinity(2)       2.6
sched_get_priority_max(2)   2.0
sched_get_priority_min(2)   2.0
sched_getaffinity(2)        2.6
sched_getattr(2)            3.14
sched_getparam(2)           2.0
sched_getscheduler(2)       2.0
sched_rr_get_interval(2)    2.0
sched_set_affinity(2)       2.6
sched_setaffinity(2)        2.6
sched_setattr(2)            3.14
sched_setparam(2)           2.0
sched_setscheduler(2)       2.0
sched_yield(2)              2.0
seccomp(2)                  3.17
select(2)                   1.0
semctl(2)                   2.0           See notes on ipc(2)
semget(2)                   2.0
semop(2)                    2.0
semtimedop(2)               2.6; 2.4.22
send(2)                     2.0
sendfile(2)                 2.2
sendfile64(2)               2.6; 2.4.19
sendmmsg(2)                 3.0
sendmsg(2)                  2.0
sendto(2)                   2.0
set_mempolicy(2)            2.6.6
set_robust_list(2)          2.6.17
set_thread_area(2)          2.6
set_tid_address(2)          2.6
setdomainname(2)            1.0
setfsgid(2)                 1.2
setfsgid32(2)               2.4
setfsuid(2)                 1.2
setfsuid32(2)               2.4
setgid(2)                   1.0
setgid32(2)                 2.4
setgroups(2)                1.0
setgroups32(2)              2.4
sethostname(2)              1.0
setitimer(2)                1.0
setns(2)                    3.0
setpgid(2)                  1.0
setpgrp(2)                  2.0
setpriority(2)              1.0
setregid(2)                 1.0
setregid32(2)               2.4
setresgid(2)                2.2
setresgid32(2)              2.4
setresuid(2)                2.2
setresuid32(2)              2.4
setreuid(2)                 1.0
setreuid32(2)               2.4
setrlimit(2)                1.0
setsid(2)                   1.0
setsockopt(2)               2.0
settimeofday(2)             1.0
setuid(2)                   1.0
setuid32(2)                 2.4
setxattr(2)                 2.6; 2.4.18
sgetmask(2)                 1.0
shmat(2)                    2.0
shmctl(2)                   2.0
shmdt(2)                    2.0
shmget(2)                   2.0
shutdown(2)                 2.0
sigaction(2)                1.0
sigaltstack(2)              2.2
signal(2)                   1.0
signalfd(2)                 2.6.22
signalfd4(2)                2.6.27
sigpending(2)               1.0
sigprocmask(2)              1.0
sigreturn(2)                1.0
sigsuspend(2)               1.0
socket(2)                   2.0
socketcall(2)               1.0
socketpair(2)               2.0
splice(2)                   2.6.17
ssetmask(2)                 1.0
stat(2)                     1.0
stat64(2)                   2.4
statfs(2)                   1.0
statfs64(2)                 2.6
statx(2)                    4.11
stime(2)                    1.0
swapoff(2)                  1.0
swapon(2)                   1.0
symlink(2)                  1.0
symlinkat(2)                2.6.16
sync(2)                     1.0
sync_file_range(2)          2.6.17
sync_file_range2(2)         2.6.22
syncfs(2)                   2.6.39
sysfs(2)                    1.2
sysinfo(2)                  1.0
syslog(2)                   1.0
tee(2)                      2.6.17
tgkill(2)                   2.6
time(2)                     1.0
timer_create(2)             2.6
timer_delete(2)             2.6
timer_getoverrun(2)         2.6
timer_gettime(2)            2.6
timer_settime(2)            2.6
timerfd_create(2)           2.6.25
timerfd_gettime(2)          2.6.25
timerfd_settime(2)          2.6.25
times(2)                    1.0
tkill(2)                    2.6; 2.4.22
truncate(2)                 1.0
truncate64(2)               2.4
ugetrlimit(2)               2.4
umask(2)                    1.0
umount(2)                   1.0
umount2(2)                  2.2
uname(2)                    1.0
unlink(2)                   1.0
unlinkat(2)                 2.6.16
unshare(2)                  2.6.16
uselib(2)                   1.0
ustat(2)                    1.0
userfaultfd(2)              4.3
utime(2)                    1.0
utimensat(2)                2.6.22
utimes(2)                   2.2
vfork(2)                    2.2
vhangup(2)                  1.0
vm86old(2)                  1.0   Was "vm86"; renamed in 2.0.28/2.2
vm86(2)                     2.0.28; 2.2
vmsplice(2)                 2.6.17
wait4(2)                    1.0
waitid(2)                   2.6.10
waitpid(2)                  1.0
write(2)                    1.0
writev(2)                   2.0
```

