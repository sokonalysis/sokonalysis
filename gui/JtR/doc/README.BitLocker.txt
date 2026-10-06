This document is about cracking password protected BitLocker encrypted
volumes with JtR.

Step 1: Extract the hash
------------------------

In order to use the BitLocker-OpenCL format, you must produce a well-formatted
hash from your BitLocker encrypted image. Use the tool run/bitlocker2john.py to
extract hashes from password protected BitLocker encrypted volumes.
Usage: python3 bitlocker2john.py <bitlocker_image> [-o <bitlocker_partition_offset>]

It returns four output hashes with different prefixes:

* If the device was encrypted using the User Password authentication method,
  bitlocker2john prints these two hashes:
  * $bitlocker$0$... : it starts the User Password fast attack mode
  * $bitlocker$1$... : it starts the User Password attack mode with MAC verification (slower execution, no false positives)

* In any case, bitlocker2john prints these two hashes:
  * $bitlocker$2$... : it starts the Recovery Password fast attack mode
  * $bitlocker$3$... : it starts the Recovery Password attack mode with MAC verification (slower execution, no false positives)

Hash extraction example,

$ python3 bitlocker2john.py bitlocker_image -o 4194304

[+] BitLocker signature found: -FVE-FS-
[+] Identified volume GUID: 4967D63B-2E29-4AD8-8399-F6A339E3D001 = BitLocker
[+] FVE metadata info found at offsets ['0x2500000', '0x42500000', '0x82500000']

Parsing FVE block...

Parsing FVE metadata header...
Metadata size: 820
Volume GUID: F23E2E52-12F0-4066-94B6-F91C9A1A1D91
Encryption method: 0x80028002

Parsing FVE metadata entry...
Entry size: 68
Entry type: 0x7 = Computer description
Value type: 0x2 = UTF-16 string

Parsing description...
Info: DESKTOP-J5HJVN9 E: 12/08/2022

...

The following hashes were found:
$bitlocker$0$16$4a67bc123abedc43d60b3ece78ec6d1e$1048558$12$a015f77b68aed80103000000$60$2dbacf4710d3d42aa4f7baeedff85d72fc892f8f3457271901c0d2eccc3de890f081b3335740a5b5f1473892569ec0455d1aa2fd0075ac073a5f7b2a
$bitlocker$1$16$4a67bc123abedc43d60b3ece78ec6d1e$1048558$12$a015f77b68aed80103000000$60$2dbacf4710d3d42aa4f7baeedff85d72fc892f8f3457271901c0d2eccc3de890f081b3335740a5b5f1473892569ec0455d1aa2fd0075ac073a5f7b2a
$bitlocker$2$16$4b10ca85ab17a7419990d92f75abc848$1048558$12$a015f77b68aed80106000000$60$011e39cfd4dc9f647cef46b843347a3677c0706d3653f3477d44c72c8e36e8e02e010744dc384a419ff487a0190b42da0a29229d57a0bc3c6a7193f7
$bitlocker$3$16$4b10ca85ab17a7419990d92f75abc848$1048558$12$a015f77b68aed80106000000$60$011e39cfd4dc9f647cef46b843347a3677c0706d3653f3477d44c72c8e36e8e02e010744dc384a419ff487a0190b42da0a29229d57a0bc3c6a7193f7


Alternatively, run the compiled program bitlocker2john, which is normally
built from source along with the rest of John the Ripper and is included
pre-built in John the Ripper binary releases.

$ ../run/bitlocker2john minimalistic.raw  # operate on a disk image
Signature found at 0x00010003
Version: 8
Invalid version, looking for a signature with valid version...
Signature found at 0x02110000
Version: 2 (Windows 7 or later)
VMK entry found at 0x021100b6
Key protector with user password found
minimalistic.raw:$bitlocker$0$16$e221443f32c419b74504ed51b0d66dbf$1048576$12$704e12c6c...

Instead of running bitlocker2john directly on BitLocker encrypted devices
(e.g. /dev/sdb1), you may use the dd command to create a disk image of a
device encrypted with BitLocker

$ sudo dd if=/dev/disk2 of=disk_image conv=noerror,sync
+4030464+0 records in
+4030464+0 records out
+2063597568 bytes transferred in 292.749849 secs (7049013 bytes/sec)

For further details about User Password and Recovery Password attacks, please
refer to the Wiki page: https://openwall.info/wiki/john/OpenCL-BitLocker


Step 2: Attack!
---------------

Use the BitLocker-OpenCL format specifying the hash file:

$ ./john --format=bitlocker-opencl --wordlist=wordlist target_hash

Currently, this format is able to evaluate passwords having length between 8
(minimum password length) and 55 characters.

To avoid wasting compute resources, choose just one hash for this attack -
either $bitlocker$0$... or $bitlocker$1$...


Recovery Passwords (but you're out of luck cracking these, so just don't)
-------------------------------------------------------------------------

The mask you can use to generate Recovery Passwords is:

--mask=?d?d?d?d?d?d-?d?d?d?d?d?d-?d?d?d?d?d?d-?d?d?d?d?d?d-?d?d?d?d?d?d-?d?d?d?d?d?d-?d?d?d?d?d?d-?d?d?d?d?d?d

Please note that the number of possible Recovery Passwords is WAY too large, so
there's effectively NO CHANCE that this will find yours unless you recall
almost all of it (except for just a handful of digits) and replace most of the
"?d" above with the known digits.

Recovery Passwords are currently only supported by the BitLocker-OpenCL format
(for use on GPUs), not by the corresponding BitLocker CPU format, but like the
above paragraph says it's a controversial feature anyhow, which is unlikely to
ever help.

To avoid wasting compute resources, choose just one hash for this attack -
either $bitlocker$2$... or $bitlocker$3$...


Links
-----

Samples BitLocker images for testing are available at,

* https://github.com/kholia/libbde/tree/bitlocker2john/samples
* https://github.com/e-ago/bitcracker/tree/master/Images

Samples of User Password/Recovery Passwords dictionaries are available at
https://github.com/e-ago/bitcracker/tree/master/Dictionary

More information on BitLocker cracking can be found at,

* https://openwall.info/wiki/john/OpenCL-BitLocker
* https://github.com/e-ago/bitcracker
