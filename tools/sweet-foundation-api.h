/* Selected public Foundation selectors for the fixed iOS 16.5 probes. */
#ifndef SWEET_FOUNDATION_API_H
#define SWEET_FOUNDATION_API_H
#include "sweet-ipc.h"
typedef unsigned long NSUInteger;
typedef _Bool BOOL;
@class NSString, NSData, NSError;
__attribute__((objc_root_class)) @interface NSObject
+ (id)alloc;
+ (Class)class;
- (id)init;
- (BOOL)isKindOfClass:(Class)kind;
@end
@interface NSAutoreleasePool : NSObject
- (void)drain;
@end
@interface NSString : NSObject
+ (id)stringWithUTF8String:(const char *)bytes;
- (const char *)UTF8String;
- (NSUInteger)length;
- (NSString *)uppercaseString;
@end
@interface NSNumber : NSObject
+ (id)numberWithInt:(int)value;
- (int)intValue;
@end
@interface NSDictionary : NSObject
+ (id)dictionaryWithObjects:(const id *)objects forKeys:(const id *)keys count:(NSUInteger)count;
- (id)objectForKey:(id)key;
- (NSUInteger)count;
@end
@interface NSData : NSObject
+ (id)dataWithContentsOfFile:(NSString *)path;
+ (id)dataWithBytes:(const void *)bytes length:(NSUInteger)length;
- (const void *)bytes;
- (NSUInteger)length;
- (BOOL)writeToFile:(NSString *)path atomically:(BOOL)atomic;
- (BOOL)isEqualToData:(NSData *)data;
@end
@interface NSJSONSerialization : NSObject
+ (NSData *)dataWithJSONObject:(id)object options:(NSUInteger)options error:(NSError **)error;
+ (id)JSONObjectWithData:(NSData *)data options:(NSUInteger)options error:(NSError **)error;
@end
@interface NSException : NSObject
+ (id)exceptionWithName:(NSString *)name reason:(NSString *)reason userInfo:(NSDictionary *)info;
- (NSString *)name;
@end
#endif
