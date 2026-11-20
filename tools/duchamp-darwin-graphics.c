/* SPDX-License-Identifier: 0BSD */
/* QEMU-only userspace integration probe; no private Apple frameworks or GPU. */
#include "duchamp-darwin-iokit.h"
static int bad(const char *step,int rc) {ipc_note("FAIL %s result=0x%x",step,rc);return 1;}
enum {WIDTH=64,HEIGHT=32,X=160,Y=1600};
int main(void) {
    if(ipc_identity("darwin-gfx"))return 1;
    ipc_note("DYNAMIC images=%u",_dyld_image_count());
    dg_u32 master=0,fbservice=0,surfservice=0,hidservice=0,touchservice=0;
    int rc=host_get_io_main(mach_host_self(),&master);
    if(rc || !master)return bad("IOMainPort",rc);
    ipc_note("IOMAIN port=0x%x",master);
    for(int retry=0;retry<20;retry++) {
        fbservice=match(master,"AppleCLCD");if(fbservice)break;sleep(1);
    }
    surfservice=match(master,"IOCoreSurfaceRoot");hidservice=match(master,"SweetHIDButtons");touchservice=match(master,"SweetHIDTouch");
    if(!fbservice || !surfservice || !hidservice || !touchservice)return bad("service matching",-1);
    if(match(master,"DuchampDeliberatelyAbsentService"))return bad("absent service matched",-1);
    ipc_note("MATCH AppleCLCD IOCoreSurfaceRoot SweetHIDButtons SweetHIDTouch; absent rejected");
    dg_u32 fb=open_client(fbservice,0),surface=open_client(surfservice,0),hid=open_client(hidservice,0x65737563);
    if(!fb || !surface || !hid)return bad("user client open",-1);
    dg_u64 display[2]={0};dg_u32 count=2;
    rc=method(fb,8,0,0,0,0,0,0,display,&count);
    if(rc || count!=2 || display[0]!=1220 || display[1]!=2712)return bad("display geometry",rc);
    ipc_note("DISPLAY width=%llu height=%llu",display[0],display[1]);
    void *queue=0;dg_u64 queue_bytes=0;dg_u32 port=0;
    rc=map_queue(hid,&queue,&queue_bytes);if(rc)return bad("HID queue map",rc);
    if(mach_port_allocate(mach_task_self_,1,&port) || notify(hid,port))return bad("HID notify",-1);
    dg_u64 options=0;rc=method(hid,0,&options,1,0,0,0,0,0,0);if(rc)return bad("HID open",rc);
    dg_u64 previous=0,sender=0;unsigned events=0,notifications=0;
    for(unsigned attempt=0;attempt<18 && events<2;attempt++) {
        struct dg_event e;int got;
        while((got=dg_queue_pop(queue,queue_bytes,&e))>0) {
            if(e.type!=3 || e.usage_page!=12 || e.usage!=0x40 || !e.sender || !e.timestamp ||
               e.timestamp<previous || e.down!=(events%2==0) || (sender && sender!=e.sender))return bad("HID event order",-1);
            previous=e.timestamp;sender=e.sender;events++;
            ipc_note("INPUT event=%u down=%u sender=%llu timestamp=%llu",events,e.down,e.sender,e.timestamp);
        }
        if(got<0)return bad("HID queue bounds",got);
        dg_u8 packet[128];rc=mach_msg(packet,2|0x100,0,sizeof(packet),port,1000,0);
        if(!rc)notifications++;
        else if(rc!=0x10004003)return bad("HID notification receive",rc);
    }
    if(events<2 || !notifications)return bad("HID timeout",-1);
    ipc_note("INPUT PASS events=%u notifications=%u",events,notifications);
    static const char xml[]="<dict><key>IOSurfaceWidth</key><integer>64</integer><key>IOSurfaceHeight</key><integer>32</integer>"
        "<key>IOSurfaceBytesPerElement</key><integer>4</integer><key>IOSurfaceBytesPerRow</key><integer>256</integer>"
        "<key>IOSurfaceAllocSize</key><integer>8192</integer><key>IOSurfacePixelFormat</key><integer>1111970369</integer></dict>";
    dg_u8 description[0xa68];dg_u32 bytes=sizeof(description);
    rc=method(surface,0,0,0,xml,sizeof(xml),description,&bytes,0,0);
    if(rc || bytes!=sizeof(description))return bad("IOSurface create",rc);
    dg_u32 id=dg_get32(description+24),bpr=dg_get32(description+40);
    dg_u32 *pixels=(void *)(unsigned long)dg_get64(description);
    if(!id || !pixels || bpr!=WIDTH*4 || dg_get32(description+28)<WIDTH*HEIGHT*4)return bad("surface bounds",-1);
    for(dg_u32 y=0;y<HEIGHT;y++)for(dg_u32 x=0;x<WIDTH;x++)
        pixels[y*WIDTH+x]=0xff000000u|((x*4)<<16)|((y*8)<<8)|((x*13+y*7)&255);
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
    dg_u64 swap=0;count=1;rc=method(fb,4,0,0,0,0,0,0,&swap,&count);
    if(rc || !swap)return bad("SwapBegin",rc);
    dg_u8 record[0x46c]={0};dg_put32(record+0x50,(dg_u32)swap);dg_put32(record+0x54,id);
    dg_put32(record+0x64+8,WIDTH);dg_put32(record+0x64+12,HEIGHT);
    dg_put32(record+0xc4,X);dg_put32(record+0xc4+4,Y);dg_put32(record+0xc4+8,WIDTH);dg_put32(record+0xc4+12,HEIGHT);dg_put32(record+0x104,1);
    rc=method(fb,5,0,0,record,sizeof(record),0,0,0,0);if(rc)return bad("SwapEnd",rc);
    ipc_note("FRAME swap=%llu surface=%u rect=%d,%d,%d,%d",swap,id,X,Y,WIDTH,HEIGHT);
    int fd=open("/private/var/tmp/duchamp-graphics-witness",0x601,0600);
    char witness[256];int n=snprintf(witness,sizeof(witness),"pid=%d\nppid=%d\nimages=%u\ninput_events=%u\nnotifications=%u\nsurface=%u\nswap=%llu\n",getpid(),getppid(),_dyld_image_count(),events,notifications,id,swap);
    if(fd<0 || ipc_write_all(fd,witness,(size_t)n) || fsync(fd) || close(fd))return bad("var witness",-1);
    ipc_note("PASS Darwin IOKit framebuffer and HID queue");
    for(;;) {usleep(100000);if(method(fb,5,0,0,record,sizeof(record),0,0,0,0))return bad("repeat present",-1);}
}
