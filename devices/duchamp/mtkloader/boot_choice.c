#include "boot_choice.h"
static uint32_t little(const volatile uint8_t *p) {
    return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;
}
int duchamp_take_xnu_request(volatile void *buffer,size_t bytes,const struct duchamp_boot_choice_access *access) {
    /* Default Android, without dereferencing the proposed buffer. */
    if(!access || access->readable!=1 || access->writable!=1 || access->retained!=1 ||
       access->cache_publication_ready!=1 || access->android_fallback_ready!=1)
        return DUCHAMP_CHOICE_ANDROID;
    if(!buffer || bytes<64 || bytes>65536)return DUCHAMP_CHOICE_INVALID;
    volatile uint8_t *p=buffer;
    const uint32_t cap=(uint32_t)bytes-12,end=little(p+4),size=little(p+8);
    if(little(p)!=0x43474244 || end>=cap || size>cap || (size<cap && size!=end))
        return DUCHAMP_CHOICE_INVALID;
    static const char request[]="\nDUCHAMP:BOOT-XNU-ONCE\n";
    const unsigned length=sizeof(request)-1;
    if(size<length)return DUCHAMP_CHOICE_ANDROID;
    const uint32_t start=(end+cap-size)%cap;
    int found=0;
    for(uint32_t pos=0;pos<=size-length;pos++) {
        unsigned i=0;
        while(i<length && p[12+(start+pos+i)%cap]==(uint8_t)request[i])i++;
        if(i==length) {p[12+(start+pos+1)%cap]='!';found=1;}
    }
    /* Publication/cleaning belongs to a verified caller. This routine cannot
     * arm a physical one-shot boot or guarantee persistence across reset.
     */
    return found?DUCHAMP_CHOICE_XNU_ONCE:DUCHAMP_CHOICE_ANDROID;
}
