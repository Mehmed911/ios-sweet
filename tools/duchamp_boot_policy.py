"""Offline, allowlisted policy evidence. Never returns complete boot arguments."""
import hashlib,importlib.util,json,re,shlex,sys
from pathlib import Path
import duchamp_saved_ufs as saved

SOURCE_PINS={
    'kernel/dma/swiotlb.c':'ad6333c3fe1ffeffa74bd5c03b420130c266f6af',
    'arch/arm64/mm/init.c':'4fabbcff8c7a1c9e121274ea995349a5204c4820',
    'init/main.c':'686594ba22ac9206a693e995214ac423ba3b29b0',
    'drivers/of/fdt.c':'335d39eeba363a9741cd9274329d82af405fa0c8',
    'arch/arm64/kvm/arm.c':'dd187094ab406811d9f0583451fa404477dfd2a4',
    'arch/arm64/include/asm/setup.h':'f4af547ef54caa70a521387d442ffeb6d04a230b',
    'arch/arm64/include/uapi/asm/setup.h':'5d703888f35110d2a7a15ec1836bffcffae3c8bb'}
VALUES={'swiotlb':{'force','noforce'},'disable_dma32':{'on','off'},
        'kvm-arm.mode':{'none','nvhe','protected'},'initcall_blacklist':{'ufshcd_core_init'},'bootconfig':{''}}

def sources(root):
    receipts=[]
    for path,expected in SOURCE_PINS.items():
        data=(root/path).read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if blob!=expected:raise ValueError('source pin mismatch: '+path)
        receipts.append({'path':path,'git_blob':blob,'sha256':saved.sha(data),
            'url':'https://github.com/aosp-mirror/kernel_common/blob/'+saved.GKI+'/'+path})
    return receipts

def select(text):
    """Only known keys AND known values; preserve order and duplicates."""
    chosen=[];unrecognized=0
    try:tokens=shlex.split(text)
    except ValueError:raise ValueError('invalid command-line quoting') from None
    for token in tokens:
        key,_,value=token.partition('=')
        if key not in VALUES:continue
        if value not in VALUES[key]:unrecognized+=1;continue
        chosen.append(token)
    return {'selected':chosen,'unrecognized_policy_values':unrecognized}

def vendor_fields(data):
    if data[:8]!=b'VNDRBOOT' or saved.unpack(data,8,'<I')[0]!=4:raise ValueError('vendor boot v4 required')
    u=lambda o:saved.unpack(data,o,'<I')[0]
    page=u(12);header=u(2096)
    if page!=4096 or header!=2128:raise ValueError('captured vendor header changed')
    align=lambda n:(n+page-1)&~(page-1)
    offset=align(header)+align(u(24))+align(u(2100))+align(u(2112))
    config=saved.span(data,offset,u(2124))
    return {'header_cmdline':select(saved.span(data,28,2048).split(b'\0')[0].decode()),
            'bootconfig_bytes':len(config),'bootconfig_sha256':saved.sha(config),
            # Unknown bootconfig syntax is never interpreted as absence.
            'bootconfig_kernel_overrides_absent_in_saved_section':not config}

def merge(builtin,fdt,limit):
    """Model the pinned EXTEND byte bound; never return the full command line."""
    if limit<2:raise ValueError('invalid command-line limit')
    raw=(builtin+' '+fdt).encode()
    return {'capacity_bytes':limit,'requested_bytes':len(raw)+1,'fits_without_truncation':len(raw)<limit,
            'selected_after_size_limit':select(raw[:limit-1].decode())}

def inspect(boot,vendor,fdt,source_root):
    image,raw_config=saved.boot_contents(boot)
    b=saved.pinned(boot,saved.BOOT_SHA);v=saved.pinned(vendor,saved.VENDOR_SHA)
    raw=saved.pinned(fdt,saved.FDT_SHA)
    spec=importlib.util.spec_from_file_location('boot_policy_fdt',Path(__file__).with_name('inspect-duchamp-hardware.py'))
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    dt=mod.Fdt(raw);chosen=dt.nodes['/chosen'].props['bootargs']
    if not chosen.endswith(b'\0') or b'\0' in chosen[:-1]:raise ValueError('invalid captured bootargs')
    flags={}
    for line in raw_config.decode().splitlines():
        if line.startswith('CONFIG_'):
            key,_,value=line.partition('=');flags[key]=value
        elif line.startswith('# CONFIG_') and line.endswith(' is not set'):flags[line[2:-11]]='n'
    keys=['CONFIG_CMDLINE_EXTEND','CONFIG_CMDLINE_FORCE','CONFIG_CMDLINE_FROM_BOOTLOADER',
          'CONFIG_BOOT_CONFIG','CONFIG_BOOT_CONFIG_EMBED','CONFIG_SWIOTLB','CONFIG_ZONE_DMA32',
          'CONFIG_KVM','CONFIG_KALLSYMS','CONFIG_IOMMU_DMA','CONFIG_CMA']
    if flags.get('CONFIG_CMDLINE_EXTEND')!='y' or flags.get('CONFIG_CMDLINE_FORCE')!='n':
        raise ValueError('unexpected captured command-line merge policy')
    builtin_text=json.loads(flags['CONFIG_CMDLINE']);builtin=select(builtin_text)
    selected=select(chosen[:-1].decode())
    if selected!={'selected':['disable_dma32=on','swiotlb=noforce','initcall_blacklist=ufshcd_core_init','bootconfig'],
                  'unrecognized_policy_values':0}:raise ValueError('captured policy differs')
    vendor_policy=vendor_fields(v)
    if vendor_policy['bootconfig_bytes']!=0:raise ValueError('nonempty saved bootconfig needs separate review')
    header_source=(source_root/'arch/arm64/include/uapi/asm/setup.h').read_text()
    match=re.search(r'^#define COMMAND_LINE_SIZE\s+(\d+)$',header_source,re.M)
    if not match or int(match[1])!=2048:raise ValueError('pinned command-line size differs')
    combined=merge(builtin_text,chosen[:-1].decode(),int(match[1]))
    if not combined['fits_without_truncation']:raise ValueError('captured command-line truncation needs review')
    header=select(saved.span(b,44,1536).split(b'\0')[0].decode())
    return {'audit_complete':True,'input_sha256':{'boot':saved.BOOT_SHA,'vendor_boot':saved.VENDOR_SHA,'fdt':saved.FDT_SHA},
        'kernel_stamp_commit':saved.GKI,'kernel_image_sha256':saved.sha(image),'config_sha256':saved.sha(raw_config),
        'config':{k:flags.get(k,'not_in_config') for k in keys},'builtin_cmdline':builtin,
        'captured_fdt_cmdline':selected,'boot_header_cmdline':header,'vendor_boot':vendor_policy,'source_bounded_merge':combined,
        'source_interpretation':{
            'swiotlb_noforce':'sets force_disable; default swiotlb_init_remap and late init return without allocating',
            'disable_dma32_on':'sets disable_dma32; ZONE_DMA32 max PFN becomes zero at zone initialization',
            'initcall_blacklist':'requests skipping ufshcd_core_init at kernel initcall dispatch; does not prove module state',
            'protected_kvm':'requested by built-in cmdline; acceptance requires hyp available and non-VHE; initialization can fail',
            'cmdline_merge':'built-in then FDT for CMDLINE_EXTEND; kernel.* bootconfig args would be prepended by init/main.c'},
        'full_command_lines_exported':False,'runtime_policy_verified':False,'physical_dma_route_verified':False,
        'installed_firmware_contract_verified':False,'physical_backend_enabled':False,
        'limits':['bootloader-generated initrd bootconfig and runtime overrides not captured',
                  'default SWIOTLB skip is not proof of all possible per-device/vendor pools',
                  'Linux source policy is not an XNU firmware contract or a measured DMA mask'],
        'scope':'saved files and pinned source only; no device, firmware or physical MMIO execution'}
