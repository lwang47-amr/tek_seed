#!/usr/bin/python3

#
# Add Ubuntu 20.10 support, Remember qemu need 2048mb
# qemu-system-x86_64 -boot d -cdrom ek-live.iso -nographic -m 2048
#
import os, sys, stat
import platform
import tek_seed_xml
import subprocess
from subprocess import DEVNULL
from subprocess import PIPE
import argparse
import shutil
import distro    # apt install python3-distro (ubuntu), pip install distro (conda)

from string import Template
xml_file='./tek_seed.xml'
xsd_file='./tek_seed.xsd'
req_pkgs = ['livecd-rootfs','systemd-container','grub-pc-bin', 
    'xorriso', 'software-properties-common', 'wget', 'git', 
    'cloud-image-utils', 'libguestfs-tools', 'ssh', 
    'python-lxml','python-pexpect','usb-pack-efi']

stat = {}



def check_installed_package_ubuntu():


    p = subprocess.Popen('apt list --installed', shell=True, 
        stdout=PIPE, stderr=PIPE)

    all_pkgs = p.communicate()[0].decode('utf-8')

    print('Checking Ubuntu packages...')
    for i in req_pkgs:
        if i in all_pkgs:
            print('   {} installed'.format(i))
        else:
            print('ERROR! Package {} is NOT installed!!'.format(i))
        return False
    return True


def get_xml_tag(tag, exit_on_error=False):

    result = tek_seed_xml.get_xml(xml_file, xsd_file, tag)

    if type(result) is list:
        result=result[0]   
    else:
        print("Error: tag '{}' not found in {}".format(tag, xml_file))
        if exit_on_error is True:
            sys.exit(0)

    return result.strip()


def live_build():

    lb_cmd     = get_xml_tag('live-build', True)
    live_dir   = get_xml_tag('live_dir', True)
    http_proxy = get_xml_tag('http_proxy', False)
    lb_proxy=""

    if http_proxy:
        lb_proxy="--apt-http-proxy {}".format(http_proxy)
    
    
    t = Template(lb_cmd)
    lb_cmd = t.substitute(LIVE_DIR=live_dir, LB_PROXY=lb_proxy)
    return lb_cmd


def systemd_nspawn():

    nspawn_cmd   = get_xml_tag('systemd-nspawn', True)
    live_dir     = get_xml_tag('live_dir', True)
    http_proxy   = get_xml_tag('http_proxy', False)
    packages     = get_xml_tag('systemd-nspawn-packages', True)
    kern_version = get_xml_tag('kernel_20.10', True)
    ns_proxy=""

    if http_proxy:
        ns_proxy="--setenv=http_proxy={} --setenv=https_proxy={}".format(http_proxy, http_proxy)

    packages = packages.replace("${KERN_VERSION}", kern_version)
    nspawn_cmd = nspawn_cmd.replace("${KERN_VERSION}", kern_version)
    nspawn_cmd = nspawn_cmd.replace("${LIVE_DIR}", live_dir)
    nspawn_cmd = nspawn_cmd.replace("${NS_PROXY}", ns_proxy)
    nspawn_cmd = nspawn_cmd.replace("${PACKAGES}", packages)
    return nspawn_cmd


def do_customize():

    cust_cmd     = get_xml_tag('customize', True)
    live_dir     = get_xml_tag('live_dir', True)
    kern_version = get_distro_version()

    # Cannot do template substition due to $TERM
    cust_cmd = cust_cmd.replace("${LIVE_DIR}", live_dir)
    cust_cmd = cust_cmd.replace("${KERN_VERSION}", kern_version)
    return cust_cmd


def create_iso():

    iso_cmd = get_xml_tag('create-iso', True)
    live_dir = get_xml_tag('live_dir', True)
    kern_version = get_distro_version()

    t = Template(iso_cmd)
    iso_cmd = t.substitute(LIVE_DIR=live_dir)
    return iso_cmd


def unpack_usb_pack():

    efi_file = '/usr/share/mkusb/usb-pack_efi-0.tar.xz'
    if not os.path.exists(efi_file):
        print('File {} not found!'.format(efi_file))
        sys.exit(1)

    if os.path.exists('usb-pack_efi'):
        return 0

    os.mkdir('usb-pack_efi')
    
    #ret = os.system('tar xfz /usr/share/mkusb/usb-pack_efi.tar.gz -C usb-pack_efi')
    ret = os.system('tar -xf {} -C usb-pack_efi'.format(efi_file))
    if ret != 0:
        prrint('unpack_usb_pack error in tar {}'.format(efi_file))
        sys.exit(1)
    os.mkdir('usb-pack_efi/iso')
    return 0


def create_usb():

    usb_cmd  = get_xml_tag('create-usb', True)
    live_dir = get_xml_tag('live_dir', True)
    usb_dev  = get_xml_tag('usb_dev', True)
    live_mnt = get_xml_tag('live_mnt', True)
    kern_version = get_xml_tag('kernel_20.10', True)
    part_a_size = get_xml_tag('usb_part_a_size', True)
    part_b_size = get_xml_tag('usb_part_b_size', True)

    # Get usb-pack_efi folder
    unpack_usb_pack()

    # Get current EK DIR
    ek_dir = os.path.dirname(os.getcwd())
    curr_dir = os.getcwd()

    #t = Template(usb_cmd)
    #usb_cmd = t.substitute(LIVE_DIR=live_dir, DISK=usb_dev, 
    #           MNT=live_mnt, EK_DIR=ek_dir, CURR_DIR=curr_dir)
    usb_cmd = usb_cmd.replace("${LIVE_DIR}", live_dir)
    usb_cmd = usb_cmd.replace("${DISK}", usb_dev)
    usb_cmd = usb_cmd.replace("${CURR_DIR}", curr_dir)
    usb_cmd = usb_cmd.replace("${MNT}", live_mnt)
    usb_cmd = usb_cmd.replace("${EK_DIR}", ek_dir)
    usb_cmd = usb_cmd.replace("${KERN_VERSION}", kern_version)
    usb_cmd = usb_cmd.replace("${PART_A_SIZE}", part_a_size)
    usb_cmd = usb_cmd.replace("${PART_B_SIZE}", part_b_size)
    
    return usb_cmd

def create_vnni():

    vnni_cmd = get_xml_tag('vnni', True)
    usb_dev  = get_xml_tag('usb_dev', True)
    live_mnt = get_xml_tag('live_mnt', True)
    vnni_cmd = vnni_cmd.replace("${DISK}", usb_dev)
    vnni_cmd = vnni_cmd.replace("${MNT}", live_mnt)
    return vnni_cmd

def show_status():

    # global stat
    status = "\n\
System Information               \n\
   TEK Seed version= {}          \n\
   Linux distro    = {}          \n\
   Disto version   = {}          \n\n\
Options and Configurations       \n\
   USB DISK*       = {}  ({} GB) \n\
   HTTP_PROXY      = {}          \n\
   HTTPS_PROXY     = {}          \n\
   CURR_DIR        = {}          \n\
   LIVE_DIR        = {}          \n\
   USB_MNT_POINT   = {}          \n\
   NFVI_EK_BLD_DIR = {}          \n\
   KERN_VERSION    = {}\n".format(
    stat['xseed_ver'],
    stat['dist'][0], 
    stat['dist'][1], 
    stat['usb'], stat['usb_size'],
    stat['proxy'], 
    stat['proxy'],
    stat['curr_dir'], 
    stat['live_dir'], 
    stat['live_mnt'], 
    stat['build_dir'],
    stat['kern_version'])

    print(status)
    return 0


def get_distro_version():

    _,_ver_,_ = distro.linux_distribution()
    if _ver_ == '20.04': 
       kern_version = get_xml_tag('kernel_20.04', True)
    elif _ver_ == '20.10':
       kern_version = get_xml_tag('kernel_20.10', True)
    else:
       print('do_customize(): failed to get distro version') 
       sys.exit(1)

    return kern_version



def helper():
    global req_pkgs

    print("\
Usage:                                                          \n\
   python3 {}                                                 \n\n\
Description:                                                    \n\
   Intel TEK Seed is used to create a Live USB device for NFVI, DLBoost, etc. It supports \n\
   Ubuntu 20.04 and later distro (see below required packages to install). During execution, \n\
   Intel TEK Seed relies on Ubuntu live-build system to create a live environment and use \n\
   a light-weight namespace container to customize more. Optionally, it goes to download  \n\
   BKC software and/or compose its automation test cases. Finally everything is packed to \n\
   an EFI bootable Live USB device. The USB contains two partitions, one ramdisk area for \n\
   LiveOS and one persistent partition for the rest of software stack.  \n\n\
   Notice root priviledge and network connection is always needed during execution, see \n\
   below configuration for proxy, DNS and other settings.                              \n\n\
Configuration Settings:                                                   \n\
   All configurtions are stored in tek_seed_xml, available to be directly editted.     \n\
Run-time Options:                                              \n\
   --clean           Clean all build/iso temp dir/files        \n\
   --help            Display usage                           \n\n\
Required privilege and Packages:                               \n\
   add-apt-repository -y ppa:mkusb/ppa                   \n\
   apt install -y {}                                    \n\n\
System devices:                                          \n\
   sudo parted -l | grep /dev/sd                           \n\n\
Examples:                                                \n\
   python3 {} --help \n\n".format(sys.argv[0], req_pkgs, sys.argv[0]))

    sys.exit(0)


if __name__ == '__main__':


    if os.getuid() != 0:
        print('\nroot priv is required to run {}!!\n'.format(sys.argv[0]))
        exit()

    parser = argparse.ArgumentParser()  # (description="my usage", usage=helper())
    parser.add_argument('-c', '--clean', help='Clean build dir', action='store_true')
    parser.add_argument('-u', '--usage', help='Show usage', action='store_true')
    args = parser.parse_args()

    # global stat
    stat['xseed_ver']    = '0.7'
    stat['dist']         = distro.linux_distribution() 
    stat['proxy']        = get_xml_tag('http_proxy', True)
    stat['curr_dir']     = os.getcwd()
    stat['live_dir']     = get_xml_tag('live_dir', True)
    stat['live_mnt']     = get_xml_tag('live_mnt', True)
    stat['build_dir']    = get_xml_tag('build_dir', True)
    stat['kern_version'] = get_distro_version()
    stat['usb']          = get_xml_tag('usb_dev', True)

    du = shutil.disk_usage(stat['usb'])
    stat['usb_size'] = round(du.total/1024**3)

    # show usage
    if args.usage:
        helper()

    # clean previous built
    if args.clean:
        if os.path.exists(stat['live_dir']):
            print('Cleaning {}...'.format(stat['build_dir']))
            shutil.rmtree(stat['live_dir'])
        print('{} cleaned'.format(stat['build_dir']))
        sys.exit(0)



    show_status()

    '''
    s = "Formatting {} ({} GB)... ALL data will be lost! ".format(
        stat['usb'], stat['usb_size']) + "Continue (y/n)? "
    yn=input(s)
        '''

    # Build EK command sets
    ek_dict = {
        'live-build':     {'func': live_build, 'cmd':[]}, 
        'systemd-nspawn': {'func': systemd_nspawn, 'cmd':[]},
        'customize':      {'func': do_customize, 'cmd': []}, 
        "create-iso":     {'func': create_iso, 'cmd': []},
        "create-usb":     {'func': create_usb, 'cmd': []},
        "create-vnni":    {'func': create_vnni, 'cmd': []}
    }

    # Get user inputs


    for k, v in ek_dict.items():
        ek_dict[k]['cmd'] = ek_dict[k]['func']()

    seq = 1
    for k, v in ek_dict.items():
        fname='ek{}.sh'.format(seq)
        with open(fname, 'w') as f:
            f.write(v['cmd'])

        # Make shell executable
        os.chmod(fname, 0o755)
        print('bash file {} created for {}'.format(fname, k))
        seq += 1

    print('{} successfully completed!'.format(sys.argv[0]))
    sys.exit(0)

