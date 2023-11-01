# Set to 1 if building an empty subscription-only package.
%define empty_package		0

#######################################################
# Only need to update these variables and the changelog
%define kernel_ver	4.18.0-477.21.1.el8_8
%define kpatch_ver	0.9.7
%define rpm_ver		1
%define rpm_rel		1

%if !%{empty_package}
# Patch sources below. DO NOT REMOVE THIS LINE.
#
# https://bugzilla.redhat.com/2219677
Source100: CVE-2023-3090.patch
#
# https://bugzilla.redhat.com/2216179
Source101: CVE-2023-3390-2.patch
#
# https://bugzilla.redhat.com/2221752
Source102: CVE-2023-35001.patch
#
# https://bugzilla.redhat.com/2217008
Source103: CVE-2023-35788.patch
#
# https://bugzilla.redhat.com/2225664
Source104: CVE-2023-3776.patch
#
# https://bugzilla.redhat.com/2228798
Source105: CVE-2023-4004.patch
# End of patch sources. DO NOT REMOVE THIS LINE.
%endif

%define sanitized_rpm_rel	%{lua: print((string.gsub(rpm.expand("%rpm_rel"), "%.", "_")))}
%define sanitized_kernel_ver   %{lua: print((string.gsub(string.gsub(rpm.expand("%kernel_ver"), '.el8_?\%d?', ""), "%.", "_")))}
%define kernel_ver_arch        %{kernel_ver}.%{_arch}

Name:		kpatch-patch-%{sanitized_kernel_ver}
Version:	%{rpm_ver}
Release:	%{rpm_rel}%{?dist}

%if %{empty_package}
Summary:	Initial empty kpatch-patch for kernel-%{kernel_ver_arch}
%else
Summary:	Live kernel patching module for kernel-%{kernel_ver_arch}
%endif

Group:		System Environment/Kernel
License:	GPLv2
ExclusiveArch:	x86_64 ppc64le

Conflicts:	%{name} < %{version}-%{release}

Provides:	kpatch-patch = %{kernel_ver_arch}
Provides:	kpatch-patch = %{kernel_ver}

%if !%{empty_package}
Requires:	systemd
%endif
Requires:	kpatch >= 0.6.1-1
Requires:	kernel-uname-r = %{kernel_ver_arch}

%if !%{empty_package}
BuildRequires:	patchutils
BuildRequires:	kernel-devel = %{kernel_ver}
BuildRequires:	kernel-debuginfo = %{kernel_ver}

# kernel build requirements, generated from:
#   % rpmspec -q --buildrequires kernel.spec | sort | awk '{print "BuildRequires:\t" $0}'
# with arch-specific packages moved into conditional block
BuildRequires:  asciidoc
BuildRequires:  audit-libs-devel
BuildRequires:  bash
BuildRequires:  bc
BuildRequires:  binutils
BuildRequires:  binutils-devel
BuildRequires:  bison
BuildRequires:  bpftool
BuildRequires:  bzip2
BuildRequires:  clang
BuildRequires:  coreutils
BuildRequires:  diffutils
BuildRequires:  dwarves
BuildRequires:  elfutils
BuildRequires:  elfutils-devel
BuildRequires:  findutils
BuildRequires:  flex
BuildRequires:  gawk
BuildRequires:  gcc
BuildRequires:  gettext
BuildRequires:  git
BuildRequires:  gzip
BuildRequires:  hmaccalc
BuildRequires:  hostname
BuildRequires:  java-devel
BuildRequires:  kabi-dw
BuildRequires:  kmod
BuildRequires:  libbabeltrace-devel
BuildRequires:  libbpf-devel
BuildRequires:  libcap-devel
BuildRequires:  libcap-ng-devel
BuildRequires:  libmnl-devel
BuildRequires:  libnl3-devel
BuildRequires:  llvm
BuildRequires:  m4
BuildRequires:  make
BuildRequires:  ncurses-devel
BuildRequires:  net-tools
BuildRequires:  newt-devel
BuildRequires:  nss-tools
BuildRequires:  numactl-devel
BuildRequires:  openssl
BuildRequires:  openssl-devel
BuildRequires:  patch
BuildRequires:  pciutils-devel
BuildRequires:  perl-Carp
BuildRequires:  perl-devel
BuildRequires:  perl(ExtUtils::Embed)
BuildRequires:  perl-generators
BuildRequires:  perl-interpreter
BuildRequires:  python3-devel
BuildRequires:  python3-docutils
BuildRequires:  redhat-rpm-config
BuildRequires:  rpm-build
BuildRequires:  rsync
BuildRequires:  tar
BuildRequires:  which
BuildRequires:  xmlto
BuildRequires:  xz
BuildRequires:  xz-devel
BuildRequires:  zlib-devel

%ifarch x86_64
BuildRequires:	pesign >= 0.10-4
%endif

%ifarch ppc64le
BuildRequires:	gcc-plugin-devel
%endif

Source0:	https://github.com/dynup/kpatch/archive/v%{kpatch_ver}.tar.gz

Source10:	kernel-%{kernel_ver}.src.rpm

# kpatch-build patches

%global _dupsign_opts --keyname=rhelkpatch1

%define builddir	%{_builddir}/kpatch-%{kpatch_ver}
%define kpatch		%{_sbindir}/kpatch
%define kmoddir 	%{_usr}/lib/kpatch/%{kernel_ver_arch}
%define kinstdir	%{_sharedstatedir}/kpatch/%{kernel_ver_arch}
%define patchmodname	kpatch-%{sanitized_kernel_ver}-%{version}-%{sanitized_rpm_rel}
%define patchmod	%{patchmodname}.ko

%define _missing_build_ids_terminate_build 1
%define _find_debuginfo_opts -r
%undefine _include_minidebuginfo
%undefine _find_debuginfo_dwz_opts

%description
This is a kernel live patch module which can be loaded by the kpatch
command line utility to modify the code of a running kernel.  This patch
module is targeted for kernel-%{kernel_ver}.

%prep
%autosetup -n kpatch-%{kpatch_ver} -p1

%build
kdevdir=/usr/src/kernels/%{kernel_ver_arch}
vmlinux=/usr/lib/debug/lib/modules/%{kernel_ver_arch}/vmlinux

# kpatch-build
make -C kpatch-build

# patch module
for i in %{sources}; do
	[[ $i == *.patch ]] && patch_sources="$patch_sources $i"
done
export CACHEDIR="%{builddir}/.kpatch"
kpatch-build/kpatch-build --non-replace -n %{patchmodname} -r %{SOURCE10} -v $vmlinux --skip-cleanup $patch_sources || { cat "${CACHEDIR}/build.log"; exit 1; }


%install
installdir=%{buildroot}/%{kmoddir}
install -d $installdir
install -m 755 %{builddir}/%{patchmod} $installdir


%files
%{_usr}/lib/kpatch


%post
%{kpatch} install -k %{kernel_ver_arch} %{kmoddir}/%{patchmod}
chcon -t modules_object_t %{kinstdir}/%{patchmod}
sync
if [[ %{kernel_ver_arch} = $(uname -r) ]]; then
	cver="%{rpm_ver}_%{rpm_rel}"
	pname=$(echo "kpatch_%{sanitized_kernel_ver}" | sed 's/-/_/')

	lver=$({ %{kpatch} list | sed -nr "s/^${pname}_([0-9_]+)\ \[enabled\]$/\1/p"; echo "${cver}"; } | sort -V | tail -1)

	if [ "${lver}" != "${cver}" ]; then
		echo "WARNING: at least one loaded kpatch-patch (${pname}_${lver}) has a newer version than the one being installed."
		echo "WARNING: You will have to reboot to load a downgraded kpatch-patch"
	else
		%{kpatch} load %{patchmod}
	fi
fi
exit 0


%postun
%{kpatch} uninstall -k %{kernel_ver_arch} %{patchmod}
sync
exit 0

%else
%description
This is an empty kpatch-patch package which does not contain any real patches.
It is only a method to subscribe to the kpatch stream for kernel-%{kernel_ver}.

%files
%doc
%endif

%changelog
* Mon Sep 11 2023 Yannick Cote <ycote@redhat.com> [1-1.el8_8]
- kernel: netfilter: use-after-free due to improper element removal in nft_pipapo_remove() [2228798] {CVE-2023-4004}
- kernel: net/sched: cls_fw component can be exploited as result of failure in tcf_change_indev function [2225664] {CVE-2023-3776}
- kernel: cls_flower: out-of-bounds write in fl_set_geneve_opt() [2217008] {CVE-2023-35788}
- kernel: nf_tables: stack-out-of-bounds-read in nft_byteorder_eval() [2221752] {CVE-2023-35001}
- kernel: UAF in nftables when nft_set_lookup_global triggered after handling named and anonymous sets in batch requests [2216179] {CVE-2023-3390}
- kernel: ipvlan: out-of-bounds write caused by unclear skb->cb [2219677] {CVE-2023-3090}

* Tue Jul 25 2023 Yannick Cote <ycote@redhat.com> [0-0.el8]
- An empty patch to subscribe to kpatch stream for kernel-4.18.0-477.21.1.el8_8 [2226157]
