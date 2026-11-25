# Secure Boot

Issue: [#516](https://github.com/tuna-os/tromso/issues/516). Policy:
[tuna-os/tunaOS#4955](https://github.com/tuna-os/tunaOS/issues/4955). The
full design, with sources, is `installer-medium/docs/SECURE-BOOT.md` in
tuna-os/tunaOS.

This page tells you what the publish job signs, what it does not sign, and
what no test has shown yet.

## The chain

Tromsø is a `tunaos-key` image. The boot chain is:

1. The firmware starts shim. Microsoft signed that shim for Fedora.
2. shim starts systemd-boot. The file name is `grubx64.efi`, because shim
   looks for that name. The tunaOS key signed it.
3. systemd-boot starts the kernel. shim checks the kernel against the tunaOS
   certificate.

A PC does not know the tunaOS certificate. The owner of the PC adds it one
time, in MokManager, from the file `tunaos-secure-boot.cer` on the ESP. A
virtual machine with no keys gets the key bundle from systemd-boot with no
prompt.

## What the publish job does

BuildStream does not sign. BuildStream keeps each source in its cache, and
CI publishes that cache to GHCR. A key in the build becomes public.

So `build-final.yml` adds the signed files as one layer. The steps run after
the build and before the push, only on `main` and `stable`, only for x86_64:

1. Check out `installer-medium/secure-boot` of tuna-os/tunaOS at a pinned
   commit.
2. Run `image/sign-image.sh`. This is the only step that gets
   `TUNAOS_SB_KEY` and `TUNAOS_SB_CERT`.
3. Run `image/verify-image.sh`. This step has no key. It uses `sbverify`
   with the certificate from the tunaOS repository.

A publish run with no key fails. The push, the cosign signature and the
promotion use the digest that has the layer.

The layer holds these files:

| File | Content |
|---|---|
| `/usr/lib/systemd/boot/efi/systemd-bootx64.efi.signed` | systemd-boot with the tunaOS signature |
| `/usr/lib/systemd/boot/efi/systemd-bootx64.efi` | systemd-boot with no signature |
| `/usr/lib/modules/<version>/vmlinuz` | the kernel with the tunaOS signature |
| `/usr/lib/tunaos/secure-boot/shimx64.efi`, `mmx64.efi` | the Fedora shim and MokManager |
| `/usr/lib/tunaos/secure-boot/tunaos-secure-boot.cer` | the public certificate |
| `/usr/lib/tunaos/secure-boot/keys/auto/` | the key bundle for systemd-boot |
| `/usr/lib/tunaos/secure-boot/mode` | the text `tunaos-key` |
| `/usr/lib/tunaos/secure-boot/provenance.toml` | the pin of the shim |
| `/usr/bin/tuna-secure-boot` | the helper for the installer |

## The shim

tunaOS builds no shim. The layer holds `shim-x64-16.1-7` from Fedora, byte
for byte. Dakota uses the same file. The pin is `image/shim.toml` in the
tunaOS repository: the Koji URL, the sha256, the source package and the
licence (BSD-3-Clause). The upstream is `rhboot/shim`.

## What has no signature

Be exact about the limits.

- **The initramfs and the kernel command line.** The image has no UKI. The
  boot entry names a kernel, an initramfs and a command line. Only the
  kernel has a signature. The command line holds the composefs digest of
  the root. A person who can write to the ESP can change the initramfs or
  the digest. Secure Boot does not stop that.
- **Kernel modules.** They have no signature. The kernel does not enforce
  module signatures.
- **The aarch64 image.** It has no layer.
- **The live ISO.** `tromso/src/build-iso.sh` copies the systemd-boot with
  no signature. The ISO boots with Secure Boot off, as before.
- **The installed ESP.** bootc copies the signed systemd-boot only. A
  system from the old installer has no shim on its ESP. It boots with
  Secure Boot off, or with the tunaOS key in the firmware. The new
  installer daemon must copy shim (tuna-os/fisherman#521).

## Who can use the key

`TUNAOS_SB_KEY` is an organisation secret. Three repositories can read it.
One step of the publish job gets it. A pull request from a fork gets no
secret. A branch run does not reach that step.

A person with write access can add a workflow on a branch, and that
workflow can read the secret. Nothing stops that today. A deployment
environment with reviewers is the fix.

The same key signs both files. On a machine that gets the key
bundle, that key is also the platform key. The key has no offline root.

## What a test has shown

| Claim | State |
|---|---|
| `sign-image.sh` and `verify-image.sh` work on a published image | Shown with a throwaway key, on a local machine. See tuna-os/tunaOS#4963. |
| The publish job signs with the real key | Not shown. The nightly build must pass first. |
| The image boots with Secure Boot on | Not shown. |
| MokManager accepts the certificate on a PC | Not shown. |

`files/boot-keys/` is a different thing. It holds the old key Makefile from
the GNOME OS recipe. The image does not use it, and
`check-release-keys.py` still rejects its test keys.
