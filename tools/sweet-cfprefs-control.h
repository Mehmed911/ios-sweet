/* The observer never reads/writes preferences; the two Foundation probes do. */
static int prefs_gone(int pid) {
    for (int i = 0; i < 120; ++i) {
        if (kill(pid, 0) < 0 && *__error() == 3) return 0;
        pause_seconds(1);
    }
    return -1;
}
static int cfprefs_lifecycle(void) {
    note("SCENARIO cfprefsd");
    int writer = -1;
    for (int i = 0; i < 360; ++i) {
        writer = ready_pid();
        if (path_matches(writer, "/sbin/sweet-launchd-service")) break;
        writer = -1; pause_seconds(1);
    }
    if (writer <= 1) return fail("preferences writer readiness");
    char *writer_print[] = {"launchctl", "print", (char *)target, 0};
    if (command("prefs-writer-running", writer_print) || property_pid(output) != writer ||
        !strstr(output, "state = running") || !strstr(output, "runs = 1\n"))
        return fail("writer state");
    int servers[2] = {0, 0};
    char *names[] = {"system/com.apple.cfprefsd.xpc.daemon", "system/com.apple.cfprefsd.xpc.daemon.system"};
    for (int i = 0; i < 2; ++i) {
        char tag[64]; snprintf(tag, sizeof(tag), "cfprefsd-%d-before", i);
        char *argv[] = {"launchctl", "print", names[i], 0};
        if (command(tag, argv)) return fail("cfprefsd job print");
        servers[i] = property_pid(output);
        if (servers[i] && !path_matches(servers[i], "/usr/sbin/cfprefsd")) return fail("cfprefsd executable");
    }
    if (!servers[0] && !servers[1]) return fail("no original cfprefsd process");
    note("PREFERENCES DAEMONS regular=%d system=%d writer=%d", servers[0], servers[1], writer);
    int readers[2] = {0, 0};
    for (int cycle = 0; cycle < 2; ++cycle) {
        char tag[80];
        snprintf(tag, sizeof(tag), "prefs-reader-start-%d", cycle + 1);
        char *start[] = {"launchctl", "kickstart", "-p", "system/org.sweet.qemu.ipc-client", 0};
        if (command(tag, start)) return fail("reader kickstart");
        readers[cycle] = decimal(output);
        if (readers[cycle] <= 1 || readers[cycle] == writer || (cycle && readers[0] == readers[1]))
            return fail("new reader PID");
        if (prefs_gone(readers[cycle])) return fail("reader not reaped");
        pause_seconds(2);
        snprintf(tag, sizeof(tag), "prefs-reader-exited-%d", cycle + 1);
        char *argv[] = {"launchctl", "print", "system/org.sweet.qemu.ipc-client", 0};
        const char *runs = cycle ? "runs = 2\n" : "runs = 1\n";
        if (command(tag, argv) || property_pid(output) || !strstr(output, "state = not running") ||
            !strstr(output, runs) || !strstr(output, "last exit code = 0\n"))
            return fail("reader normal exit");
        note("PREFERENCES READER cycle=%d pid=%d exit=0 ESRCH", cycle + 1, readers[cycle]);
    }
    int fd = open("/private/var/tmp/ipc-client.exit", 0x601, 0600);
    if (fd < 0 || write_all(fd, "exit\n", 5) || fsync(fd) || close(fd)) return fail("writer release");
    if (prefs_gone(writer)) return fail("writer not reaped");
    pause_seconds(2);
    if (command("prefs-writer-exited", writer_print) || property_pid(output) ||
        !strstr(output, "runs = 1\n") || !strstr(output, "last exit code = 0\n"))
        return fail("writer normal exit");
    for (int i = 0; i < 2; ++i) {
        char tag[64]; snprintf(tag, sizeof(tag), "cfprefsd-%d-after", i);
        char *argv[] = {"launchctl", "print", names[i], 0};
        if (command(tag, argv) || property_pid(output) != servers[i]) return fail("cfprefsd stability");
    }
    note("PREFERENCES CONTROL PASS writer=%d readers=%d,%d regular=%d system=%d",
         writer, readers[0], readers[1], servers[0], servers[1]);
    sync();
    for (unsigned int beat = 1;; ++beat) {
        pause_seconds(10);
        if (kill(writer, 0) == 0 || kill(readers[0], 0) == 0 || kill(readers[1], 0) == 0)
            return fail("probe restarted");
        for (int i = 0; i < 2; ++i)
            if (servers[i] && !path_matches(servers[i], "/usr/sbin/cfprefsd")) return fail("cfprefsd died");
        note("heartbeat=%u preferences_stopped=1", beat);
    }
}
