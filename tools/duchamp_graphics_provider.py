"""0BSD: validate a real guest IOKit contract log, without inferring rendering."""
import re

CHECKS = ('original-cache mobile-identity original-iokit public-symbols main-port '
          'accelerator-dictionary accelerator-class-key accelerator-absent zero-accelerator-rejected '
          'missing-dictionary missing-class-key missing-service-empty zero-missing-rejected '
          'surface-dictionary surface-class-key real-surface-service surface-object-identity '
          'real-userclient-open implemented-limits short-output-rejected unsupported-selector-error '
          'null-surface-capability-rejected unsupported-memory-map userclient-close service-release '
          'null-and-dead-handles-rejected').split()


def parse(text):
    checks = dict(complete_checks=re.findall(r'^PROVIDER CHECK (\S+) passed=1$', text, re.M) == CHECKS,
                  no_failed_checks=not re.search(r'^PROVIDER CHECK .* passed=(?!1$)', text, re.M),
                  honest_completion='PROVIDER DONE checks=26 failed=0 gpu_published=0 metal_compatibility=0 authentic_frame=0\n' in text)
    identity = re.findall(r'^PROVIDER IDENTITY pid=(\d+) ppid=(\d+) uid=(\d+)$', text, re.M)
    checks['mobile_process'] = len(identity) == 1 and int(identity[0][0]) > 1 and identity[0][2] == '501'
    enums = re.findall(r'^PROVIDER ENUM class=(\S+) kr=(0x[0-9a-f]+) iterator=(0x[0-9a-f]+) first=(0x[0-9a-f]+) extra=(0x[0-9a-f]+)$', text, re.M)
    objects = {r[0]: dict(zip(('kr', 'iterator', 'service', 'extra'), (int(v, 16) for v in r[1:]))) for r in enums}
    checks['exact_enumerations'] = len(enums) == len(objects) == 3
    for cls in ('IOAcceleratorES', 'DuchampDeliberatelyAbsentGraphicsProvider', 'IOCoreSurfaceRoot'):
        checks['dictionary_' + cls] = f'PROVIDER DICTIONARY class={cls} IOProviderClass={cls} keys=1\n' in text
        e = objects.get(cls, {})
        checks['matching_' + cls] = (e.get('kr') == 0 and e.get('extra') == 0 and
            (e.get('service', 0) not in (0, 0xffffffff) and e.get('iterator', 0) not in (0, 0xffffffff)
             if cls == 'IOCoreSurfaceRoot' else e.get('service') == 0))
    opened = re.findall(r'^PROVIDER OPEN service=(0x[0-9a-f]+) type=0 kr=0x0 connection=(0x[0-9a-f]+) owner_pid=(\d+)$', text, re.M)
    checks['actual_surface_client'] = len(opened) == 1 and bool(identity) and opened[0][2] == identity[0][0] and int(opened[0][0],16) == objects.get('IOCoreSurfaceRoot',{}).get('service') and int(opened[0][1],16) not in (0,0xffffffff)
    checks['implemented_operation'] = 'PROVIDER METHOD selector=13 kr=0x0 bytes=24\n' in text
    checks['kernel_unsupported_error'] = 'PROVIDER METHOD selector=4294967295 kr=0xe00002c7\n' in text
    checks['kernel_short_buffer_error'] = bool(re.search(r'^PROVIDER METHOD selector=13 short=1 kr=0x(?!0\b)[0-9a-f]+ bytes=8$', text, re.M))
    checks['kernel_null_capability_error'] = bool(re.search(r'^PROVIDER METHOD selector=34 foreign_or_null_capability=0 kr=0x(?!0\b)[0-9a-f]+$', text, re.M))
    checks['kernel_mapping_error'] = bool(re.search(r'^PROVIDER MAP type=4294967295 kr=0x(?!0\b)[0-9a-f]+ address=0 bytes=0$', text, re.M))
    return dict(passed=all(checks.values()), checks=checks, process=identity[0] if identity else None,
                enumerations=objects, surface_client=opened[0] if opened else None,
                first_springboard_frame_verified=False, gpu_provider_implemented=False,
                note='Diagnostic process observations; original BackBoard evidence is checked separately.')
