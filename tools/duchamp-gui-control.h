/* SPDX-License-Identifier: 0BSD */
static int gui_test(void) {
    const char *names[]={"gui-compositor","gui-wm","gui-red","gui-blue","gui-shell"
#if defined(DUCHAMP_LIVE_INPUT_TEST)
        ,"gui-input"
#if defined(DUCHAMP_APP_TOUCH_TEST)
        ,"gui-apps","gui-touch"
#endif
#if !defined(DUCHAMP_GUI_INTERACTIVE)
#if defined(DUCHAMP_APP_TOUCH_TEST)
        ,"app-observer"
#else
        ,"gui-live-observer"
#endif
#endif
#endif
    };
    for(unsigned i=0;i<sizeof(names)/sizeof(names[0]);i++) {
        char path[128],tag[64];snprintf(path,sizeof(path),"/sbin/duchamp-%s.plist",names[i]);
        snprintf(tag,sizeof(tag),"gui-bootstrap-%s",names[i]);
        char *args[]={"launchctl","bootstrap","system",path,0};
        if(command(tag,args))return fail("GUI job bootstrap");
    }
#if defined(DUCHAMP_GUI_INTERACTIVE)
#if defined(DUCHAMP_APP_TOUCH_TEST)
    note("GUI APP INTERACTIVE READY jobs=8 no_test_observer=1");
#else
    note("GUI LIVE INTERACTIVE READY jobs=6 no_test_observer=1");
#endif
    for(;;)pause_seconds(1);
#endif
    int ready=0;
    for(unsigned i=0;i<180;i++) {
        char data[8]={0};int fd=open(
#if defined(DUCHAMP_APP_TOUCH_TEST)
            "/private/var/tmp/apps-touch-done",
#elif defined(DUCHAMP_LIVE_INPUT_TEST)
            "/private/var/tmp/live-input-done",
#else
            "/private/var/tmp/gui-done",
#endif
            0);
        if(fd>=0){ssize_t n=read(fd,data,sizeof(data)-1);close(fd);if(n==5 && !strcmp(data,"PASS\n")){ready=1;break;}}
        pause_seconds(1);
    }
    if(!ready)return fail("GUI completion deadline");
    char *wm[]={"launchctl","print","system/org.duchamp.qemu.gui-wm",0};
    if(command("gui-manager-restarted",wm) || !strstr(output,"state = running") || !strstr(output,
#if defined(DUCHAMP_LIVE_INPUT_TEST)
        "runs = 1\n"
#else
        "runs = 2\n"
#endif
        ) || !path_matches(property_pid(output),"/sbin/duchamp-window-manager"))return fail("WM restart lifecycle");
#if defined(DUCHAMP_LIVE_INPUT_TEST)
#if defined(DUCHAMP_APP_TOUCH_TEST)
    char *input_job[]={"launchctl","print","system/org.duchamp.qemu.gui-touch",0};
    if(command("gui-touch-restarted",input_job) || !strstr(output,"state = running") || !strstr(output,"runs = 2\n") ||
       !path_matches(property_pid(output),"/sbin/duchamp-touch-input"))return fail("touch reconnect lifecycle");
#else
    char *input_job[]={"launchctl","print","system/org.duchamp.qemu.gui-input",0};
    if(command("gui-input-restarted",input_job) || !strstr(output,"state = running") || !strstr(output,"runs = 2\n") ||
       !path_matches(property_pid(output),"/sbin/duchamp-pointer-input"))return fail("input reconnect lifecycle");
#endif
#endif
    const char *jobs[]={
#if defined(DUCHAMP_LIVE_INPUT_TEST)
#if defined(DUCHAMP_APP_TOUCH_TEST)
        "app-observer","gui-touch","gui-apps",
#else
        "gui-live-observer",
#endif
        "gui-input","gui-blue",
#endif
        "gui-shell","gui-red","gui-wm","gui-compositor"};
    for(unsigned i=0;i<sizeof(jobs)/sizeof(jobs[0]);i++) {
        char target_name[128],tag[64];snprintf(target_name,sizeof(target_name),"system/org.duchamp.qemu.%s",jobs[i]);
        snprintf(tag,sizeof(tag),"gui-stop-%s",jobs[i]);
        char *args[]={"launchctl","bootout",target_name,0};if(command(tag,args))return fail("GUI job bootout");
    }
#if defined(DUCHAMP_APP_TOUCH_TEST)
    note("GUI APP TOUCH LIFECYCLE PASS touch_runs=2 bootout=9");
#elif defined(DUCHAMP_LIVE_INPUT_TEST)
    note("GUI LIVE LIFECYCLE PASS input_runs=2 bootout=7");
#else
    note("GUI LIFECYCLE PASS window_manager_runs=2 bootout=4");
#endif
    return 0;
}
