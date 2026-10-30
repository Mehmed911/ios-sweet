#include "sweet-notify.h"
extern void sync(void);
static int nfy_bad(const char *step) {
    ipc_note("NOTIFY ERROR step=%s", step);
    /* Persist inode/directory updates before the runner sees the FAIL marker. */
    sync();
    return ipc_fail(step);
}
static int nfy_receive(int token, int id, int phase, unsigned long long expected) {
    for (int i = 0; i < 300; ++i) {
        int changed = 0; unsigned long long value = 0;
        if (notify_check(token, &changed)) return nfy_bad("notify check");
        if (changed) {
            if (notify_get_state(token, &value) || value != expected) return nfy_bad("notify state mismatch");
            ipc_note("NOTIFY RECEIVED id=%d phase=%d state=0x%016llx changed=1", id, phase, value);
            return 0;
        }
        sleep(1);
    }
    return nfy_bad("notify receive timeout");
}
static int nfy_sequence(int id) {
    int token = -1, publisher = -1, changed = -1; unsigned long long initial = ~0ULL;
    ipc_note("NOTIFY REGISTER BEGIN id=%d", id);
    /* Libnotify-312 register_check with zero shm pages returns nid=0.
     * Plain IPC registration uses NID_UNSET and resolves the real name by token. */
    unsigned int status = notify_register_plain(NFY_NAME, &token);
    ipc_note("NOTIFY REGISTER RESULT id=%d api=plain status=%u token=%d", id, status, token);
    if (status || !notify_is_valid_token(token)) return nfy_bad("notify registration/token");
    status = notify_get_state(token, &initial);
    ipc_note("NOTIFY INITIAL STATE id=%d status=%u state=0x%016llx", id, status, initial);
    if (status || initial != 0) return nfy_bad("notify initial state");
    status = notify_check(token, &changed);
    ipc_note("NOTIFY INITIAL CHECK id=%d status=%u changed=%d", id, status, changed);
    if (status || changed != 1) return nfy_bad("notify initial check");
    status = notify_check(token, &changed);
    ipc_note("NOTIFY QUIET CHECK id=%d status=%u changed=%d", id, status, changed);
    if (status || changed != 0) return nfy_bad("notify quiet check");
    if (id == 1 && notify_register_plain(NFY_NAME, &publisher)) return nfy_bad("notify publisher");
    ipc_note("NOTIFY REGISTERED id=%d token=%d initial_state=0 initial_changed=1 quiet=0", id, token);
    if (nfy_mark("ready", id) || nfy_wait("begin", 0)) return nfy_bad("notify begin gate");
    if (id == 1) {
        if (notify_set_state(publisher, NFY_ONE) || notify_post(NFY_NAME)) return nfy_bad("notify first post");
        ipc_note("NOTIFY POSTED phase=1 state=0x%016llx", NFY_ONE);
    }
    if (nfy_receive(token, id, 1, NFY_ONE) || nfy_mark("received1", id)) return 1;
    if (id == 1) {
        if (nfy_wait("received1", 2) || notify_cancel(token) || notify_is_valid_token(token) ||
            notify_check(token, &changed) != 2) return nfy_bad("notify first cancel");
        ipc_note("NOTIFY CANCELLED id=1 valid=0 check_status=2");
        if (notify_set_state(publisher, NFY_TWO) || notify_post(NFY_NAME)) return nfy_bad("notify second post");
        ipc_note("NOTIFY POSTED phase=2 state=0x%016llx", NFY_TWO);
        if (nfy_wait("received2", 2) || notify_is_valid_token(token) || notify_check(token, &changed) != 2)
            return nfy_bad("cancelled token after second post");
        ipc_note("NOTIFY CANCEL HOLDS id=1 phase=2 valid=0 check_status=2");
        if (notify_cancel(publisher)) return nfy_bad("notify publisher cleanup");
    } else {
        if (nfy_receive(token, id, 2, NFY_TWO) || nfy_mark("received2", id) ||
            notify_cancel(token) || notify_is_valid_token(token) || notify_check(token, &changed) != 2)
            return nfy_bad("notify second cancel");
        ipc_note("NOTIFY CANCELLED id=2 valid=0 check_status=2");
    }
    ipc_note("NOTIFY PROBE PASS id=%d", id);
    return nfy_mark("done", id) ? nfy_bad("notify done token") : 0;
}
