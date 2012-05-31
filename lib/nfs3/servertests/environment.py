#
# environment.py for NFSV3
#
# Requires python 2.3
#
# Written by Zack Kirsch <zack@kirsch.org>
#

import time
import testmod
import rpc
import os
import socket

from nfs3.mountlib import *
from nfs3.mount_const import *
from nfs3.mount_type import *
from nfs3.nfs3lib import *
from nfs3.rpcblib import *
from nlm.nlm import *
from nsm.nsm import *

# NFSv3 environment, consists of:
# 1) RPCB to find protocol ports
# 2) MOUNT to get initial file handle
# 3) NFSv3 for testing
# 4) NLM for locking
# 5) NSM for monitoring hosts that are locking
# XXX Not all of these are actually implemented.

class Environment(testmod.Environment):
    def __init__(self, opts):
        self.sec1, sec2, sec3 = self._get_security(opts)
        rootsec = opts.flavor(0, opts.machinename, 0, 0, [0])

        # Get protocol port
        rpcb = RpcbClient('client1_pid%i' % os.getpid(), opts.server,
            sec_list=[self.sec1], opts=opts)
        mountport = rpcb.rpcb2_getport(MOUNT_PROGRAM, MOUNT_V3)
        self.nfs3port = rpcb.rpcb2_getport(NFS_PROGRAM, NFS_V3)
        
        self.mc = MountClient('client1_pid%i' % os.getpid(), opts.server,
            mountport, opts.path, sec_list=[self.sec1], opts=opts)
        self.rootclient = MountClient('client1_pid%i' % os.getpid(),
            opts.server, mountport, opts.path, sec_list=[rootsec], opts=opts)

        self.ipv6 = opts.ipv6

        # Only initialize NLM client if specified on command line
        # to work around BVT errors and the fact that this screws up the
        # client's rpc.lockd
        if opts.nlm and not opts.ipv6:
            nlmport = rpcb.rpcb2_getport(NLM_PROG, NLM4_VERS)
            self.nlm = NLM4Client('client1_pid%i' % os.getpid(), opts.server,
               nlmport, opts.path[-1], sec_list=[self.sec1], opts=opts)
        else:
            self.nlm = None

        # NSM is similar
        if opts.nsm:
            rpcb_local = RpcbClient('client2_pid%i' % os.getpid(), "localhost",
                sec_list=[self.sec1], opts=opts)
            nsmport = rpcb.rpcb2_getport(SM_PROG, SM_VERS)
            nsmport_local = rpcb_local.rpcb2_getport(SM_PROG, SM_VERS)
            self.nsm = NSMClient('client1_pid%i' % os.getpid(), opts.server,
                nsmport, sec_list=[self.sec1], opts=opts)
            self.nsm_local = NSMClient('client2_pid%i' % os.getpid(), "localhost",
                nsmport_local, sec_list=[self.sec1], opts=opts)
        else:
            self.nsm = None

        self.c1 = NFS3Client('client1_pid%i' % os.getpid(),
            opts.server, self.nfs3port, opts.path[-1], sec_list=[self.sec1], opts=opts)
        self.c2 = NFS3Client('client2_pid%i' % os.getpid(),
            opts.server, self.nfs3port, opts.path[-1], sec_list=[sec2], opts=opts)
        self.c3 = NFS3Client('client3_pid%i' % os.getpid(),
            opts.server, self.nfs3port, opts.path[-1], sec_list=[sec3], opts=opts)

        #if opts.secondserver:
        #    print "Using secondserver = %s" % opts.secondserver
        #    self.c1node2 = NFS4Client('client1_pid%i' % os.getpid(),
        #                         opts.secondserver, opts.port, opts.path,
        #                         sec_list=[self.sec1], opts=opts)
        #    self.c3node2 = NFS4Client('client3_pid%i' % os.getpid(),
        #                         opts.secondserver, opts.port, opts.path,
        #                         sec_list=[self.sec1], opts=opts)
        #    self.secondconns = [("clientid3", self.c3), ("clientid3-node2", self.c3node2)]
        #    self.secondconn = None
        #else:
        #    self.secondconns = [("clientid3", self.c3)]
        #    #self.secondconns = []
        #    self.secondconn = None

        self.longname = "a"*512
        self.uid = 0
        self.gid = 0
        self.pid = os.getpid()
        self.opts = opts
        self.filedata = "This is the file test data."
        self.linkdata = "/etc/X11"

    def _get_security(self, opts):
        if opts.security == 'none':
            return [opts.flavor(), opts.flavor()]
        elif opts.security == 'sys':
            sec1 = opts.flavor(0, opts.machinename, opts.uid, opts.gid, [])
            sec2 = opts.flavor(0, opts.machinename, opts.uid+1, opts.gid+1, [])
            sec3 = opts.flavor(0, opts.machinename, 10, 10, [])
            return [sec1, sec2, sec3]
        elif opts.security.startswith('krb5'):
            sec1 = opts.flavor(opts.service)
            sec2 = opts.flavor(opts.service)
            sec3 = opts.flavor(opts.service)
            return [sec1, sec2, sec3]
        else:
            raise 'Bad security %s' % opts.security

    """
    XXX These are defined for NFSv4, and could be defined for NFSv3 as
        well.
    """

    def init(self):
        """Run once before any test is run"""
        c = self.c1
        if self.opts.maketree:
            self._maketree()
        if self.opts.noinit:
            return

        # Make sure homedir is empty
        c.clean_dir(homedir_fh(self.mc, c))

    def _maketree(self):
        # Make the homedir which will contain all test files for v3 tests
        if self.opts.uid != 0 or self.opts.gid != 0:
            print "WARNING: need root for privileged mount port"

        c = self.c1
        mnt_fh = self.mc.mount_getfh('/' + '/'.join(self.mc.opts.path[:-1]))
        res = c.mkdir(mnt_fh, c.homedir, dir_mode_set=1, dir_mode_val=0777)
        checklist(res, [NFS3ERR_EXIST, NFS3_OK],
                  "Trying to create /%s," % '/'.join(self.opts.path))
        
    def finish(self):
        """Run once after all tests are run"""
        if self.opts.nocleanup:
            return
        c = self.c1
        # Null call twice so it's easier to pick out in a pcap
        c.null()
        c.null()
        self.c2.null()
        self.c3.null()

        # Clean the homedir
        c.clean_dir(homedir_fh(self.mc, c))

    def startUp(self):
        """Run before each test"""
        self.c1.null()

    def sleep(self, sec, msg=''):
        """Sleep for given seconds"""
        print "Sleeping for %i seconds:" % sec, msg
        time.sleep(sec)
        print "Woke up"

    def get_and_init_secondconn(self, firstconn, default_secondconn=None):
        pass

#########################################
debug_fail = False

def check(res, stat=NFS3_OK, msg=None, warnlist=[]):
    if res.status == stat:
        if not (debug_fail and msg):
            return
    if type(stat) is str:
        raise "You forgot to put 'msg=' in front of check's string arg"
    desired = nfsstat3[stat]
    received = nfsstat3[res.status]
    if msg:
        msg = "%s should return %s, instead got %s" % (msg, desired, received)
    if res.status in warnlist:
        raise testmod.WarningException(msg)
    else:
        raise testmod.FailureException(msg)

def checklist(res, statlist, msg=None):
    if res.status in statlist:
        return
    statnames = [nfsstat3[stat] for stat in statlist]
    desired = ' or '.join(statnames)
    if not desired:
        desired = 'one of <none>'
    received = nfsstat3[res.status]
    if msg:
        failedop_name = msg
    msg = "%s should return %s, instead got %s" % \
      (failedop_name, desired, received)
    raise testmod.FailureException(msg)
    
def checkdict(expected, got, translate={}, failmsg=''):
    pass

def checkvalid(cond, failmsg):
    if not cond: raise testmod.FailureException(failmsg)

def homedir_fh(mc, c):
    mnt_fh = mc.mount_getfh('/' + '/'.join(mc.opts.path[:-1]))
    res = c.lookup(mnt_fh, c.homedir)
    check(res, msg="Could not access homedir %s" % c.homedir)
    return res.object.data

def get_invalid_utf8strings():
    pass
