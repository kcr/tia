#!/usr/bin/python3


import struct
import collections
import sys


VolHeader = collections.namedtuple(
    'VolHeader',
    ['magic', 'version', 'id', 'parent', 'volumeInfo', 'smallVnodeIndex',
     'largeVnodeIndex', 'volumeAcl', 'volumeMountTable', 'linkTable',
     'reserved'])

def readvolheader(filename):
    vh = struct.unpack('=19I', open(filename, 'rb').read())
    ## struct versionStamp ## struct versionStamp {		/* Version stamp for critical volume files */
    ##     bit32 magic;		/* Magic number */
    ##     bit32 version;		/* Version number of this file, or software
    ## 				 * that created this file */
    ## } stamp;	/* Must be first field */
    ## VolumeId id;		/* Volume number */
    ## VolumeId parent;		/* Read-write volume number (or this volume
	## 			 * number if this is a read-write volume) */
    ## afs_int32 volumeInfo_lo;
    ## afs_int32 smallVnodeIndex_lo;
    ## afs_int32 largeVnodeIndex_lo;
    ## afs_int32 volumeAcl_lo;
    ## afs_int32 volumeMountTable_lo;
    ## afs_int32 volumeInfo_hi;
    ## afs_int32 smallVnodeIndex_hi;
    ## afs_int32 largeVnodeIndex_hi;
    ## afs_int32 volumeAcl_hi;
    ## afs_int32 volumeMountTable_hi;
    ## afs_int32 linkTable_lo;
    ## afs_int32 linkTable_hi;
    ## /* If you add fields, add them before here and reduce the size of  array */
    ## bit32 reserved[3];
    ret = VolHeader._make(
        list(vh[:4]) +
        [(vh[i + 9] << 32) | vh[i + 4] for i in range(5)] +
        [(vh[15] << 32) | vh[14], vh[16:]])
    if ret.magic != 0x88a1bb3c or ret.version != 1:
        raise ValueError('Not an AFS volume header')
    return ret


def flipb64(i):
    if i < 0:
        raise ValueError('flipbase64 only unsigned numbers')
    # viz openafs/src/util/flipbase64.c:50
    if sys.platform == 'darwin':
        # cases-insensitive filesystem, anyone?
        xlate='!"#$%&()*+,-0123456789:;<=>?@[]^_`abcdefghijklmnopqrstuvwxyz{|}~'
    else:
        xlate='+=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    s = ''
    if i == 0:
        s += xlate[0]
    while i:
        s += xlate[i & 0x3f]
        i = i >> 6
    return s

def afsiname(vh, i):
    NAMEI_VNODEMASK = 0x003ffffff
    path = os.path.join('AFSIDat', flipb64(vh.id & 0xff), flipb64(v.id))
    vno = i & NAMEI_VNODEMASK
    if vno == NAMEI_VNODEMASK:
        path = os.path.join(path, 'special')
    else:
        path = os.path.join(
            path, flipb64(vno >> 14 & 0xff), flipb64(vno >> 9 & 0x1ff))
    path = os.path.join(path, flipb64(i))
    return path
