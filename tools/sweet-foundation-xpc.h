/* Foundation objects are serialized explicitly as JSON in native XPC data. */
#ifndef SWEET_FOUNDATION_XPC_H
#define SWEET_FOUNDATION_XPC_H
#include "sweet-foundation-api.h"
extern void xpc_dictionary_set_data(sweet_xpc_t, const char *, const void *, size_t);
extern const void *xpc_dictionary_get_data(sweet_xpc_t, const char *, size_t *);
static inline NSString *fnd_string(const char *text) { return [NSString stringWithUTF8String:text]; }
static inline int fnd_number(NSDictionary *dict, const char *key, int expected) {
    id value = [dict objectForKey:fnd_string(key)];
    return [value isKindOfClass:[NSNumber class]] && [(NSNumber *)value intValue] == expected;
}
static inline int fnd_device(NSDictionary *dict, const char *expected) {
    id value = [dict objectForKey:fnd_string("device")];
    return [value isKindOfClass:[NSString class]] && !strcmp([(NSString *)value UTF8String], expected);
}
static inline NSData *fnd_encode(NSDictionary *dict) {
    NSError *error = 0;
    NSData *data = [NSJSONSerialization dataWithJSONObject:dict options:0 error:&error];
    return data && !error && [data length] > 0 && [data length] <= 4096 ? data : 0;
}
static inline NSDictionary *fnd_decode(sweet_xpc_t message, NSData **data) {
    size_t length = 0;
    const void *bytes = xpc_dictionary_get_data(message, "foundation-json", &length);
    if (!bytes || !length || length > 4096) return 0;
    *data = [NSData dataWithBytes:bytes length:length];
    NSError *error = 0;
    id value = [NSJSONSerialization JSONObjectWithData:*data options:0 error:&error];
    return !error && [value isKindOfClass:[NSDictionary class]] ? value : 0;
}
static inline int fnd_save(NSData *data, const char *role, ipc_u32 seq) {
    char path[160];
    snprintf(path, sizeof(path), "/private/var/tmp/foundation-xpc-%s-%u.json", role, seq);
    return [data writeToFile:fnd_string(path) atomically:1] ? 0 : -1;
}
static inline int fnd_request_body(sweet_xpc_t message, ipc_u32 seq, ipc_u32 value) {
    id keys[] = {fnd_string("device"), fnd_string("seq"), fnd_string("value")};
    id values[] = {fnd_string("duchamp"), [NSNumber numberWithInt:(int)seq], [NSNumber numberWithInt:(int)value]};
    NSDictionary *dict = [NSDictionary dictionaryWithObjects:values forKeys:keys count:3];
    NSData *data = fnd_encode(dict);
    if (!data) return -1;
    xpc_dictionary_set_data(message, "foundation-json", [data bytes], [data length]);
    ipc_note("FOUNDATION XPC REQUEST seq=%u bytes=%lu", seq, [data length]);
    return 0;
}
static inline int fnd_server_body(sweet_xpc_t event, sweet_xpc_t reply, ipc_u32 seq, ipc_u32 value, ipc_u32 transformed) {
    NSData *input = 0;
    NSDictionary *dict = fnd_decode(event, &input);
    if (!dict || [dict count] != 3 || !fnd_device(dict, "duchamp") ||
        !fnd_number(dict, "seq", (int)seq) || !fnd_number(dict, "value", (int)value)) return -1;
    NSString *upper = [(NSString *)[dict objectForKey:fnd_string("device")] uppercaseString];
    if (!upper || strcmp([upper UTF8String], "DUCHAMP")) return -1;
    id keys[] = {fnd_string("device"), fnd_string("soc"), fnd_string("seq"), fnd_string("value")};
    id values[] = {upper, [NSNumber numberWithInt:6897], [NSNumber numberWithInt:(int)seq], [NSNumber numberWithInt:(int)transformed]};
    NSData *output = fnd_encode([NSDictionary dictionaryWithObjects:values forKeys:keys count:4]);
    if (!output || fnd_save(input, "request", seq) || fnd_save(output, "server-reply", seq)) return -1;
    xpc_dictionary_set_data(reply, "foundation-json", [output bytes], [output length]);
    ipc_note("FOUNDATION XPC SERVER seq=%u request_bytes=%lu reply_bytes=%lu", seq, [input length], [output length]);
    return 0;
}
static inline int fnd_client_body(sweet_xpc_t reply, ipc_u32 seq, ipc_u32 expected) {
    NSData *data = 0;
    NSDictionary *dict = fnd_decode(reply, &data);
    if (!dict || [dict count] != 4 || !fnd_device(dict, "DUCHAMP") || !fnd_number(dict, "soc", 6897) ||
        !fnd_number(dict, "seq", (int)seq) || !fnd_number(dict, "value", (int)expected) ||
        fnd_save(data, "client-reply", seq)) return -1;
    ipc_note("FOUNDATION XPC CLIENT VALIDATED seq=%u bytes=%lu", seq, [data length]);
    return 0;
}
/* Every callback receives its own pool; no Foundation object escapes it. */
static inline int fnd_request(sweet_xpc_t message, ipc_u32 seq, ipc_u32 value) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    if (!pool) return -1;
    int result = -1;
    @try { result = fnd_request_body(message, seq, value); }
    @catch (id exception) { (void)exception; ipc_fail("Foundation request exception"); }
    [pool drain];
    if (!result) ipc_note("FOUNDATION XPC REQUEST POOL drained seq=%u", seq);
    return result;
}
static inline int fnd_server(sweet_xpc_t event, sweet_xpc_t reply, ipc_u32 seq, ipc_u32 value, ipc_u32 transformed) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    if (!pool) return -1;
    int result = -1;
    @try { result = fnd_server_body(event, reply, seq, value, transformed); }
    @catch (id exception) { (void)exception; ipc_fail("Foundation server exception"); }
    [pool drain];
    if (!result) ipc_note("FOUNDATION XPC SERVER POOL drained seq=%u", seq);
    return result;
}
static inline int fnd_client(sweet_xpc_t reply, ipc_u32 seq, ipc_u32 expected) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    if (!pool) return -1;
    int result = -1;
    @try { result = fnd_client_body(reply, seq, expected); }
    @catch (id exception) { (void)exception; ipc_fail("Foundation client exception"); }
    [pool drain];
    if (!result) ipc_note("FOUNDATION XPC CLIENT POOL drained seq=%u", seq);
    return result;
}
#endif
