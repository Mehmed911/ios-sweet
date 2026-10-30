/* Host-only control-flow model for the actual extracted qu_read()/qu_error().
 * It does not model XNU VM/PAN or prove a kernel ABI; the guest test does.
 */
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/sysmacros.h>
#include "../drivers/ufs_readonly.h"
#define __unused __attribute__((unused))
#define PAGE_SIZE 16384u
#define KMA_DATA 0
#define VM_KERN_MEMORY_IOKIT 0
#define KERN_SUCCESS 0
#define MIN(a,b) ((a)<(b)?(a):(b))
typedef uintptr_t vm_offset_t;
struct uio { int64_t offset,residual; size_t copied; uint8_t data[65536]; };
static struct { int ready; uint64_t bytes; uint32_t physical_bytes; struct dufs_host host; } qu;
static int qu_lock,held,alloc_fail,allocations,frees,read_calls,fail_read;
static int64_t copy_fault_after;
static void *kernel_map;
static unsigned checks;
#define CHECK(v) do { checks++; assert(v); } while(0)
static int64_t uio_offset(struct uio *u) { return u->offset; }
static int64_t uio_resid(struct uio *u) { return u->residual; }
static void lck_mtx_lock(int *lock) { (void)lock; assert(!held); held=1; }
static void lck_mtx_unlock(int *lock) { (void)lock; assert(held); held=0; }
static int kmem_alloc(void *map,vm_offset_t *out,size_t n,int flags,int tag) {
    (void)map;(void)flags;(void)tag; assert(!held);
    if(alloc_fail) return 1;
    *out=(uintptr_t)malloc(n); assert(*out); allocations++; return 0;
}
static void kmem_free(void *map,vm_offset_t p,size_t n) {
    (void)map;(void)n; assert(!held); frees++; free((void *)p);
}
static uint8_t byte_at(uint64_t pos) { return (uint8_t)(pos*131+(pos/4096)*17); }
int dufs_read(struct dufs_host *h,uint64_t lba,uint32_t blocks,void *data,size_t n) {
    (void)h; assert(held && blocks && n==(size_t)blocks*4096 && n<=PAGE_SIZE);
    if(++read_calls==fail_read) return DUFS_TIMEOUT;
    for(size_t i=0;i<n;i++) ((uint8_t *)data)[i]=byte_at(lba*4096+i);
    return 0;
}
static int uiomove(void *source,int amount,struct uio *u) {
    assert(!held && amount>0 && amount<=u->residual);
    size_t n=(size_t)amount;
    if(copy_fault_after>=0 && u->copied+n>(uint64_t)copy_fault_after)
        n=(size_t)copy_fault_after-u->copied;
    memcpy(u->data+u->copied,source,n);
    u->offset+=(int64_t)n; u->residual-=(int64_t)n; u->copied+=n;
    return n==(size_t)amount?0:EFAULT;
}
#include "adapter-functions.inc"
static void reset(struct uio *u,int64_t offset,int64_t bytes) {
    memset(u,0,sizeof(*u)); memset(u->data,0xa5,sizeof(u->data));
    u->offset=offset; u->residual=bytes;
    qu.ready=1; qu.bytes=1024*1024; qu.physical_bytes=4096;
    held=alloc_fail=allocations=frees=read_calls=fail_read=0; copy_fault_after=-1;
}
static void data_matches(struct uio *u,uint64_t start,size_t n) {
    for(size_t i=0;i<n;i++) assert(u->data[i]==byte_at(start+i));
    for(size_t i=n;i<sizeof(u->data);i++) assert(u->data[i]==0xa5);
    CHECK(1);
}
int main(void) {
    struct uio u;
    reset(&u,513,40000);
    CHECK(qu_read(0,&u,0)==0 && !u.residual && u.copied==40000);
    CHECK(read_calls==3 && allocations==1 && frees==1 && !held);
    data_matches(&u,513,40000);
    reset(&u,3,40000); copy_fault_after=5000;
    CHECK(qu_read(0,&u,0)==EFAULT && u.offset==5003 && u.residual==35000);
    CHECK(frees==1 && read_calls==1 && !held); data_matches(&u,3,5000);
    reset(&u,3,40000); fail_read=2;
    CHECK(qu_read(0,&u,0)==ETIMEDOUT && u.copied==PAGE_SIZE-3);
    CHECK(u.residual==40000-(PAGE_SIZE-3) && frees==1 && !held);
    data_matches(&u,3,PAGE_SIZE-3);
    reset(&u,1024*1024-17,100);
    CHECK(qu_read(0,&u,0)==0 && u.copied==17 && u.residual==83);
    CHECK(read_calls==1 && frees==1 && !held); data_matches(&u,1024*1024-17,17);
    reset(&u,1024*1024,1);
    CHECK(qu_read(0,&u,0)==0 && !read_calls && frees==1 && !held);
    reset(&u,-1,1); CHECK(qu_read(0,&u,0)==EINVAL && !allocations);
    reset(&u,0,-1); CHECK(qu_read(0,&u,0)==EINVAL && !allocations);
    reset(&u,0,0); CHECK(qu_read(0,&u,0)==0 && !allocations);
    reset(&u,0,10); alloc_fail=1;
    CHECK(qu_read(0,&u,0)==ENOMEM && !read_calls && !frees && !held);
    reset(&u,0,10); qu.ready=0; CHECK(qu_read(0,&u,0)==ENXIO && !allocations);
    printf("%u adapter UIO model checks passed; no XNU VM/PAN emulation\n",checks);
    return 0;
}
