#!/usr/bin/env python3
"""Original launchd + intact cache + container/log/LS providers in QEMU RAM.

Preserve native provider jobs/credentials and record diagnostic redirection,
crash-loop suppression, a live cache witness and an actual LS reply callback.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import tempfile
import traceback
from duchamp_ls_status import parse as parse_ls_status
from duchamp_ui_readiness import registry as parse_registry, display as parse_display

REPO=Path(__file__).resolve().parents[1]


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as source:
        for data in iter(lambda:source.read(4<<20),b''):digest.update(data)
    return digest.hexdigest()


def require(ok,message):
    if not ok:raise ValueError(message)


def batch_passed(checks,ui_checks,ui_requested):
    return bool(checks) and all(value is True for value in checks.values()) and (
        not ui_requested or set(ui_checks)=={'runningboardd_native_identity','backboardd_native_identity',
            'six_five_second_health_checks','native_reply_after_ui'} and all(value is True for value in ui_checks.values()))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--seconds',type=int,default=360)
    ap.add_argument('--ui-probes',action='store_true',help='after core transport, probe original runningboardd/backboardd')
    ap.add_argument('--readiness',action='store_true',help='after UI health, request native registry rebuild and read display service')
    ap.add_argument('--springboard',action='store_true',help='only after native readiness and bundle-record gates, try original SpringBoard')
    args=ap.parse_args()
    require(not args.readiness or args.ui_probes,'readiness requires the UI providers')
    require(not args.springboard or args.readiness,'SpringBoard requires native readiness')
    out=args.output.resolve();require(not out.exists(),'preserve existing output')
    parent=Path.home()/'.cache/duchamp-qemu-tests';parent.mkdir(parents=True,exist_ok=True)
    native=Path(tempfile.mkdtemp(prefix='platform-services-',dir=parent))
    out.mkdir(parents=True)
    report=dict(passed=False,native_directory=str(native),scope=dict(phone_access=False,partition_write=False,
            physical_ufs=False,gpu=False,gui_tested=False,mach_lookup_is_native_reply=False,
            ui_daemon_probes_requested=args.ui_probes))
    report['scope']['readiness_requested']=args.readiness
    report['scope']['springboard_requested']=args.springboard
    result_code=1
    try:
        logs=native/'logs';logs.mkdir()
        def run(tag,command,check=True):
            result=subprocess.run([str(x) for x in command],cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (logs/(tag+'.log')).write_text(result.stdout)
            if check:require(result.returncode==0,tag+': '+result.stdout[-4000:])
            return result
        base=REPO/'work/shared-cache-qemu-v4/evidence/root.hfs'
        require(sha(base)=='3e23c283d5847ccf9e556f2300df8050d30ad8487e759e92689dd2765a9f71bf','cache root pin changed')
        root=native/'root.hfs';shutil.copyfile(base,root)
        hfs=REPO/'research/libdmg-hfsplus-build/hfsplus'
        require(sha(hfs)=='be041fa07ae8cbe040a2ec3811241af993eea597e8d46917f6c32359b2cd8b1b','HFS helper changed')
        shutil.copyfile(hfs,native/'hfsplus');(native/'hfsplus').chmod(0o755)
        def volume(*command,check=True):
            return run('hfs-'+str(len(list(logs.iterdir()))),[native/'hfsplus',root,*command],check)
        source_names=['qemu-service-ram.py','test-duchamp-platform-services.py','sweet-platform-services.c',
            'sweet-lsd-native-reply.m','sweet-ipc.h','sweet-foundation-api.h','qemu-sweet.py','mkpayload.py']
        source_names.append('duchamp_ls_status.py')
        if args.readiness:source_names+=['sweet-ui-readiness.m','sweet-ui-readiness.entitlements.plist','duchamp_ui_readiness.py']
        if args.springboard:source_names.append('read-systemos-zbm.cpp')
        sources=native/'test-sources';sources.mkdir()
        source_pins={}
        for name in source_names:
            path=REPO/'tools'/name;source_pins[name]=sha(path);shutil.copyfile(path,sources/name)
        prefs=REPO/'research/cfprefs-runtime-20F66-v2'
        info=json.loads((prefs/'source.json').read_text())
        audit=json.loads((prefs/'runtime-audit.json').read_text());require(audit['passed'],'supporting source closure incomplete')
        install={}
        expected={}
        for guest,item in audit['files'].items():
            path=prefs/'runtime-root'/guest.lstrip('/')
            require(sha(path)==item['sha256'],'runtime dependency changed: '+guest)
            install[guest]=path;expected[guest]=item['sha256']
        for guest,pin in info['resources'].items():
            path=prefs/'runtime-root'/guest.lstrip('/');require(sha(path)==pin,'resource changed')
            install[guest]=path;expected[guest]=pin
        for guest,pin in {'/sbin/launchd':'4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
            '/usr/libexec/xpcproxy':'2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f'}.items():
            path=REPO/'research/darwin-launchd-20F66/runtime-root'/guest.lstrip('/')
            require(sha(path)==pin,'original launchd/xpcproxy changed');install[guest]=path;expected[guest]=pin
        support=REPO/'work/lsd-support-audit-v1'
        receipt=support/'extraction-receipt.json'
        require(sha(receipt)=='2e40cee8599eaff9c57e20abb5236c62d1ed22fefa61e28f965ff72b80b47561','provider source receipt changed')
        extraction=json.loads(receipt.read_text())
        native_jobs={}
        for guest,item in extraction['extracted_files'].items():
            path=support/'apple-extracted'/guest.lstrip('/')
            require(sha(path)==item['sha256'],'provider executable changed')
            if guest.endswith('.plist'):
                job=plistlib.loads(path.read_bytes())
                entry=job.get('Program') or job['ProgramArguments'][0]
                native_jobs[entry]=job
                continue
            install[guest]=path;expected[guest]=item['sha256']
        policy=REPO/'work/container-policy-v1'
        require(sha(policy/'final-receipt.json')=='b3dbe2e8957fc313099a507879656e9df5b6b5cee030119bc024e5b80475bb1f','policy receipt changed')
        policy_receipt=json.loads((policy/'final-receipt.json').read_text())
        require(policy_receipt['completed'] and policy_receipt['all_13_extracted_files_verified'],'policy extraction incomplete')
        for relative,item in policy_receipt['files'].items():
            relative=relative.replace('\\','/');path=policy/relative
            require(sha(path)==item['sha256'],'original policy changed')
            if relative.startswith('apple-extracted/'):
                guest='/'+relative[len('apple-extracted/'):]
            elif relative.startswith('global-policy/'):
                guest='/'+relative[len('global-policy/'):]
            else:
                continue  # Receipts/comparisons are not guest system files.
            if guest.startswith('/System/Library/LaunchDaemons/'):continue
            install[guest]=path;expected[guest]=item['sha256']
        lsd=REPO/'work/ui-daemon-scan-v1/apple-extracted/usr/libexec/lsd'
        require(sha(lsd)=='cb9a5082ac7448e1ff8ee30e45925909568f39e6f4dc30e0bbbdf4332c27d0e4','lsd changed')
        install['/usr/libexec/lsd']=lsd;expected['/usr/libexec/lsd']=sha(lsd)
        version=REPO/'work/services-system-resources-v1/apple-extracted/System/Library/CoreServices/SystemVersion.plist'
        version_pin='46457f81a04a81f462bfa0ab24693eff2140ce81a254e64354e43bd0b996dd22'
        require(sha(version)==version_pin,'matching original SystemVersion resource missing/changed')
        version_info=plistlib.loads(version.read_bytes())
        require(version_info['ProductBuildVersion']=='20F66' and version_info['ProductVersion']=='16.5','system version mismatch')
        install['/System/Library/CoreServices/SystemVersion.plist']=version
        expected['/System/Library/CoreServices/SystemVersion.plist']=version_pin
        icu=REPO/'work/services-icu-resources-v1/apple-extracted'
        icu_pins={'/usr/share/icu/icudt70l.dat':'d2d5f82e30f4c193d48da78604381fa551adab548e2533e1ae6139538336f736',
            '/usr/share/icu/icutzformat.txt':'327d09f9e798492441b2a7839e2ce11498c64ae4c36ea98e248b89c5fc3172fe'}
        for guest,pin in icu_pins.items():
            path=icu/guest.lstrip('/');require(sha(path)==pin,'matching original ICU resource missing/changed')
            install[guest]=path;expected[guest]=pin
        lsd_job_path=REPO/'work/ui-daemon-scan-v1/apple-extracted/System/Library/LaunchDaemons/com.apple.lsd.plist'
        require(sha(lsd_job_path)=='9728a545bd4cdde11d2f264ef547c5a15717964d8029b37fa71ffa23010b3a78','lsd job changed')
        native_jobs['/usr/libexec/lsd']=plistlib.loads(lsd_job_path.read_bytes())
        if args.readiness:
            resources=REPO/'work/services-ui-boundary-resources-v1'
            require(sha(resources/'receipt.json')=='3b5f048c8554ae7b0396af5c5075df5995f089cc7f07343f9dcbbe9ef14c7901','original UI/installation resource receipt changed')
            resource_receipt=json.loads((resources/'receipt.json').read_text())
            require(resource_receipt['all_requested_present'],'incomplete original bundle/installd extraction')
            for guest,item in resource_receipt['files'].items():
                path=resources/'apple-extracted'/guest.lstrip('/')
                require(sha(path)==item['sha256'],'original UI/installation resource changed')
                if guest.startswith('/System/Library/LaunchDaemons/'):
                    job=plistlib.loads(path.read_bytes())
                    native_jobs[job['ProgramArguments'][0]]=job
                else:install[guest]=path;expected[guest]=item['sha256']
            if args.springboard:
                bundle=REPO/'work/springboard-bundle-v2'
                require(sha(bundle/'receipt.json')=='f2de94690e2fe824b4cf9d42ff665fcaee0efcdac5c82f80576021cb45d04fac','original full SpringBoard bundle receipt changed')
                bundle_files=json.loads((bundle/'receipt.json').read_text())['files']
                for guest,item in bundle_files.items():
                    require(guest.startswith('/System/Library/CoreServices/SpringBoard.app/') and '..' not in guest.split('/'),'unsafe bundle path')
                    path=bundle/'apple-extracted'/guest.lstrip('/')
                    require(not path.is_symlink() and sha(path)==item['sha256'],'original bundle file changed')
                    require(guest not in expected or expected[guest]==item['sha256'],'conflicting bundle bytes')
                    install[guest]=path;expected[guest]=item['sha256']
                module=REPO/'work/ui-trampolines-v3'
                require(sha(module/'receipt.json')=='c39473bd1118fc00d2ef4354dba477acbdef6e65ce155e2def5f2f87ac581c7f','original Objective-C trampoline receipt changed')
                module_receipt=json.loads((module/'receipt.json').read_text())
                guest='/usr/lib/libobjc-trampolines.dylib'
                path=module/'apple-extracted'/guest.lstrip('/')
                require(module_receipt['guest_path']==guest and module_receipt['bytes']==68080 and
                    module_receipt['macho']['cpu']=='arm64' and module_receipt['macho']['code_signature'] and
                    module_receipt['negative_checks']==3,'trampoline provenance/architecture checks incomplete')
                require(sha(path)=='a5410b215468c275e1f861c7e605f58401e332f7f23765a6e1fbe7391d4f05df','original trampoline module changed')
                require(sha(REPO/'tools/read-systemos-zbm.cpp')==module_receipt['helper_source_sha256'],'module decoder source differs from receipt')
                install[guest]=path;expected[guest]=sha(path)
                render=REPO/'work/springboard-render-resources-v1'
                require(sha(render/'receipt.json')=='d4ffb35a6e3b476a42132b2c09132dcc2901349ac9ffc46571255881e3685b3c','original icon/font resource receipt changed')
                render_receipt=json.loads((render/'receipt.json').read_text())
                require(render_receipt['file_count']==115 and render_receipt['total_bytes']==9788380,'incomplete icon/font resources')
                for guest,item in render_receipt['files'].items():
                    require(guest in ('/System/Library/Fonts/Core/Helvetica.ttc','/System/Library/Fonts/CoreUI/SFUI.ttf') or
                        guest.startswith(('/System/Library/PrivateFrameworks/IconServices.framework/',
                            '/System/Library/PrivateFrameworks/MobileIcons.framework/')),'unexpected icon/font resource path')
                    path=render/'apple-extracted'/guest.lstrip('/')
                    require(not path.is_symlink() and sha(path)==item['sha256'],'original icon/font resource changed')
                    require(guest not in expected or expected[guest]==item['sha256'],'conflicting icon/font resource bytes')
                    install[guest]=path;expected[guest]=item['sha256']
        if args.ui_probes:
            scan=REPO/'work/ui-daemon-scan-v1'
            require(sha(scan/'extraction-receipt.json')=='2e51fe8085ebce51f8d40b177d127241b692a4d025fed4217740ce71b10b9898','UI source receipt changed')
            ui_files=json.loads((scan/'extraction-receipt.json').read_text())['extracted_files']
            for entry in ('/usr/libexec/runningboardd','/usr/libexec/backboardd'):
                label=Path(entry).name
                for guest in (entry,'/System/Library/LaunchDaemons/com.apple.'+label+'.plist'):
                    item=ui_files[guest];path=scan/'apple-extracted'/guest.lstrip('/')
                    require(sha(path)==item['sha256'],'original UI source changed')
                    if guest.endswith('.plist'):native_jobs[entry]=plistlib.loads(path.read_bytes())
                    else:install[guest]=path;expected[guest]=item['sha256']
            if args.springboard:
                guest='/System/Library/LaunchDaemons/com.apple.SpringBoard.plist'
                path=scan/'apple-extracted'/guest.lstrip('/')
                require(sha(path)==ui_files[guest]['sha256'],'original SpringBoard job changed')
                native_jobs['/System/Library/CoreServices/SpringBoard.app/SpringBoard']=plistlib.loads(path.read_bytes())
            event_config='/System/Library/BackBoard/EventProcessorConfiguration.plist'
            path=REPO/'work/services-backboard-resources-v1/apple-extracted'/event_config.lstrip('/')
            pin='1360a59a33789cebea9db2f652ddaf42c6978158a98c2fce72cb43810ea9ed01'
            require(sha(path)==pin,'matching original BackBoard event configuration missing/changed')
            install[event_config]=path;expected[event_config]=pin
        jobs={};overrides={}
        for entry,original in native_jobs.items():
            job=dict(original);label=job['Label']
            changes=dict(KeepAlive=False,StandardOutPath='/private/var/tmp/'+label+'-console.log',
                StandardErrorPath='/private/var/tmp/'+label+'-console.log')
            job.update(changes)
            if entry.startswith('/usr/libexec/containermanagerd'):
                # The normal daemon's native system-domain default is root.
                # This minimal launchd fixture relocated an unspecified user
                # to user/501. Make root/System explicit; preserve arguments.
                root_context=dict(UserName='root',GroupName='wheel',LimitLoadToSessionType='System')
                job.update(root_context);changes.update(root_context)
            if entry in ('/usr/libexec/runningboardd','/usr/libexec/backboardd','/System/Library/CoreServices/SpringBoard.app/SpringBoard'):
                job['RunAtLoad']=False;changes['RunAtLoad']=False
                if entry.endswith('/runningboardd'):
                    job.update(UserName='root',GroupName='wheel',LimitLoadToSessionType='System')
                    changes.update(UserName='root',GroupName='wheel',LimitLoadToSessionType='System')
            # Disable only crash-loop panic policy in this controlled fixture.
            # Arguments, conditional flags, MachServices and credentials stay native.
            if '_PanicOnCrash' in job:del job['_PanicOnCrash'];changes['_PanicOnCrash']='removed for diagnostic trial'
            jobs[label+'.plist']=job;overrides[label]=changes
        notify=dict(info['notifyd_source']['original_job'])
        notify.update(RunAtLoad=True,KeepAlive=False,UserName='root',GroupName='wheel',
            StandardOutPath='/private/var/tmp/notifyd-console.log',StandardErrorPath='/private/var/tmp/notifyd-console.log',
            ProgramArguments=['/usr/sbin/notifyd','-d','-log_file','/private/var/tmp/notifyd-debug.log','-shm_pages','0'])
        jobs['com.apple.notifyd.plist']=notify
        for name,meta in info['cfprefsd_source']['original_jobs'].items():
            job=dict(meta['original_job']);job.update(Disabled=False,RunAtLoad=False,KeepAlive=False,
                UserName='root',GroupName='wheel',LimitLoadToSessionType='System',
                StandardOutPath='/private/var/tmp/cfprefsd-console.log',StandardErrorPath='/private/var/tmp/cfprefsd-console.log')
            jobs[name]=job
        jobs['org.sweet.qemu.c-service.plist']=dict(Label='org.sweet.qemu.platform-services',
            ProgramArguments=['/sbin/sweet-platform-services'],RunAtLoad=True,KeepAlive=False,
            UserName='root',GroupName='wheel',LimitLoadToSessionType='System',
            StandardOutPath='/dev/console',StandardErrorPath='/dev/console')
        # Let launchd establish the client's native user bootstrap context,
        # rather than only changing UID in a system-bootstrap fork child.
        jobs['org.sweet.qemu.lsd-native.plist']=dict(Label='org.sweet.qemu.lsd-native',
            ProgramArguments=['/sbin/sweet-lsd-native-reply'],UserName='mobile',GroupName='mobile',
            RunAtLoad=False,KeepAlive=False,StandardOutPath='/private/var/tmp/platform-native-query.txt',
            StandardErrorPath='/private/var/tmp/platform-native-query.txt')
        if args.readiness:
            for kind in ('registry','display'):
                label='org.sweet.qemu.ui-'+kind
                jobs[label+'.plist']=dict(Label=label,ProgramArguments=['/sbin/sweet-ui-readiness',kind],
                    UserName='mobile',GroupName='mobile',RunAtLoad=False,KeepAlive=False,
                    StandardOutPath='/private/var/tmp/ui-'+kind+'.txt',
                    StandardErrorPath='/private/var/tmp/ui-'+kind+'.txt')
        for name,job in jobs.items():
            path=native/name;path.write_bytes(plistlib.dumps(job))
            destination='/private/var/tmp/SpringBoard-job.plist' if name=='com.apple.SpringBoard.plist' else '/System/Library/LaunchDaemons/'+name
            install[destination]=path
        if args.springboard:
            absent=volume('ls','/System/Library/LaunchDaemons/com.apple.SpringBoard.plist',check=False)
            require('No such file or directory' in absent.stdout,'base already exposes an automatic SpringBoard job')
        link_root=prefs/'runtime-root'
        programs=[('controller','sweet-platform-services.c',False),('query','sweet-lsd-native-reply.m',True)]
        if args.readiness:programs.append(('readiness','sweet-ui-readiness.m',True))
        for name,filename,objc in programs:
            flags=['-fblocks','-fno-objc-arc','-fobjc-exceptions'] if objc else [
                '-DSWEET_UI_PROBES='+str(int(args.ui_probes)),'-DSWEET_UI_READINESS='+str(int(args.readiness)),
                '-DSWEET_SPRINGBOARD_PROBE='+str(int(args.springboard))]
            if name=='readiness':flags+=['-DSWEET_VERIFY_SPRINGBOARD_RECORD='+str(int(args.springboard))]
            run('compile-'+name,['clang','-target','arm64-apple-ios16.5','-O1','-Wall','-Wextra','-Werror',
                '-fno-stack-protector','-fno-builtin',*flags,'-c',sources/filename,'-o',native/(name+'.o')])
            libs=['-lobjc.A','-framework','Foundation'] if objc else []
            run('link-'+name,['ld64.lld','-arch','arm64','-platform_version','ios','16.5','16.5','-adhoc_codesign',
                '-syslibroot',link_root,'-L'+str(link_root/'usr/lib'),'-F'+str(link_root/'System/Library/Frameworks'),
                '-lSystem.B',*libs,'-e','_main','-o',native/name,native/(name+'.o')])
        install.update({'/sbin/sweet-platform-services':native/'controller','/sbin/sweet-lsd-native-reply':native/'query'})
        if args.readiness:
            signer=REPO/'research/host-ipsw-3.1.739/ipsw'
            require(sha(signer)=='7f22f07821cd964c0333172ef9bac734b53df5035a5e7c8ce9ec1580891f6d4c','offline signing tool changed')
            unsigned_pin=sha(native/'readiness')
            run('sign-readiness',[signer,'macho','sign','--id','org.sweet.qemu.ui-readiness','--ad-hoc',
                '--ent',sources/'sweet-ui-readiness.entitlements.plist','--output',native/'readiness-signed',native/'readiness'])
            require(sha(native/'readiness')==unsigned_pin,'signer changed its input')
            signed_info=run('signed-entitlements',[signer,'macho','info',native/'readiness-signed','--ent'])
            entitlements=plistlib.loads(signed_info.stdout.encode())
            require(entitlements=={'com.apple.lsapplicationworkspace.rebuildappdatabases':True},'unexpected client entitlement set')
            install['/sbin/sweet-ui-readiness']=native/'readiness-signed'
        known=set();installed={}
        for guest,path in sorted(install.items()):
            for parent_dir in reversed(Path(guest).parents):
                name=parent_dir.as_posix()
                if name not in known:
                    if 'No such file or directory' in volume('ls',name,check=False).stdout:
                        volume('mkdir',name);volume('chmod','755',name)
                    known.add(name)
            volume('add',path,guest);volume('chmod','644' if guest.endswith('.plist') or '/etc/' in guest else '755',guest)
            volume('extract',guest,native/'roundtrip');pin=sha(path)
            require(sha(native/'roundtrip')==pin,'installed source differs: '+guest)
            require(guest not in expected or pin==expected[guest],'source changed during install')
            installed[guest]=pin
        inputs=dict(base_sha256=sha(base),root_sha256=sha(root),installed=installed,source_pins=source_pins,
            native_jobs=native_jobs,diagnostic_overrides=overrides,
            deferred_springboard_job='/private/var/tmp/SpringBoard-job.plist' if args.springboard else None,
            note='Original programs/arguments/MachServices; no-restart/output/crash-policy overrides. MCM root/System explicit to prevent observed user relocation; native query uses a mobile launchd job. Original logd hardware/variant gates retained.')
        (native/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
        spec=importlib.util.spec_from_file_location('platform_ram_runner',REPO/'tools/qemu-service-ram.py')
        loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
        print('platform-services: original launchd/cache/providers, QEMU writable RAM starting',flush=True)
        vm=loader.run_vm(REPO/'work/ci-41543710742-kernel/artifact/kernel.development.sweet',
            REPO/'research/mt6897-boot/bsd-service-split-ci41543710742-qemu-authorized.adt',root,native/'run',args.seconds,
            ['PLATFORM SERVICES DONE status=0','PLATFORM SERVICES DONE status=1','PLATFORM CACHE FAIL',
             'SWEET EARLY PANIC:','Library not loaded:','Symbol not found:'])
        guest=native/'guest';guest.mkdir()
        final=native/'run/ramdisk-final.hfs'
        def extract(path,dest):
            return run('extract-'+str(len(list(logs.iterdir()))),[native/'hfsplus',final,'extract',path,dest],False)
        extract('/private/var/tmp/ipc-platform-services.log',guest/'controller.log')
        extract('/private/var/tmp/platform-native-query.txt',guest/'native-query.txt')
        extract('/private/var/tmp/platform-native-query-first.txt',guest/'native-query-first.txt')
        if args.readiness:
            for kind in ('registry','display'):
                extract('/private/var/tmp/ui-'+kind+'.txt',guest/('ui-'+kind+'.txt'))
        if args.springboard:
            extract('/private/var/tmp/platform-springboard-bootstrap.txt',guest/'springboard-bootstrap.txt')
        for label in ('com.apple.containermanagerd','com.apple.containermanagerd.system','com.apple.logd','com.apple.lsd',
            'com.apple.runningboardd','com.apple.backboardd','com.apple.mobile.installd','com.apple.SpringBoard'):
            extract('/private/var/tmp/'+label+'-console.log',guest/(label+'.log'))
        for index in range(7 if args.springboard else 6 if args.readiness else 5 if args.ui_probes else 3):
            extract('/private/var/tmp/platform-%d-start.txt'%index,guest/('%d-start.txt'%index))
            for attempt in range(5):extract('/private/var/tmp/platform-%d-print-%d.txt'%(index,attempt),guest/('%d-print-%d.txt'%(index,attempt)))
        matching=True
        for i,(path,pin) in enumerate(installed.items()):
            result=extract(path,guest/('installed-'+str(i)))
            matching &= result.returncode==0 and (guest/('installed-'+str(i))).is_file() and sha(guest/('installed-'+str(i)))==pin
        text=(guest/'controller.log').read_text() if (guest/'controller.log').exists() else ''
        reply=(guest/'native-query.txt').read_text() if (guest/'native-query.txt').exists() else ''
        native_status=parse_ls_status(reply)
        checks=dict(original_cache_verified='PLATFORM ORIGINAL CACHE VERIFIED' in text,
            logd_native_identity=bool(re.search(r'PLATFORM SERVICE ALIVE label=com.apple.logd pid=\d+ uid=272 gid=272 stable=3',text)),
            mcm_native_identity=bool(re.search(r'PLATFORM SERVICE ALIVE label=com.apple.containermanagerd pid=\d+ uid=0 gid=0 stable=3',text)),
            lsd_native_identity=bool(re.search(r'PLATFORM SERVICE ALIVE label=com.apple.lsd pid=\d+ uid=501 gid=501 stable=3',text)),
            native_status_reply=native_status['transport_verified'],
            original_icu_dateformat='LSD NATIVE ICU ISO8601 PASS 1970-01-01T00:00:00Z' in reply,
            final_providers_alive='PLATFORM FINAL PROVIDERS ALIVE=1' in text,
            complete_saved_result='PLATFORM SERVICES DONE status=0' in text,
            success_stop=vm.get('stop_marker')=='PLATFORM SERVICES DONE status=0',
            all_installed_hashes_match=bool(matching),source_root_unchanged=vm.get('source_root_unchanged') is True,
            base_unchanged=sha(base)==inputs['base_sha256'],
            test_sources_unchanged=source_pins=={name:sha(REPO/'tools'/name) for name in source_names})
        core_fields=['original_cache_verified','logd_native_identity','mcm_native_identity','lsd_native_identity',
            'native_status_reply','original_icu_dateformat','final_providers_alive','all_installed_hashes_match',
            'source_root_unchanged','base_unchanged','test_sources_unchanged']
        core_passed=all(checks[name] for name in core_fields) and 'PLATFORM CORE SERVICES PASS=1' in text
        ui_checks={}
        if args.ui_probes:
            ui_checks=dict(runningboardd_native_identity=bool(re.search(r'PLATFORM SERVICE ALIVE label=com.apple.runningboardd pid=\d+ uid=0 gid=0 stable=3',text)),
                backboardd_native_identity=bool(re.search(r'PLATFORM SERVICE ALIVE label=com.apple.backboardd pid=\d+ uid=501 gid=501 stable=3',text)),
                six_five_second_health_checks=re.findall(r'PLATFORM UI HEALTH check=(\d+) stable=1',text)==['1','2','3','4','5','6'],
                native_reply_after_ui='PLATFORM NATIVE REPLY AFTER UI verified=1' in text)
        readiness_checks={}
        if args.readiness:
            readiness_results={}
            for kind,parse in [('registry',parse_registry),('display',parse_display)]:
                path=guest/('ui-'+kind+'.txt')
                response=path.read_text() if path.exists() else ''
                readiness_results[kind]=parse(response,require_app=args.springboard) if kind=='registry' else parse(response)
                readiness_checks[kind]=readiness_results[kind]['verified']
            checks['native_readiness']=set(readiness_checks)=={'registry','display'} and all(readiness_checks.values())
            checks['native_installd_identity']=bool(re.search(r'PLATFORM SERVICE ALIVE label=com.apple.mobile.installd pid=\d+ uid=33 gid=33 stable=3',text))
        if args.springboard:
            checks['springboard_native_identity']=bool(re.search(r'PLATFORM SERVICE ALIVE label=com.apple.SpringBoard pid=\d+ uid=501 gid=501 stable=3',text))
            checks['springboard_health']=re.findall(r'PLATFORM SPRINGBOARD HEALTH check=(\d+) stable=1',text)==['1','2','3','4','5','6']
            gate=text.find('PLATFORM READINESS registry=1 display=1')
            loaded=text.find('PLATFORM COMMAND tag=springboard-bootstrap status=0x0 timeout=0')
            started=text.find('PLATFORM SPRINGBOARD START pid=')
            checks['springboard_started_after_gate']=0<=gate<loaded<started
        report.update(passed=batch_passed(checks,ui_checks,args.ui_probes),checks=checks,vm=vm,root_sha256=inputs['root_sha256'],
            installed_count=len(installed),provider_diagnostics_are_not_rpc_proof=True,
            core_services_passed=core_passed,ls_native_status=native_status,ui_checks=ui_checks,
            readiness_checks=readiness_checks,full_gui_ready=False)
        if args.readiness:report['readiness_results']=readiness_results
        result_code=0 if report['passed'] else 1
    except Exception:
        report['error']=traceback.format_exc();print(report['error'],flush=True)
    finally:
        (native/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
        shutil.copytree(native,out/'evidence',ignore=shutil.ignore_patterns('guest-ram.bin'))
    print(json.dumps(report,indent=2),flush=True)
    return result_code


if __name__=='__main__':raise SystemExit(main())
