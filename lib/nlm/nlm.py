#!/usr/bin/env python
# nlm.py - NLM protocol library for python

import rpc
import threading
import socket
import os
from xdrlib import Error as XDRError
from nlm_prot_const import *
from nlm_prot_type import *
from nlm_prot_pack import *
from testmod import WarningException, FailureException

try:
    import portmap
except:
    # XXX missing portmap prevents anything from running. Handle missing
    # portmap gracefully?
    pass

AuthSys = rpc.SecAuthSys(0,'jupiter',103558,100,[])

class NLMCBServer(rpc.RPCServer):
    def __init__(self, client,ipv6=False):
        self.prog = 100021
        self.port = 50000
        self.client = client
        rpc.RPCServer.__init__(self, prog=self.prog, vers=4,
                port=self.port)
        self.packer = NLM_PROTPacker()
        self.unpacker = NLM_PROTUnpacker('')
        self.cb_lock = threading.Lock()
        self.cb_lock.acquire()
        self.cb_funct = {}
        self.cb_res = {}
        self.cb_event = {}
        self.cb_granted_funct = None
        self.cb_granted_event = None
        self.cb_lock.release()

    def set_cb(self, cookie, funct, event):
        self.cb_lock.acquire()
        if funct is not None:
            self.cb_funct[cookie] = funct
        if event is not None:
            self.cb_event[cookie] = event
        self.cb_lock.release()

    def clear_cb(self, cookie):
        self.cb_lock.acquire()
        if cookie in self.cb_event:
            del self.cb_event[cookie]
        if cookie in self.cb_res:
            del self.cb_res[cookie]
        if cookie in self.cb_funct:
            del self.cb_funct[cookie]
        self.cb_lock.release()

    def get_cb_res(self, cookie):
        self.cb_lock.acquire()
        res = self.cb_res.get(cookie, None)
        self.cb_lock.release()
        return res

    def run(self):
        # XXX TODO: Replace portmap with something that supports ipv6
        print "Starting NLM Call Back server on port %i" % self.port
        portmap.unset(100021, 0)
        portmap.unset(100021, 1)
        portmap.unset(100021, 3)
        portmap.unset(100021, 4)
        portmap.set(100021, 4, 6, self.port) 
      #  portmap.set(100021, 4, 17, self.port) 
        rpc.RPCServer.run(self)

    def handle_res(self, data, cred):
        self.unpacker.reset(data)
        res = self.unpacker.unpack_nlm4_res()
        try:
            self.unpacker.done()
        except XDRError:
            return rpc.GARBAGE_ARGS, ''
        self.cb_lock.acquire()
        if res.cookie in self.cb_funct:
            self.cb_funct[res.cookie](res)
            del self.cb_funct[res.cookie]
        if res.cookie in self.cb_event:
            self.cb_event[res.cookie].set()
            del self.cb_event[res.cookie]
        self.cb_res[res.cookie] = res
        self.cb_lock.release()

    def handle_0(self, data, cred):
        """ NULL op """
        if data != '':
            return rpc.GARBAGE_ARGS, ''
        else:
            return rpc.SUCCESS, ''

    def handle_11(self, data, cred):
        """ TEST_RES op """
        self.unpacker.reset(data)
        res = self.unpacker.unpack_nlm4_testres()
        try:
            self.unpacker.done()
        except XDRError:
            return rpc.GARBAGE_ARGS, ''
        self.cb_lock.acquire()
        if res.cookie in self.cb_funct:
            self.cb_funct[res.cookie](res)
            del self.cb_funct[res.cookie]
        if res.cookie in self.cb_event:
            self.cb_event[res.cookie].set()
            del self.cb_event[res.cookie]
        self.cb_res[res.cookie] = res
        self.cb_lock.release()

        return rpc.SUCCESS, ''

    def handle_12(self, data, cred):
        """ LOCK_RES op """
        self.handle_res(data,cred)
        return rpc.SUCCESS, ''

    def handle_13(self, data, cred):
        """ CANCEL_RES op """
        self.handle_res(data,cred)
        return rpc.SUCCESS, ''

    def handle_14(self, data, cred):
        """ UNLOCK_RES op """
        self.handle_res(data,cred)
        return rpc.SUCCESS, ''

    def handle_5(self, data, cred):
        """ GRANTED op """
        p = self.packer
        un_p = self.unpacker
        p.reset()
        un_p.reset(data)

        res = un_p.unpack_nlm4_testargs()
        cookie = res.cookie
        try:
            self.unpacker.done()
        except XDRError:
            return rpc.GARBAGE_ARGS, ''
        response = NLM4_GRANTED
        if self.cb_granted_funct is not None:
            response = self.cb_granted_funct(res)
            self.cb_granted_funct = None
        if self.cb_granted_event is not None:
            self.cb_granted_event.set()
            self.cb_granted_event = None
        p.pack_nlm4_res(cookie, response)
        return rpc.SUCCESS, p.get_buffer()

    def handle_10(self, data, cred):
        """ GRANTED_MSG op """
        un_p = self.unpacker
        un_p.reset(data)

        res = un_p.unpack_nlm4_testargs()
        try:
            self.unpacker.done()
        except XDRError:
            return rpc.GARBAGE_ARGS, ''
        if self.cb_granted_funct is None and self.cb_granted_event is None:
            print "WARNING: Got a GRANTED_MSG, but have no callback or event.\
                    The lock will not be held!"
            return rpc.SUCCESS, ''
        if self.cb_granted_funct is not None:
            self.cb_granted_funct(res)
            self.cb_granted_funct = None
        if self.cb_granted_event is not None:
            self.cb_granted_event.set()
            self.cb_granted_event = None
        return rpc.SUCCESS, ''


class NLM4Client(rpc.RPCClient):
     def __init__(self, id, host='localhost', port=300, homedir=['pynfs'],
            sec_list=[AuthSys], opts = None):
          self.ipv6 = getattr(opts, "ipv6", False)
          self._start_cb_server("cb_server_%s" % id)
          self.packer = NLM_PROTPacker()
          self.unpacker = NLM_PROTUnpacker('')
          self.homedir = homedir
          self.id = id
          self.opts = opts
          uselowport = True
          rpc.RPCClient.__init__(self, host, port, program=NLM_PROG,
               version=NLM4_VERS, sec_list=sec_list,
               uselowport=uselowport,ipv6=self.ipv6)
          self.server_address = (host,port)

     def _start_cb_server(self, name=None):
          self.cb_server = NLMCBServer(self,self.ipv6)
          self.thread = threading.Thread(target=self.cb_server.run, name=name)
          self.thread.setDaemon(True)
          self.thread.start()

          self.cb_control = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          while 1:
               try:
                    self.cb_control.connect(('127.0.0.1', self.cb_server.port))
                    break
               except socket.error:
                    print "Waiting for CB Server to start"
                    time.sleep(1)

     def nlm4_pack(self, procedure, data):
          p = self.packer
          if procedure == NLMPROC4_NULL:
               pass
          #Main procs
          elif procedure == NLMPROC4_TEST:
               p.pack_nlm4_testargs(data)
          elif procedure == NLMPROC4_TEST_MSG:
               p.pack_nlm4_testargs(data)
          elif procedure == NLMPROC4_LOCK:
               p.pack_nlm4_lockargs(data)
          elif procedure == NLMPROC4_LOCK_MSG:
               p.pack_nlm4_lockargs(data)
          elif procedure == NLMPROC4_UNLOCK:
               p.pack_nlm4_unlockargs(data)
          elif procedure == NLMPROC4_UNLOCK_MSG:
               p.pack_nlm4_unlockargs(data)
          elif procedure == NLMPROC4_CANCEL:
               p.pack_nlm4_cancargs(data)
          elif procedure == NLMPROC4_CANCEL_MSG:
               p.pack_nlm4_cancargs(data)
          #DOS-style
          elif procedure == NLMPROC4_SHARE:
               p.pack_nlm4_shareargs(data)
          elif procedure == NLMPROC4_UNSHARE:
               p.pack_nlm4_unshareargs(data)
          elif procedure == NLMPROC4_NM_LOCK:
               p.pack_nlm4_lockargs(data)
          elif procedure == NLMPROC4_FREE_ALL:
               p.pack_nlm4_notify(data)
          else:
               raise XDRError, 'bad switch=%s' % procedure

     def nlm4_unpack(self, procedure):
          un_p = self.unpacker

          if procedure == NLMPROC4_NULL:
               return
          elif procedure == NLMPROC4_TEST:
               return un_p.unpack_nlm4_testres()
          elif procedure == NLMPROC4_LOCK:
               return un_p.unpack_nlm4_res()
          elif procedure == NLMPROC4_UNLOCK:
               return un_p.unpack_nlm4_res()
          elif procedure == NLMPROC4_CANCEL:
               return un_p.unpack_nlm4_res()
          elif procedure == NLMPROC4_SHARE:
               return un_p.unpack_nlm4_shareres()
          elif procedure == NLMPROC4_UNSHARE:
               return un_p.unpack_nlm4_shareres()
          elif procedure >= NLMPROC4_TEST_MSG and procedure <= \
                    NLMPROC4_GRANTED_MSG:
               return
          elif procedure == NLMPROC4_NM_LOCK:
               return un_p.unpack_nlm4_res()
          elif procedure == NLMPROC4_FREE_ALL:
               return
          else:
               raise XDRError, 'bad switch=%s' % procedure

     def nlm4_call(self, procedure, data=''):
          p = self.packer
          un_p = self.unpacker

          # Pack
          p.reset()
          self.nlm4_pack(procedure, data)

          # Call
          res = self.call(procedure, p.get_buffer())

          # Unpack
          un_p.reset(res)
          res = self.nlm4_unpack(procedure)
          un_p.done()

          return res

     def nlm4_call_async(self, procedure, data):
          p = self.packer

          p.reset()
          self.nlm4_pack(procedure, data)

          self.send(procedure, p.get_buffer(), None, None)

#Synchronous Calls
     def test(self, lock, netobj_cookie=None, exclusive=False):
          arg_list=nlm4_testargs(netobj_cookie, exclusive, lock)
          return self.nlm4_call(NLMPROC4_TEST,arg_list)

     ### Name changed to avoid conflict with thread.lock
     def lockk(self, lock, netobj_cookie=None, block=False, exclusive=False,
                    reclaim=False, state = 1):
          arg_list=nlm4_lockargs(netobj_cookie, block, exclusive, 
               lock, reclaim, state)
          return self.nlm4_call(NLMPROC4_LOCK,arg_list)
     
     def unlock(self, lock, netobj_cookie=None):
          arg_list=nlm_unlockargs(netobj_cookie, lock)
          return self.nlm4_call(NLMPROC4_UNLOCK,arg_list)
     
     def cancel(self, lock, netobj_cookie=None, block=False, exclusive=False):
          arg_list=nlm_cancargs(netobj_cookie, block, exclusive, lock)
          return self.nlm4_call(NLMPROC4_CANCEL,arg_list)

#Asynchronous Calls     
     def test_msg(self, lock, netobj_cookie=None, exclusive=False,
                    cb_funct=None, cb_event=None):
          arg_list=nlm4_testargs(netobj_cookie, exclusive, lock)
          self.cb_server.set_cb(netobj_cookie, cb_funct, cb_event)
          return self.nlm4_call_async(NLMPROC4_TEST_MSG, arg_list)

     def lock_msg(self, lock, netobj_cookie=None, block=False, exclusive=False,
                    reclaim=False, state = 1, cb_funct=None, cb_event=None):
          arg_list=nlm4_lockargs(netobj_cookie, block, exclusive, 
                    lock, reclaim, state)
          self.cb_server.set_cb(netobj_cookie, cb_funct, cb_event)
          return self.nlm4_call_async(NLMPROC4_LOCK_MSG,arg_list)

     def unlock_msg(self, lock, netobj_cookie=None, cb_funct=None,
                    cb_event=None):
          arg_list=nlm_unlockargs(netobj_cookie, lock)
          self.cb_server.set_cb(netobj_cookie, cb_funct, cb_event)
          return self.nlm4_call_async(NLMPROC4_UNLOCK_MSG,arg_list)

     def cancel_msg(self, lock, netobj_cookie=None, block=False, exclusive=False,
                    cb_funct=None, cb_event=None):
          arg_list=nlm_cancargs(netobj_cookie, block, exclusive, lock)
          self.cb_server.set_cb(netobj_cookie, cb_funct, cb_event)
          return self.nlm4_call_async(NLMPROC4_CANCEL_MSG,arg_list)
# DOS-style
     def share(self, netobj_cookie=None, caller_name='', netobj_fh=None,
                    netobj_oh=None, mode=0, access=0, reclaim=False):
          arg_list=nlm_shareargs(netobj_cookie, nlm_share(caller_name, 
                    netobj_fh, netobj_oh, mode, access), reclaim)
          return self.nlm4_call(NLMPROC4_SHARE,arg_list)

     def unshare(self, netobj_cookie=None, caller_name='', netobj_fh=None,
                    netobj_oh=None, mode=0, access=0):
          arg_list=nlm_shareargs(netobj_cookie, nlm_share(caller_name,
                    netobj_fh, netobj_oh, mode, access))
          return self.nlm4_call(NLMPROC4_UNSHARE,arg_list)

     def nm_lock(self, lock, netobj_cookie=None, block=False, exclusive=False,
                    reclaim=False, state=1):
         arg_list=nlm_lockargs(netobj_cookie, block, exclusive, lock, reclaim,
              state)
         return self.nlm4_call(NLMPROC4_NM_LOCK, arg_list)

     def free_all(self, name):
         return self.nlm4_call(NLMPROC4_FREE_ALL, nlm_notify(name, 0))
###############################

def nlm4check(res, stat=NLM4_GRANTED, msg=None, warnlist=[]):
     if res.stat == stat:
          return
     if type(stat) is str:
          raise "No 'msg=' in front of check's string arg"
     desired = nlm4_stats[stat]
     received = nlm4_stats[res.stat]
     if msg:
          msg = "%s should return %s, instead got %s" % (msg, desired, received)

     if res.stat in warnlist:
          raise WarningException(msg)
     else:
          raise FailureException(msg)

