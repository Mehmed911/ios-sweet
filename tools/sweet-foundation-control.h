/* Included after launchctl capture helpers. */
static int foundation_lifecycle(void) {
    note("SCENARIO foundation");
    int pid = -1;
    for (int i = 0; i < 240; ++i) {
        pid = ready_pid();
        if (path_matches(pid, "/sbin/sweet-launchd-service")) break;
        pid = -1; pause_seconds(1);
    }
    if (pid <= 1) return fail("Foundation readiness");
    char *argv[] = {"launchctl", "print", (char *)target, 0};
    if (command("print-foundation-running", argv) || property_pid(output) != pid ||
        !strstr(output, "state = running")) return fail("Foundation running state");
    note("FOUNDATION RUNNING pid=%d", pid);
    int release = open("/private/var/tmp/ipc-client.exit", 0x601, 0600);
    if (release < 0 || write_all(release, "exit\n", 5) || fsync(release) || close(release))
        return fail("Foundation release");
    int gone = 0;
    for (int i = 0; i < 60; ++i) {
        if (kill(pid, 0) < 0 && *__error() == 3) { gone = 1; break; }
        pause_seconds(1);
    }
    if (!gone) return fail("Foundation not reaped");
    note("FOUNDATION REAPED pid=%d ESRCH", pid);
    pause_seconds(5);
    if (command("print-foundation-exited", argv) || property_pid(output) != 0 ||
        !strstr(output, "last exit code = 0")) return fail("Foundation normal exit");
    note("FOUNDATION CONTROL PASS pid=%d", pid);
    sync();
    for (unsigned int beat = 1;; ++beat) {
        pause_seconds(10);
        if (kill(pid, 0) == 0 || *__error() != 3) return fail("Foundation restarted");
        note("heartbeat=%u foundation_stopped=1 pid=%d", beat, pid);
    }
}
