#!/usr/bin/env python
# mountlib.py - MOUNT library for python

import rpc
from xdrlib import Error as XDRError
import mount_const
from mount_const import *
import mount_type
from mount_type import *
from mount_pack import *
import time
import struct
import socket
import sys

AuthSys = rpc.SecAuthSys(0,'jupiter',103558,100,[])

class MountException(rpc.RPCError):
    pass

#A MOUNT procedure returned an error
class BadMountRes(MountException):
    def __init__(self, errcode, msg=None):
        self.errcode = errcode
        if msg:
            self.msg = msg + ': '
        else:
            self.msg = ''
    def __str__(self):
        return self.msg + "should return MNT3_OK, instead got %s" % \
            (mountstat3[self.errcode])


class MountClient(rpc.RPCClient):
    def __init__(self, id, host='localhost', port=300, homedir=['pynfs'],
            sec_list=[AuthSys], opts = None):
        self.ipv6 = getattr(opts, 'ipv6', False)
        self.packer = MOUNTPacker()
        self.unpacker = MOUNTUnpacker('')
        self.homedir = homedir
        self.id = id
        self.opts = opts
        # Mounting generally requires a low port
        #uselowport = getattr(opts, "secure", False)
        uselowport = True
        rpc.RPCClient.__init__(self, host, port, program=MOUNT_PROGRAM,
            version=MOUNT_V3, sec_list=sec_list,
            uselowport=uselowport,ipv6=self.ipv6)
        self.server_address = (host, port)
        print "seclist = ", sec_list

    # XXX Mount version - assuming MOUNT V3
    def mount_pack(self, procedure, data):
        p = self.packer

        if procedure == MOUNTPROC3_NULL:
            pass
        elif procedure == MOUNTPROC3_MNT:
            p.pack_dirpath(data)
        elif procedure == MOUNTPROC3_DUMP:
            pass
        elif procedure == MOUNTPROC3_UMNT:
            p.pack_dirpath(data)
        elif procedure == MOUNTPROC3_UMNTALL:
            pass
        elif procedure == MOUNTPROC3_EXPORT:
            pass
        else:
            raise XDRError, 'bad switch=%s' % procedure

    # XXX Fancy unpacking, into status, data, etc
    def mount_unpack(self, procedure):
        un_p = self.unpacker

        if procedure == MOUNTPROC3_NULL:
            return
        elif procedure == MOUNTPROC3_MNT:
            return un_p.unpack_mountres3()
        elif procedure == MOUNTPROC3_DUMP:
            return un_p.unpack_mountlist()
        elif procedure == MOUNTPROC3_UMNT:
            return
        elif procedure == MOUNTPROC3_UMNTALL:
            return
        elif procedure == MOUNTPROC3_EXPORT:
            return un_p.unpack_exports()
        else:
            raise XDRError, 'bad switch=%s' % procedure

    def mount_call(self, procedure, data=''):
        # Pack Request
        p = self.packer
        un_p = self.unpacker
        p.reset()

        self.mount_pack(procedure, data)

        # Make Call
        res = self.call(procedure, p.get_buffer())

        # Unpack Reply
        un_p.reset(res)
        res = self.mount_unpack(procedure)
        un_p.done()

        # XXX Error checking?
        return res

    """
    BASIC MOUNT OPERATIONS
    """

    def mount_null(self):
        return self.mount_call(mount_const.MOUNTPROC3_NULL)
    def mount_mnt(self, path):
        return self.mount_call(mount_const.MOUNTPROC3_MNT, path)
    def mount_dump(self):
        return self.mount_call(mount_const.MOUNTPROC3_DUMP)
    # XXX Ops 3 and 4
    def mount_export(self):
        return self.mount_call(mount_const.MOUNTPROC3_EXPORT)

    """
    UTILITY FUNCTIONS
    """

    # Verify a MOUNT call was successful,
    # raise BadMountRes otherwise
    def mount_check_result(self, res, msg=None):
        if not res.fhs_status:
            return
        raise BadMountRes(res.fhs_status, msg)

    def mount_getfh(self, path):
        res = self.mount_mnt(path)

        self.mount_check_result(res, "MNT")
        return res.mountinfo.fhandle
