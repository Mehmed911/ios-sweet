#include "sweet-ipc.h"
#if defined(SWEET_NOTIFYD_TEST)
#include "sweet-notify.h"
#endif
static char asl_output[32768];
static int asl_read(const char *path, char *data, size_t capacity) {
    int fd = open(path, 0); if (fd < 0) return -1;
    size_t at = 0;
    while (at < capacity - 1) {
        ssize_t n = read(fd, data + at, capacity - 1 - at);
        if (n < 0 && *__error() == 4) continue;
        if (n < 0) { close(fd); return -1; }
        if (!n) break;
        at += (size_t)n;
    }
    data[at] = 0; close(fd);
    return at == capacity - 1 ? -1 : 0;
}
static int asl_gate(const char *path, const char *token) {
    int fd = open(path, 0x601, 0600); if (fd < 0) return -1;
    int error = write_all(fd, token, strlen(token)) || fsync(fd);
    if (close(fd)) error = 1;
    return error ? -1 : 0;
}
static int asl_received(int id, int seq, int pid) {
    char token[80], identity[40], sender[48], client[32], sequence[32];
    snprintf(token, sizeof(token), "[Message SWEET_SYSLOGD_C%d_S%d_20F66]", id, seq);
    snprintf(identity, sizeof(identity), "[PID %d]", pid);
    snprintf(sender, sizeof(sender), "[Sender sweet-asl%d]", id);
    snprintf(client, sizeof(client), "[SweetClient %d]", id);
    snprintf(sequence, sizeof(sequence), "[SweetSequence %d]", seq);
    const char *start = asl_output;
    while (*start) {
        const char *end = strchr(start, '\n');
        size_t length = end ? (size_t)(end - start) : strlen(start);
        if (length < 4096) {
            char line[4096]; for (size_t i = 0; i < length; ++i) line[i] = start[i];
            line[length] = 0;
            if (strstr(line, token) && strstr(line, identity) && strstr(line, sender) &&
                strstr(line, client) && strstr(line, sequence) && strstr(line, "[UID 0]") &&
                strstr(line, "[GID 0]") && strstr(line, "[Facility local0]") &&
                strstr(line, "[SweetFixture syslogd-qemu]")) return 1;
        }
        if (!end) break;
        start = end + 1;
    }
    return 0;
}
static int syslogd_lifecycle(void) {
    const char *service = "system/com.apple.syslogd";
    const char *scenario = "syslogd";
#if defined(SWEET_NOTIFYD_TEST)
    scenario = "notifyd";
    int notification_server = -1, remote_token = -1;
#endif
    note("SCENARIO %s", scenario);
    int server = -1, probes[2] = {-1, -1};
    for (int i = 0; i < 300; ++i) {
        server = ipc_read_pid("/private/var/run/syslog.pid");
        probes[0] = ipc_read_pid("/private/var/tmp/asl-probe1.pid");
        probes[1] = ipc_read_pid("/private/var/tmp/asl-probe2.pid");
        if (probes[0] != probes[1] && path_matches(server, "/usr/sbin/syslogd") &&
            path_matches(probes[0], "/sbin/sweet-launchd-service") &&
            path_matches(probes[1], "/sbin/sweet-ipc-client") &&
            !asl_read("/private/var/tmp/syslogd-debug.log", asl_output, sizeof(asl_output)) &&
            strstr(asl_output, "starting work queue")
#if defined(SWEET_NOTIFYD_TEST)
            && nfy_exists("ready", 1) && nfy_exists("ready", 2)
#endif
            ) break;
        server = probes[0] = probes[1] = -1; pause_seconds(1);
    }
    if (server <= 1) return fail("syslogd/probe readiness");
    char *before[] = {"launchctl", "print", (char *)service, 0};
    if (command("syslogd-before", before) || property_pid(output) != server ||
        !strstr(output, "state = running") || !strstr(output, "runs = 1\n") ||
        !strstr(output, "com.apple.system.logger")) return fail("syslogd initial print");
    note("SYSLOGD READY server=%d clients=%d,%d original=/usr/sbin/syslogd", server, probes[0], probes[1]);
#if defined(SWEET_NOTIFYD_TEST)
    char *notify_print[] = {"launchctl", "print", "system/com.apple.notifyd", 0};
    if (command("notifyd-before", notify_print) || !strstr(output, "state = running") ||
        !strstr(output, "runs = 1\n") || !strstr(output, "com.apple.system.notification_center"))
        return fail("notifyd initial print");
    notification_server = property_pid(output);
    if (!path_matches(notification_server, "/usr/sbin/notifyd")) return fail("notifyd executable");
    note("NOTIFYD READY server=%d clients=%d,%d", notification_server, probes[0], probes[1]);
    if (nfy_mark("begin", 0) || nfy_wait("done", 1) || nfy_wait("done", 2))
        return fail("notify notification/cancel test");
    unsigned long long remote_state = 0;
    if (notify_register_plain("com.apple.system.syslog.master", &remote_token) ||
        notify_set_state(remote_token, 0x300ff) || notify_get_state(remote_token, &remote_state) ||
        remote_state != 0x300ff || notify_post("com.apple.asl.remote"))
        return fail("ASL remote master setup");
    note("ASL REMOTE MASTER state=0x%llx notifyd=%d", remote_state, notification_server);
#endif
    if (asl_gate("/private/var/tmp/asl-probes.begin", "begin\n")) return fail("ASL begin gate");
    int received = 0;
    for (int poll = 0; poll < 300; ++poll) {
        if (!path_matches(server, "/usr/sbin/syslogd")) return fail("syslogd exited during receive");
        int complete = !asl_read("/private/var/log/sweet-asl.log", asl_output, sizeof(asl_output));
        for (int id = 1; id <= 2; ++id)
            for (int seq = 1; seq <= 3; ++seq) complete &= asl_received(id, seq, probes[id - 1]);
        if (complete && ipc_read_pid("/private/var/tmp/asl-probe1.done") == probes[0] &&
            ipc_read_pid("/private/var/tmp/asl-probe2.done") == probes[1]) { received = 1; break; }
        pause_seconds(1);
    }
    if (!received) return fail("six authenticated ASL messages not received");
    note("SYSLOGD RECEIVED server=%d clients=%d,%d messages=6", server, probes[0], probes[1]);
#if defined(SWEET_NOTIFYD_TEST)
    if (notify_set_state(remote_token, 0) || notify_get_state(remote_token, &remote_state) ||
        remote_state || notify_post("com.apple.asl.remote") || notify_cancel(remote_token))
        return fail("ASL remote master cleanup");
    note("ASL REMOTE MASTER restored=0 token_cancelled=1");
#endif
    if (asl_gate("/private/var/tmp/asl-probes.exit", "exit\n")) return fail("ASL exit gate");
    for (int id = 1; id <= 2; ++id) {
        int gone = 0;
        for (int i = 0; i < 120; ++i) {
            if (kill(probes[id - 1], 0) < 0 && *__error() == 3) { gone = 1; break; }
            pause_seconds(1);
        }
        if (!gone) return fail("ASL probe not reaped");
        char *job = id == 1 ? "system/org.sweet.qemu.c-service" : "system/org.sweet.qemu.ipc-client";
        char tag[32]; snprintf(tag, sizeof(tag), "syslogd-probe%d-exited", id);
        char *args[] = {"launchctl", "print", job, 0};
        if (command(tag, args) || property_pid(output) || !strstr(output, "state = not running") ||
            !strstr(output, "runs = 1\n") || !strstr(output, "last exit code = 0")) return fail("probe normal exit");
    }
    if (command("syslogd-after", before) || property_pid(output) != server ||
        !strstr(output, "state = running") || !strstr(output, "runs = 1\n")) return fail("syslogd final print");
#if defined(SWEET_NOTIFYD_TEST)
    if (command("notifyd-after", notify_print) || property_pid(output) != notification_server ||
        !strstr(output, "state = running") || !strstr(output, "runs = 1\n")) return fail("notifyd final print");
    note("NOTIFYD CONTROL PASS server=%d syslogd=%d clients=%d,%d", notification_server, server, probes[0], probes[1]);
#endif
    note("SYSLOGD CONTROL PASS server=%d clients=%d,%d messages=6", server, probes[0], probes[1]);
    sync();
    for (unsigned int beat = 1;; ++beat) {
        pause_seconds(10);
        if (!path_matches(server, "/usr/sbin/syslogd")) return fail("syslogd lost");
#if defined(SWEET_NOTIFYD_TEST)
        if (!path_matches(notification_server, "/usr/sbin/notifyd")) return fail("notifyd lost");
#endif
        for (int i = 0; i < 2; ++i)
            if (!kill(probes[i], 0) || *__error() != 3) return fail("ASL probe restarted");
        note("heartbeat=%u syslogd_running=1 server=%d probes_stopped=1", beat, server);
    }
}
