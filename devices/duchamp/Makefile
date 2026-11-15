# Run from the repository root: make -f devices/duchamp/Makefile ...
OUT ?= out/duchamp/hakios-review
DTB ?= ../phone-fdt.bin
.PHONY: hardware-check test loader
hardware-check:
	python3 devices/duchamp/tools/hardware.py "$(DTB)" devices/duchamp/hardware.json --check
test:
	python3 tools/test-duchamp-hakios-port.py --output "$(OUT)" --dtb "$(DTB)" $(if $(UPSTREAM),--upstream "$(UPSTREAM)") $(if $(PAYLOAD),--payload "$(PAYLOAD)" --boot-template "$(BOOT_TEMPLATE)")
loader:
	DUCHAMP_TARGET=qemu SHIM_OUT="$(OUT)/loader" sh devices/duchamp/mtkloader/build.sh
