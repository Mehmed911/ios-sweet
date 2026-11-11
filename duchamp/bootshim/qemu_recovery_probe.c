/* Minimal Linux PID 1 for the QEMU recovery-return test. */

enum {
	SYS_MOUNT = 40,
	SYS_OPENAT = 56,
	SYS_READ = 63,
	SYS_WRITE = 64,
	SYS_PPOLL = 73,
	SYS_REBOOT = 142,
	SYS_GETPID = 172,
	AT_FDCWD = -100,
	O_RDWR = 2,
};

#define LINUX_REBOOT_MAGIC1 0xfee1deadL
#define LINUX_REBOOT_MAGIC2 672274793L
#define LINUX_REBOOT_CMD_RESTART 0x01234567L

static long
syscall5(long number, long a0, long a1, long a2, long a3, long a4)
{
	register long x0 __asm__("x0") = a0;
	register long x1 __asm__("x1") = a1;
	register long x2 __asm__("x2") = a2;
	register long x3 __asm__("x3") = a3;
	register long x4 __asm__("x4") = a4;
	register long x8 __asm__("x8") = number;
	__asm__ volatile("svc #0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x3),
	    "r"(x4), "r"(x8) : "memory");
	return x0;
}

static int
contains(const char *data, long bytes, const char *token, long length)
{
	for (long pos = 0; pos <= bytes - length; pos++) {
		long i = 0;
		while (i < length && data[pos + i] == token[i])
			i++;
		if (i == length)
			return 1;
	}
	return 0;
}

#define LOG(message) syscall5(SYS_WRITE, console, (long)(message), sizeof(message) - 1, 0, 0)

__attribute__((noreturn)) void
_start(void)
{
	const long console = syscall5(SYS_OPENAT, AT_FDCWD, (long)"/dev/console", O_RDWR, 0, 0);
	if (console < 0 || syscall5(SYS_GETPID, 0, 0, 0, 0, 0) != 1)
		goto stop;
	if (syscall5(SYS_MOUNT, (long)"proc", (long)"/proc", (long)"proc", 0, 0) < 0)
		goto stop;
	const long cmdline = syscall5(SYS_OPENAT, AT_FDCWD, (long)"/proc/cmdline", 0, 0, 0);
	char arguments[4096];
	const long bytes = syscall5(SYS_READ, cmdline, (long)arguments, sizeof(arguments), 0, 0);
	static const char slot_a[] = "androidboot.slot_suffix=_a ";
	static const char slot_b[] = "androidboot.slot_suffix=_b ";
	if (contains(arguments, bytes, slot_a, sizeof(slot_a) - 1)) {
		LOG("DUCHAMP RETURN PROBE ANDROID KERNEL A PID1\n");
	} else if (contains(arguments, bytes, slot_b, sizeof(slot_b) - 1)) {
		LOG("DUCHAMP RETURN PROBE RECOVERY B PID1\n");
		LOG("DUCHAMP RETURN PROBE NEXT SLOT REQUEST A\n");
		char reply[8];
		const long count = syscall5(SYS_READ, console, (long)reply, sizeof(reply), 0, 0);
		if (count == 2 && reply[0] == 'A' && reply[1] == '\n') {
			LOG("DUCHAMP RETURN PROBE NEXT SLOT VERIFIED A\n");
			syscall5(SYS_REBOOT, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
			    LINUX_REBOOT_CMD_RESTART, 0, 0);
			LOG("DUCHAMP RETURN PROBE REBOOT RETURNED\n");
		} else {
			LOG("DUCHAMP RETURN PROBE WRONG SLOT\n");
		}
	}

stop:
	for (;;)
		syscall5(SYS_PPOLL, 0, 0, 0, 0, 0);
}
