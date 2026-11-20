/* SPDX-License-Identifier: 0BSD */
static int compositor_start(void) {
    const char *names[]={"compositor","red","overlay"};
    for(unsigned i=0;i<3;i++) {
        char path[128],tag[64];
        snprintf(path,sizeof(path),"/sbin/duchamp-%s.plist",names[i]);
        snprintf(tag,sizeof(tag),"compositor-bootstrap-%s",names[i]);
        char *args[]={"launchctl","bootstrap","system",path,0};
        if(command(tag,args))return fail("compositor job bootstrap");
    }
    return 0;
}
static int compositor_normal(void) {
    const char *names[]={"compositor-normal","early-red","early-overlay"};
    for(unsigned i=0;i<3;i++) {
        char path[128],tag[64];snprintf(path,sizeof(path),"/sbin/duchamp-%s.plist",names[i]);
        snprintf(tag,sizeof(tag),"compositor-bootstrap-%s",names[i]);
        char *args[]={"launchctl","bootstrap","system",path,0};
        if(command(tag,args))return fail("normal compositor bootstrap");
    }
    int clean=0;
    for(unsigned i=0;i<45;i++) {
        int fd=open("/private/var/tmp/ipc-compositor-service.log",0);
        if(fd>=0) {
            ssize_t n=read(fd,output,sizeof(output)-1);close(fd);
            if(n>0) {
                output[n]=0;
                if(strstr(output,"FAIL"))return fail("normal compositor failed");
                const char *a=strstr(output,"DEAD role=1"),*b=strstr(output,"DEAD role=2");
                if(a && b && strstr(a,"events=0 acked=0") && strstr(b,"events=0 acked=0")){clean=1;break;}
            }
        }
        pause_seconds(1);
    }
    if(!clean)return fail("normal compositor early-client cleanup deadline");
    char *running[]={"launchctl","print","system/org.duchamp.qemu.compositor-normal",0};
    if(command("compositor-normal-running",running) || !strstr(output,"state = running") || !strstr(output,"runs = 1\n"))return fail("normal compositor survival");
    int pid=property_pid(output);
    if(!path_matches(pid,"/sbin/duchamp-compositor"))return fail("normal compositor identity");
    char *stop[]={"launchctl","bootout","system/org.duchamp.qemu.compositor-normal",0};
    if(command("compositor-normal-bootout",stop))return fail("normal compositor bootout");
    for(unsigned i=0;i<30;i++) {
        if(kill(pid,0)<0 && *__error()==3) {note("COMPOSITOR NORMAL PASS pid=%d early_cleanup=2 survived=1 gone=1",pid);return 0;}
        pause_seconds(1);
    }
    return fail("normal compositor survived bootout");
}
static int compositor_finish(void) {
    int ready=0;
    for(unsigned i=0;i<160;i++) {
        char data[8]={0};int fd=open("/private/var/tmp/compositor-done",0);
        if(fd>=0) {ssize_t n=read(fd,data,sizeof(data)-1);close(fd);if(n==5 && !strcmp(data,"PASS\n")){ready=1;break;}}
        pause_seconds(1);
    }
    if(!ready)return fail("compositor completion deadline");
    char *before[]={"launchctl","print","system/org.duchamp.qemu.compositor",0};
    if(command("compositor-running",before) || !strstr(output,"state = running") || !strstr(output,"runs = 1\n"))return fail("compositor running job");
    int pid=property_pid(output);
    if(!path_matches(pid,"/sbin/duchamp-compositor"))return fail("compositor process identity");
    char *red[]={"launchctl","print","system/org.duchamp.qemu.comp-red",0};
    char *blue[]={"launchctl","print","system/org.duchamp.qemu.comp-overlay",0};
    if(command("compositor-red-exited",red) || property_pid(output) || !strstr(output,"state = not running") || !strstr(output,"last exit code = 0"))return fail("red client exit");
    if(command("compositor-overlay-exited",blue) || property_pid(output) || !strstr(output,"state = not running"))return fail("overlay client termination");
    char *stop[]={"launchctl","bootout","system/org.duchamp.qemu.compositor",0};
    if(command("compositor-bootout",stop))return fail("compositor bootout");
    for(unsigned i=0;i<30;i++) {
        if(kill(pid,0)<0 && *__error()==3) {
            note("COMPOSITOR LIFECYCLE PASS pid=%d bootout=0 gone=1",pid);return compositor_normal();
        }
        pause_seconds(1);
    }
    return fail("compositor survived bootout");
}
