/* SPDX-License-Identifier: 0BSD */
extern int dup2(int,int);
static int app_exit_record(const char *label,const char *name) {
    char target[96],path[96];snprintf(target,sizeof(target),"system/org.duchamp.qemu.%s",label);
    snprintf(path,sizeof(path),"/private/var/tmp/app-exit-%s.log",name);
    int fd=open(path,0x601,0600);if(fd<0)return -1;
    int child=fork();if(child<0){close(fd);return -1;}
    if(!child){if(dup2(fd,1)<0 || dup2(fd,2)<0)_exit(126);close(fd);char *args[]={"launchctl","print",target,0};execve("/bin/launchctl",args,*_NSGetEnviron());_exit(127);}
    close(fd);int status=0;if(waitpid(child,&status,0)!=child || status)return -1;
    ipc_note("EXIT RECORD %s launchctl_print_exit=0",name);return 0;
}
static int app_phase(unsigned phase) {
    char data[24];int n=snprintf(data,sizeof(data),"%u\n",phase),fd=open("/private/var/tmp/app-stage",0x601,0600);
    if(fd<0 || ipc_write_all(fd,data,(size_t)n) || fsync(fd) || close(fd))return -1;
    ipc_note("PHASE %u",phase);if(phase!=1)sleep(8);return 0;
}
static int app_observer(void) {
    if(ipc_identity("app-observer"))return 1;
    dg_u32 applications=lookup(AP_SERVICE),manager=lookup(GW_SERVICE);struct gw_identity red,blue,old_red,old_blue;
    if(!applications || !manager)return failure("observer services",-1);
    if(app_action(applications,AP_LAUNCH,2) || app_action(applications,AP_LAUNCH,3) ||
       ap_rpc(applications,AP_QUERY,2,(struct dc_owner){0},&red) || ap_rpc(applications,AP_QUERY,3,(struct dc_owner){0},&blue) ||
       red.pid<=1 || blue.pid<=1 || red.pid==blue.pid || !red.birth || !blue.birth)return failure("real app processes",-1);
    old_red=red;old_blue=blue;ipc_note("PASS PROCESS_IDENTITIES red=%u/%u blue=%u/%u",red.pid,red.birth,blue.pid,blue.birth);
    struct gw_identity invalid;
    if(ap_rpc(applications,AP_FOREGROUND,2,(struct dc_owner){red.pid,red.birth+1},&invalid)!=DC_STALE)return failure("PID version binding",-1);
    ipc_note("PASS PID_VERSION_BINDING same_pid_wrong_birth_denied=1");
    if(app_action(applications,AP_FOREGROUND,2) || app_action(applications,AP_BACKGROUND,2) ||
       ap_rpc(applications,AP_QUERY,2,(struct dc_owner){0},&red) || red.visible || red.state!=1 || red.pid!=old_red.pid ||
       ap_rpc(applications,AP_QUERY,3,(struct dc_owner){0},&blue) || blue.state!=2 ||
       app_action(applications,AP_FOREGROUND,2))return failure("foreground background",-1);
    ipc_note("PASS FOREGROUND_BACKGROUND same_process=1 focus_restored=3");if(app_phase(1))return 1;
    unsigned observed_two=0,ready=0;
    for(unsigned tick=0;tick<1000;tick++) {
        struct gw_result a,b;
        if(ap_rpc(applications,AP_QUERY,2,(struct dc_owner){0},&red) || ap_rpc(applications,AP_QUERY,3,(struct dc_owner){0},&blue) ||
           gw_rpc(manager,(struct gw_body){.op=GW_QUERY,.id=2},0,0,&a) || gw_rpc(manager,(struct gw_body){.op=GW_QUERY,.id=3},0,0,&b))return failure("touch observation",-1);
        if(red.contacts==1 && blue.contacts==1)observed_two=1;
        if(observed_two && a.x==26 && a.y==22 && a.w==70 && a.h==44 && b.w==82 && b.h==48 &&
           !red.contacts && !blue.contacts && red.touch_events>=3 && blue.touch_events>=3){ready=1;break;}
        usleep(100000);
    }
    if(!ready)return failure("simultaneous touch geometry",-1);
    ipc_note("PASS TWO_CONTACTS separate_targets=2,3 drag=26,22 resize=82,48");if(app_phase(2))return 1;
    ready=0;
    for(unsigned tick=0;tick<1000;tick++) {
        if(ap_rpc(applications,AP_QUERY,2,(struct dc_owner){0},&red) || ap_rpc(applications,AP_QUERY,3,(struct dc_owner){0},&blue))return 1;
        if(red.contacts==1 && blue.contacts==1){ready=1;break;}usleep(100000);
    }
    if(!ready || launch("kickstart","gui-touch"))return failure("touch reconnect request",-1);
    ready=0;
    for(unsigned tick=0;tick<1000;tick++) {
        if(ap_rpc(applications,AP_QUERY,2,(struct dc_owner){0},&red) || ap_rpc(applications,AP_QUERY,3,(struct dc_owner){0},&blue))return 1;
        if(!red.contacts && !blue.contacts && red.cancelled && blue.cancelled){ready=1;break;}usleep(100000);
    }
    if(!ready)return failure("cancel on input death",-1);
    ipc_note("PASS CANCEL_DELIVERED red=%u blue=%u",red.cancelled,blue.cancelled);if(app_phase(3))return 1;
    if(app_action(applications,AP_BACKGROUND,3))return 1;
    ipc_note("PASS BACKGROUND blue_pid=%u retained=1",blue.pid);if(app_phase(4))return 1;
    if(app_action(applications,AP_FOREGROUND,3) || app_phase(5))return 1;
    if(app_action(applications,AP_TERMINATE,3) || ap_rpc(applications,AP_QUERY,2,(struct dc_owner){0},&red) || red.state!=2)return failure("graceful exit focus",-1);
    if(app_exit_record("gui-blue","blue"))return failure("graceful exit receipt",-1);
    ipc_note("PASS GRACEFUL_EXIT old_blue=%u focus_restored=2",old_blue.pid);if(app_phase(6))return 1;
    if(app_action(applications,AP_LAUNCH,3) || ap_rpc(applications,AP_QUERY,3,(struct dc_owner){0},&blue) ||
       blue.pid==old_blue.pid || blue.birth==old_blue.birth ||
       ap_rpc(applications,AP_BACKGROUND,3,(struct dc_owner){old_blue.pid,old_blue.birth},&old_blue)!=DC_STALE)return failure("stale app handle",-1);
    ipc_note("PASS RESTART new_blue=%u/%u stale_handle_rejected=1",blue.pid,blue.birth);if(app_phase(7))return 1;
    ready=0;
    for(unsigned tick=0;tick<1000;tick++) {
        if(ap_rpc(applications,AP_QUERY,2,(struct dc_owner){0},&red))return 1;
        if(red.contacts==1){ready=1;break;}usleep(100000);
    }
    if(!ready || app_action(applications,AP_CRASH,2))return failure("actual app abort",-1);
    if(app_exit_record("gui-red","red"))return failure("crash exit receipt",-1);
    ipc_note("PASS CRASH_EXIT old_red=%u expected_signal=SIGABRT",old_red.pid);if(app_phase(8))return 1;
    if(app_action(applications,AP_LAUNCH,2) || ap_rpc(applications,AP_QUERY,2,(struct dc_owner){0},&red) ||
       red.pid==old_red.pid || red.birth==old_red.birth || red.touch_events ||
       ap_rpc(applications,AP_FOREGROUND,2,(struct dc_owner){old_red.pid,old_red.birth},&old_red)!=DC_STALE)return failure("crash restart identity",-1);
    ipc_note("PASS CRASH_RESTART new_red=%u/%u old_capture_detached=1",red.pid,red.birth);if(app_phase(9))return 1;
    ready=0;
    for(unsigned tick=0;tick<1000;tick++) {
        if(ap_rpc(applications,AP_QUERY,2,(struct dc_owner){0},&red))return 1;
        if(red.touch_events==2 && !red.contacts){ready=1;break;}
        if(red.touch_events>2)return failure("stale capture reached new process",-1);usleep(100000);
    }
    if(!ready)return failure("new contact after restart",-1);
    ipc_note("PASS NEW_CONTACT_ONLY delivered=2 old_release_not_delivered=1");if(app_phase(10))return 1;
    if(app_action(applications,AP_TERMINATE,2) || app_action(applications,AP_TERMINATE,3) || app_phase(11))return 1;
    if(app_action(applications,AP_LAUNCH,2) || app_action(applications,AP_LAUNCH,3) || app_phase(12))return 1;
    int fd=open("/private/var/tmp/apps-touch-done",0x601,0600);
    if(fd<0 || ipc_write_all(fd,"PASS\n",5) || fsync(fd) || close(fd))return failure("app test witness",-1);
    ipc_note("PASS APPS_TOUCH_COMPLETE launchd_pid1=1");for(;;)sleep(1);
}
