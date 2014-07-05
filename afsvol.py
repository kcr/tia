#!/usr/bin/python3


import sys
import os
import struct
import collections
import glob


VolHeader = collections.namedtuple(
    'VolHeader',
    ['magic', 'version', 'id', 'parent', 'volumeInfo', 'smallVnodeIndex',
     'largeVnodeIndex', 'volumeAcl', 'volumeMountTable', 'linkTable',
     'reserved'])


def readvolheader(filename):
    # viz openafs/src/vol/volume.h:343
    vh = struct.unpack('=19I', open(filename, 'rb').read())
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
    path = os.path.join('AFSIDat', flipb64(vh.id & 0xff), flipb64(vh.id))
    vno = i & NAMEI_VNODEMASK
    if vno == NAMEI_VNODEMASK:
        path = os.path.join(path, 'special')
    else:
        path = os.path.join(
            path, flipb64(vno >> 14 & 0xff), flipb64(vno >> 9 & 0x1ff))
    path = os.path.join(path, flipb64(i))
    return path


def String(x):
    f = x.find(b'\0')
    if f > -1:
        x = x[:f]
    return x.decode()


def VolumeType(x):
    if x == 0:
        return 'RWrite'
    elif x == 1:
        return 'ROnly'
    elif x == 2:
        return 'Backup'
    raise ValueError('Illegal volume type')


def Match(v):
    return lambda x: x == v


def readvoldiskdata(vicep, vh):
    # viz openafs/src/vol/volume.h:373
    fields = [
        ('I', 'magic', int),
        ('I', 'version', int),
        ('I', 'id', int),
        ('32s', 'name', String),
        ('?', 'inUse', bool),
        ('?', 'inService', bool),
        ('?', 'blessed', bool),
        ('?', 'needsSalvaged', bool),
        ('I', 'uniquifier', int),
        ('i', 'type', VolumeType),
        ('I', 'parentId', int),
        ('I', 'cloneId', int),
        ('I', 'backupId', int),
        ('I', 'restoredFromId', int),
        ('?', 'needsCallback', bool),
        ('B', 'destroyMe', Match(0xD3)),
        ('B', 'dontSalvage', Match(0xE5)), # 0xE6 on D/UX on Alphas, apparently?
        ('B', 'reserveb3', int, 1),
        ('6I', 'reserved1', int, 6),
        ('i', 'maxquota', int),
        ('i', 'minquota', int),
        ('i', 'maxfiles', int),
        ('I', 'accountint', int),
        ('I', 'owner', int),
        ('8i', 'reserved2', int, 8),
        ('i', 'filecount', int),
        ('i', 'diskused', int),
        ('i', 'dayUse', int),
        ('7i', 'weekUse', int, 7),
        ('I', 'dayUseDate', int),
        ('I', 'volUpdateCounter', int),
        ('10I', 'reserved3', int, 10),
        ('I', 'creationDate', int),
        ('I', 'accessDate', int),
        ('I', 'updateDate', int),
        ('I', 'expirationDate', int),
        ('I', 'backupDate', int),
        ('I', 'copyDate', int),
        ('I', 'stat_initialized', int),
        ('7I', 'reserved4', int, 7),
        ('128s', 'offlineMessage', String),
        ('4I', 'stat_reads', int, 4),
        ('4I', 'stat_writes', int, 4),
        ('6I', 'stat_fileSameAuthor', int, 6),
        ('6I', 'stat_fileDiffAuthor', int, 6),
        ('6I', 'stat_dirSameAuthor', int, 6),
        ('6I', 'stat_dirDiffAuthor', int, 6),
        ]
    fmt = ''.join(f[0] for f in fields)
    data = open(os.path.join(vicep, afsiname(vh, vh.volumeInfo)), 'rb').read()
    unpacked = struct.unpack(fmt, data)
    l = []
    for f in fields:
        if len(f) == 3:
            l.append(f[2](unpacked[0]))
            unpacked = unpacked[1:]
        elif len(f) == 4:
            l.append([f[2](y) for y in unpacked[:f[3]]])
            unpacked = unpacked[f[3]:]
    assert unpacked == ()

    VolDiskData = collections.namedtuple('VolDiskData', [f[1] for f in fields])

    ret = VolDiskData._make(l)
    if ret.magic != 0x78a1b2c5:
        raise ValueError('Not an AFS VolumeDiskData blob')
    return ret


def main():
    for vicep in glob.glob('/vicep*'):
        for vhpath in glob.glob(os.path.join(vicep, 'V*.vol')):
            vh = readvolheader(vhpath)
            vdd = readvoldiskdata(vicep, vh)
            print (vdd)

if __name__ == '__main__':
    main()
