/* SPDX-License-Identifier: 0BSD */
#include <assert.h>
#include <stdio.h>
#include "duchamp-window-core.h"
#include "duchamp-app-wire.h"
static unsigned n;static struct dw_manager m;
#define T(x) do{assert(x);n++;}while(0)
int main(void) {
    struct dc_owner red={10,1},blue={11,2},reused={10,3};dg_u32 target=0;
    dw_init(&m);T(dw_create(&m,red,2,(struct dc_rect){12,16,70,44})==0);
    T(dw_create(&m,blue,3,(struct dc_rect){60,28,72,44})==0);
    T(dw_background(&m,reused,2)==DC_OWNER);T(dw_background(&m,blue,2)==DC_OWNER);
    T(dw_focus(&m,red,2)==0 && m.focus==2);T(dw_background(&m,red,2)==0 && m.focus==3 && !m.windows[1].visible);
    T(dw_touch(&m,0,1,24,38,1,&target)==0 && !target);T(dw_touch(&m,0,1,24,38,0,&target)==0);
    T(dw_focus(&m,red,2)==0 && m.windows[1].visible);
    T(dw_touch(&m,0,1,20,19,1,&target)==0 && target==2);
    T(dw_touch(&m,1,2,130,70,1,&target)==0 && target==3 && m.focus==3);
    T(m.windows[1].contacts==1 && m.windows[2].contacts==1);
    T(dw_touch(&m,0,1,34,25,2,&target)==0 && target==2);
    T(dw_touch(&m,1,2,140,74,2,&target)==0 && target==3);
    T(m.windows[1].rect.x==26 && m.windows[1].rect.y==22 && m.windows[2].rect.w==82 && m.windows[2].rect.h==48);
    T(dw_touch(&m,0,1,34,25,0,&target)==0 && !m.windows[1].contacts);
    T(dw_touch(&m,1,2,140,74,3,&target)==0 && !m.windows[2].contacts && m.windows[2].cancelled==1);
    T(dw_touch(&m,1,2,140,74,0,&target)==DC_STALE);
    T(dw_touch(&m,MT_SLOTS,1,0,0,1,&target)==DC_INVALID);
    T(dw_touch(&m,0,MT_ID_MAX+1,0,0,1,&target)==DC_INVALID);
    T(dw_touch(&m,0,1,DC_W,0,1,&target)==DC_INVALID);
    T(dw_touch(&m,0,1,40,50,1,&target)==0 && target==2);
    T(dw_touch(&m,1,1,120,50,1,&target)==DC_STALE);
    T(dw_touch(&m,0,2,40,50,2,&target)==DC_STALE);
    T(dw_destroy(&m,red,2)==0 && m.contacts[0].target==0 && m.focus==3);
    T(dw_create(&m,reused,2,(struct dc_rect){12,16,70,44})==0);
    T(dw_touch(&m,0,1,40,50,0,&target)==0 && !target && !m.windows[1].touch_events);
    T(dw_touch(&m,0,2,40,50,1,&target)==0 && target==2);
    T(dw_background(&m,reused,2)==0 && m.contacts[0].target==0 && !m.windows[1].contacts);
    T(dw_touch(&m,0,2,40,50,0,&target)==0 && !target);
    struct ap_request r={.h={.size=sizeof(r),.id=AP_MSG},.b={AP_VERSION,AP_LAUNCH,2,0,0}};
    T(ap_valid(&r));r.b.id=1;T(!ap_valid(&r));r.b.id=4;T(!ap_valid(&r));r.b.id=2;r.b.op=~0u;T(!ap_valid(&r));
    r.b.op=AP_QUERY;r.h.bits=0x80000000u;T(!ap_valid(&r));r.h.bits=0;r.h.size--;T(!ap_valid(&r));
    struct mt_report a={.version=MT_VERSION,.generation=1,.flags=MT_CONNECTED},b=a;
    b.flags=MT_REPORT;b.sequence=1;b.changed=b.active=1;b.contacts[0]=(struct mt_contact){1,100,200,1};T(mt_follows(&a,&b));
    struct mt_report c=b;c.sequence=2;c.changed=0;c.contacts[0].x++;T(!mt_follows(&b,&c));
    c=b;c.sequence=2;c.changed=1;c.contacts[0].id=2;T(!mt_follows(&b,&c));
    c=b;c.sequence=2;c.generation=2;T(!mt_follows(&b,&c));c=b;T(!mt_follows(&b,&c));
    c=b;c.sequence=2;c.flags=MT_REPORT|MT_CANCEL;c.active=0;c.contacts[0].active=0;T(mt_follows(&b,&c));
    printf("PASS %u application/touch ownership assertions\n",n);return 0;
}
