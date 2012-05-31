#!/usr/bin/env python
# rpcblib.py - RPCBIND and PORTMAP library for python

# Implemented by hand by Zack Kirsch, but could be easily auto-generated

import rpc
from xdrlib import Error as XDRError
from rpcb_const import *
from rpcb_type import *
from rpcb_pack import *
import time
import struct
import socket
import sys

AuthSys = rpc.SecAuthSys(0,'jupiter',103558,100,[])

class RpcbException(rpc.RPCError):
    pass

class RpcbClient(rpc.RPCClient):
    def __init__(self, id, host='localhost', port=RPCB_PORT, homedir=['pynfs'],
            sec_list=[AuthSys], opts = None):
        self.ipv6 = getattr(opts,"ipv6", False)
        self.packer = RPCBPacker()
        self.unpacker = RPCBUnpacker('')
        self.homedir = homedir
        self.id = id
        self.opts = opts
        self.uselowport = getattr(opts, "secure", False)
        self.host = host
        self.port = port
        self.sec_list = sec_list

    def rpcb_pack(self, version, procedure, data):
        if version == PMAP_VERS:
            self.rpcb2_pack(procedure, data)
        elif version == RPCBVERS:
            self.rpcb3_pack(procedure, data)
        elif version == RPCBVERS4:
            self.rpcb4_pack(procedure, data)
        else:
            raise RpcbException, 'bad version = %s' % version

    def rpcb2_pack(self, procedure, data):
        p = self.packer

        if procedure == PMAPPROC_NULL:
            pass
        elif procedure == PMAPPROC_SET:
            p.pack_mapping(data)
        elif procedure == PMAPPROC_UNSET:
            p.pack_mapping(data)
        elif procedure == PMAPPROC_GETPORT:
            p.pack_mapping(data)
        elif procedure == PMAPPROC_DUMP:
            pass
        elif procedure == PMAPPROC_CALLIT:
            p.pack_call_args(data)
        else:
            raise XDRError, 'bad switch=%s' % procedure

    # XXX TODO
    def rpcb3_pack(self, procedure, data):
        p = self.packer
        raise XDRError, 'unimplemented'

    def rpcb4_pack(self, procedure, data):
        p = self.packer

        if procedure == const.RPCBPROC_SET:
            p.pack_rpcb(data)
        elif procedure == RPCBPROC_UNSET:
            p.pack_rpcb(data)
        elif procedure == RPCBPROC_GETADDR:
            p.pack_rpcb(data)
        elif procedure == RPCBPROC_DUMP:
            pass
        elif procedure == RPCBPROC_GETTIME:
            pass
        elif procedure == RPCBPROC_UADDR2TADDR:
            p.pack_astring(data)
        elif procedure == RPCBPROC_TADDR2UADDR:
            p.pack_netbuf(data)
        elif procedure == RPCBPROC_GETVERSADDR:
            p.pack_rpcb(data)
        elif procedure == RPCBPROC_INDIRECT:
            p.pack_rpcb_rmtcallargs(data)
        elif procedure == RPCBPROC_GETADDRLIST:
            p.pack_rpcb(data)
        elif procedure == RPCBPROC_GETSTAT:
            pass
        else:
            raise XDRError, 'bad switch=%s' % procedure

    def rpcb_unpack(self, version, procedure):
        if version == PMAP_VERS:
            return self.rpcb2_unpack(procedure)
        elif version == RPCBVERS:
            return self.rpcb3_unpack(procedure)
        elif version == RPCBVERS4:
            return self.rpcb4_unpack(procedure)
        else:
            raise RpcbException, 'bad version = %s' % version

    def rpcb2_unpack(self, procedure):
        un_p = self.unpacker

        if procedure == PMAPPROC_NULL:
            pass
        elif procedure == PMAPPROC_SET:
            return un_p.unpack_bool()
        elif procedure == PMAPPROC_UNSET:
            return un_p.unpack_bool()
        elif procedure == PMAPPROC_GETPORT:
            return un_p.unpack_uint()
        elif procedure == PMAPPROC_DUMP:
            return un_p.unpack_pmaplist()
        elif procedure == PMAPPROC_CALLIT:
            return un_p.unpack_call_result()
        else:
            raise XDRError, 'bad switch=%s' % procedure

    # XXX TODO
    def rpcb3_unpack(self, procedure):
        un_p = self.unpacker
        raise XDRError, 'unimplemented'

    # XXX Fancy unpacking, into status, data, etc
    def rpcb4_unpack(self, procedure):
        un_p = self.unpacker

        if procedure == const.RPCBPROC_SET:
            return un_p.unpack_bool()
        elif procedure == RPCBPROC_UNSET:
            return un_p.unpack_bool()
        elif procedure == RPCBPROC_GETADDR:
            return un_p.unpack_astring()
        elif procedure == RPCBPROC_DUMP:
            return un_p.unpack_rpcblist_ptr()
        elif procedure == RPCBPROC_GETTIME:
            return un_p.unpack_unsigned()
        elif procedure == RPCBPROC_UADDR2TADDR:
            return un_p.unpack_netbuf()
        elif procedure == RPCBPROC_TADDR2UADDR:
            return un_p.unpack_astring()
        elif procedure == RPCBPROC_GETVERSADDR:
            return un_p.unpack_astring()
        elif procedure == RPCBPROC_INDIRECT:
            return un_p.unpack_rpcb_rmtcallres()
        elif procedure == RPCBPROC_GETADDRLIST:
            return un_p.unpack_rpcb_entry_list_ptr()
        elif procedure == RPCBPROC_GETSTAT:
            return un_p.unpack_rpcb_stat_byvers()
        else:
            raise XDRError, 'bad switch=%s' % procedure

    def rpcb_call(self, version, procedure, data=''):
        rpc.RPCClient.__init__(self, self.host, self.port, program=RPCBPROG,
            version=version, sec_list=self.sec_list,
            uselowport=self.uselowport,ipv6=self.ipv6)

        # Pack Request
        p = self.packer
        un_p = self.unpacker
        p.reset()

        self.rpcb_pack(version, procedure, data)

        # Make Call
        res = self.call(procedure, p.get_buffer())

        # Unpack Reply
        un_p.reset(res)
        res = self.rpcb_unpack(version, procedure)
        un_p.done()

        # XXX Error checking?
        return res

    """
    Basic RPCB ops
    """
    # XXX Many are missing right now

    def rpcb2_getport(self, program, version, prot=IPPROTO_TCP, port=0):
        data = types.mapping()
        data.prog = program
        data.vers = version
        data.prot = prot
        data.port = port
        return self.rpcb_call(PMAP_VERS, PMAPPROC_GETPORT, data)

    def rpcb4_getaddr(self, program, version, netid="", addr="", owner=""):
        data = types.rpcb()
        data.r_prog = program
        data.r_vers = version
        data.r_netid = netid
        data.r_addr = addr
        data.r_owner = owner
        return self.rpcb_call(RPCBVERS4, RPCBPROC_GETADDR, data)

    """
    Utility functions
    """
