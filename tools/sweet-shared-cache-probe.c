/* The declarations match Apple dyld-1066.8 dyld{,_priv}.h and Darwin libc.
 * No SDK, derived framework export, container RPC or GPU is used here.
 */
typedef unsigned long size_t;
typedef unsigned long uintptr_t;
typedef unsigned int u32;
extern int printf(const char *, ...), fflush(void *), getpid(void), getppid(void);
extern unsigned int sleep(unsigned int);
extern int memcmp(const void *,const void *,size_t), strcmp(const char *,const char *);
extern _Bool _dyld_get_shared_cache_uuid(unsigned char[16]);
extern const void *_dyld_get_shared_cache_range(size_t *);
extern _Bool _dyld_shared_cache_contains_path(const char *);
extern unsigned int _dyld_image_count(void);
extern const char *_dyld_get_image_name(unsigned int);
extern const void *_dyld_get_image_header(unsigned int);
extern void *dlopen(const char *,int), *dlsym(void *,const char *);
extern const char *dlerror(void);

static const char *paths[]={
    "/System/Library/PrivateFrameworks/ContainerManagerCommon.framework/ContainerManagerCommon",
    "/System/Library/PrivateFrameworks/CacheDelete.framework/CacheDelete"
};
static const unsigned char expected_uuid[16]={
    0xe5,0x42,0x0d,0xb3,0x30,0xd0,0x33,0xaa,0x8b,0x7e,0x05,0xb5,0x03,0x8b,0xb4,0x6d
};

__attribute__((noreturn)) static void finish(int status,const char *step) {
    printf("SWEET SHARED CACHE: %s step=%s\n",status?"FAIL":"PASS",step);
    fflush(0);
    for (;;) sleep(60);
}

int main(void) {
    unsigned char uuid[16]={0};
    size_t length=0;
    printf("SWEET SHARED CACHE: DYNAMIC MAIN pid=%d ppid=%d\n",getpid(),getppid()); fflush(0);
    if (getpid()<=1 || getppid()!=1) finish(1,"child-of-static-pid1");
    if (!_dyld_get_shared_cache_uuid(uuid) || memcmp(uuid,expected_uuid,16))
        finish(1,"cache-uuid");
    printf("SWEET SHARED CACHE: UUID ");
    for (int i=0;i<16;i++) printf("%02X",uuid[i]);
    printf("\n"); fflush(0);
    const void *base=_dyld_get_shared_cache_range(&length);
    if (!base || !length) finish(1,"cache-range");
    printf("SWEET SHARED CACHE: RANGE base=%p bytes=%lu\n",base,length); fflush(0);
    for (int p=0;p<2;p++) {
        if (!_dyld_shared_cache_contains_path(paths[p])) finish(1,"path-not-in-cache");
        printf("SWEET SHARED CACHE: PRE DLOPEN index=%d\n",p); fflush(0);
        void *handle=dlopen(paths[p],2); /* RTLD_NOW */
        if (!handle) {
            printf("SWEET SHARED CACHE: dlerror=%s\n",dlerror());
            finish(1,"dlopen");
        }
        const u32 *header=0;
        for (unsigned int i=0;i<_dyld_image_count();i++) {
            const char *name=_dyld_get_image_name(i);
            if (name && !strcmp(name,paths[p])) header=_dyld_get_image_header(i);
        }
        uintptr_t offset=(uintptr_t)header-(uintptr_t)base;
        if (!header || length<32 || offset>length-32 || header[0]!=0xfeedfacf ||
            !(header[6]&0x80000000u)) finish(1,"image-not-mapped-from-cache");
        /* Exercise original Objective-C metadata after cache initializers.
         * Class names were observed in these exact cache images. Never call
         * a recovered private C++/Objective-C method using a guessed ABI.
         */
        typedef void *(*get_class_fn)(const char *);
        typedef const char *(*class_name_fn)(void *);
        get_class_fn get_class=(get_class_fn)dlsym(handle,"objc_getClass");
        class_name_fn class_name=(class_name_fn)dlsym(handle,"class_getName");
        const char *name=p==0?"MCMError":"CDRecentInfo";
        void *cls=get_class?get_class(name):0;
        const char *observed=cls && class_name?class_name(cls):0;
        if (!observed || strcmp(observed,name)) finish(1,"objc-class");
        printf("SWEET SHARED CACHE: FRAMEWORK index=%d incache=1 class=%s\n",p,observed);
        fflush(0);
    }
    finish(0,"uuid-range-frameworks-objc");
}
