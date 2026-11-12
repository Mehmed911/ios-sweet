#include "qemu_bl31_receiver.h"
#include "../loader/materialize.h"

#if !defined(DUCHAMP_QEMU_ONLY) || !defined(DUCHAMP_QEMU_BL31_RECEIVER)
#error "the synthetic BL31 receiver requires its isolated QEMU boot profile"
#endif

#define MAILBOX_ADDRESS UINT64_C(0x49000000)
#define MAILBOX_MAGIC UINT64_C(0x31334c42554d4551) /* Little-endian QEMUBL31 */
#define RECORD_SIZE 64u
#define BOOT_ID_DIGITS 16u

struct mailbox {
	uint64_t magic;
	uint64_t entry_id;
	unsigned char record[RECORD_SIZE];
};

_Static_assert(sizeof(struct mailbox) == 80, "QEMU BL31 mailbox layout");

static const struct {
	char name[32];
	uint32_t length;
	unsigned char record[RECORD_SIZE];
} adt_placeholder = { .name = "qemu-bl31-ufs", .length = RECORD_SIZE };

static int
same_bytes(const void *left, const void *right, size_t size)
{
	const unsigned char *a = left, *b = right;
	for (size_t i = 0; i < size; i++) {
		if (a[i] != b[i]) return 0;
	}
	return 1;
}

static unsigned char *
find_record(unsigned char *adt, size_t size)
{
	unsigned char *record = NULL;
	if (size < sizeof(adt_placeholder)) return NULL;
	/* The test generator installs this unique zeroed property in /chosen. */
	for (size_t i = 0; i <= size - sizeof(adt_placeholder); i += 4) {
		if (!same_bytes(adt + i, &adt_placeholder, sizeof(adt_placeholder))) continue;
		if (record) return NULL;
		record = adt + i + __builtin_offsetof(__typeof__(adt_placeholder), record);
	}
	return record;
}

static char *
find_entry_id(char *command)
{
	static const char placeholder[] = "sweet-qemu-boot-id=0x0000000000000000";
	const size_t token_size = sizeof(placeholder) - 1;
	char *digits = NULL;
	size_t size = 0;
	while (size < DUCHAMP_BOOT_ARGS_COMMAND_LINE_LENGTH && command[size]) size++;
	if (size == DUCHAMP_BOOT_ARGS_COMMAND_LINE_LENGTH || size < token_size) return NULL;
	for (size_t i = 0; i <= size - token_size; i++) {
		if ((i && command[i - 1] != ' ') ||
		    (command[i + token_size] && command[i + token_size] != ' ') ||
		    !same_bytes(command + i, placeholder, token_size)) continue;
		if (digits) return NULL;
		digits = command + i + token_size - BOOT_ID_DIGITS;
	}
	return digits;
}

int
duchamp_qemu_receive_bl31(const struct duchamp_dry_run_plan *plan)
{
	const volatile struct mailbox *mailbox = (const void *)(uintptr_t)MAILBOX_ADDRESS;
	if (mailbox->magic != MAILBOX_MAGIC) return 0;
	uint64_t id = mailbox->entry_id;
	if (!id) return 0;
	unsigned char *record = find_record((void *)(uintptr_t)plan->adt.destination,
	    plan->adt.copy_size);
	char *digits = find_entry_id((void *)(uintptr_t)(plan->boot_args.destination +
	    DUCHAMP_BOOT_ARGS_COMMAND_LINE_OFFSET));
	if (!record || !digits) return 0;
	for (size_t i = 0; i < RECORD_SIZE; i++) record[i] = mailbox->record[i];
	for (size_t i = BOOT_ID_DIGITS; i > 0; i--) {
		digits[i - 1] = "0123456789abcdef"[id & 15u];
		id >>= 4;
	}
	return 1;
}
