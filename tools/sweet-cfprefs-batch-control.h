#include "sweet-cfprefs-batch.h"
static int pb_gone(int pid) {
    for (int i = 0; i < 120; ++i) {
        if (kill(pid, 0) < 0 && *__error() == 3) return 0;
        pause_seconds(1);
    }
    return -1;
}
static int pb_ready(int id, int previous) {
    for (int i = 0; i < 600; ++i) {
        int pid = pb_load("pid", id);
        if (pid != previous && path_matches(pid, id ? "/sbin/sweet-ipc-client" : "/sbin/sweet-launchd-service")) return pid;
        pause_seconds(1);
    }
    return -1;
}
static int pb_wait_executable(int pid, const char *path) {
    /* kickstart -p reports the xpcproxy PID before its exec has completed. */
    for (int i = 0; i < 300; ++i) {
        if (path_matches(pid, path)) return 0;
        if (kill(pid, 0) < 0 && *__error() == 3) return -1;
        pause_seconds(1);
    }
    return -1;
}
static int pb_phase(int step) {
    if (pb_store("control", 0, step)) return fail("batch phase control");
    for (int i = 0; i < 600; ++i) {
        if (pb_load("ack", 1) == step && pb_load("ack", 2) == step && pb_load("completed", 0) == step) {
            note("BATCH PHASE COMPLETE step=%d", step); return 0;
        }
        pause_seconds(1);
    }
    return fail("batch phase acknowledgement timeout");
}
static int pb_exited(const char *tag, const char *job, int runs) {
    char *argv[] = {"launchctl", "print", (char *)job, 0};
    char expected[40]; snprintf(expected, sizeof(expected), "runs = %d\n", runs);
    if (command(tag, argv) || property_pid(output) || !strstr(output, "state = not running") ||
        !strstr(output, expected) || !strstr(output, "last exit code = 0\n")) return -1;
    return 0;
}
static int cfprefs_batch_lifecycle(void) {
    note("SCENARIO cfprefs-batch");
    int writer = pb_ready(0, -1), first = pb_ready(1, -1), reader2 = pb_ready(2, -1);
    if (writer <= 1 || first <= 1 || reader2 <= 1 || writer == first || first == reader2 || writer == reader2)
        return fail("batch initial live probes");
    note("BATCH LIVE writer=%d reader1=%d reader2=%d", writer, first, reader2);
    char *daemon[] = {"launchctl", "print", "system/com.apple.cfprefsd.xpc.daemon", 0};
    char *notify[] = {"launchctl", "print", "system/com.apple.notifyd", 0};
    if (command("batch-daemon-before", daemon) || !strstr(output, "state = running") ||
        !strstr(output, "runs = 1\n")) return fail("batch cfprefsd initial state");
    int old_daemon = property_pid(output);
    if (!path_matches(old_daemon, "/usr/sbin/cfprefsd")) return fail("batch original cfprefsd identity");
    if (command("batch-notify-before", notify) || !strstr(output, "state = running") ||
        !strstr(output, "runs = 1\n")) return fail("batch notifyd initial state");
    int notification = property_pid(output);
    if (!path_matches(notification, "/usr/sbin/notifyd")) return fail("batch original notifyd identity");
    if (pb_phase(1) || pb_phase(2)) return 1;
    if (!path_matches(writer, "/sbin/sweet-launchd-service") || !path_matches(first, "/sbin/sweet-ipc-client") ||
        !path_matches(reader2, "/sbin/sweet-ipc-client")) return fail("batch clients not simultaneously alive");
    char *restart[] = {"launchctl", "kickstart", "-k", "-p", "system/com.apple.cfprefsd.xpc.daemon", 0};
    if (command("batch-daemon-restart", restart)) return fail("batch daemon restart");
    int new_daemon = decimal(output);
    if (new_daemon <= 1 || new_daemon == old_daemon || pb_gone(old_daemon) ||
        pb_wait_executable(new_daemon, "/usr/sbin/cfprefsd")) return fail("batch restarted daemon identity");
    note("BATCH DAEMON EXEC READY pid=%d path=/usr/sbin/cfprefsd", new_daemon);
    note("BATCH DAEMON RESTART old=%d new=%d old_reaped=1", old_daemon, new_daemon);
    if (pb_store("control", 1, -1) || pb_gone(first) ||
        pb_exited("batch-reader1-first-exit", "system/org.sweet.qemu.prefs-reader1", 1))
        return fail("batch orderly first reader stop");
    char *reader_start[] = {"launchctl", "kickstart", "-p", "system/org.sweet.qemu.prefs-reader1", 0};
    if (command("batch-reader1-restart", reader_start)) return fail("batch reader restart");
    int next = decimal(output), ready = pb_ready(1, first);
    if (next <= 1 || next != ready || next == first || next == reader2 || next == writer)
        return fail("batch new reader identity");
    note("BATCH READER RESTART old=%d new=%d ready=1", first, next);
    /* Step 3 reads generation 2 without any setter after daemon restart.
     * Step 4 writes generation 3 through the existing writer connection. */
    if (pb_phase(3) || pb_phase(4) || pb_gone(writer) || pb_gone(next) || pb_gone(reader2))
        return fail("batch recovery/final exits");
    if (pb_exited("batch-writer-final", "system/org.sweet.qemu.c-service", 1) ||
        pb_exited("batch-reader1-final", "system/org.sweet.qemu.prefs-reader1", 2) ||
        pb_exited("batch-reader2-final", "system/org.sweet.qemu.prefs-reader2", 1))
        return fail("batch normal reaped launchd states");
    if (command("batch-daemon-final", daemon) || property_pid(output) != new_daemon ||
        !strstr(output, "runs = 2\n") || !strstr(output, "state = running"))
        return fail("batch final daemon state");
    if (command("batch-notify-final", notify) || property_pid(output) != notification ||
        !strstr(output, "runs = 1\n") || !strstr(output, "state = running"))
        return fail("batch notification daemon stability");
    note("BATCH CONTROL PASS writer=%d first_reader1=%d reader1=%d reader2=%d old_daemon=%d daemon=%d notifyd=%d",
         writer, first, next, reader2, old_daemon, new_daemon, notification);
    sync();
    for (unsigned int beat = 1;; ++beat) {
        pause_seconds(10);
        if (kill(writer, 0) == 0 || kill(first, 0) == 0 || kill(next, 0) == 0 || kill(reader2, 0) == 0 ||
            !path_matches(new_daemon, "/usr/sbin/cfprefsd") || !path_matches(notification, "/usr/sbin/notifyd"))
            return fail("batch stopped/daemon heartbeat");
        note("heartbeat=%u preferences_batch_stopped=1", beat);
    }
}
