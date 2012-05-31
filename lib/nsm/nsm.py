#!/usr/bin/env python
# nsm.py - NSM protocol library for python

import rpc
from xdrlib import Error as XDRError
from nsm_const import *
from nsm_const import res as nsm_stats
from nsm_type import *
from nsm_pack import *
from testmod import WarningException, FailureException

AuthSys = rpc.SecAuthSys(0,'jupiter',103558,100,[])

class NSMClient(rpc.RPCClient):
     def __init__(self, id, host='localhost', port=300, sec_list=[AuthSys],
               opts = None):
          self.ipv6 = getattr(opts, "ipv6", False)
          self.packer = NSMPacker()
          self.unpacker = NSMUnpacker('')
          self.id = id
          self.opts = opts
          uselowport = True
          rpc.RPCClient.__init__(self, host, port, program=SM_PROG,
               version=1, sec_list=sec_list, uselowport=uselowport,
               ipv6=self.ipv6)
          self.server_address = (host,port)

     def nsm_pack(self, procedure, data):
          p = self.packer
          if procedure == SM_NULL:
               pass
          elif procedure == SM_STAT:
               p.pack_sm_name(data)
          elif procedure == SM_MON:
               p.pack_mon(data)
          elif procedure == SM_UNMON:
               p.pack_mon_id(data)
          elif procedure == SM_UNMON_ALL:
               p.pack_my_id(data)
          elif procedure == SM_SIMU_CRASH:
               pass
          elif procedure == SM_NOTIFY:
               p.pack_stat_chge(data)
          else:
               raise XDRError, 'bad switch=%s' % procedure

     def nsm_unpack(self, procedure):
          un_p = self.unpacker

          if procedure == SM_NULL:
               return
          elif procedure == SM_STAT:
               return un_p.unpack_sm_stat_res()
          elif procedure == SM_MON:
               return un_p.unpack_sm_stat_res()
          elif procedure == SM_UNMON:
               return un_p.unpack_sm_stat()
          elif procedure == SM_UNMON_ALL:
               return un_p.unpack_sm_stat()
          elif procedure == SM_SIMU_CRASH:
               return
          elif procedure == SM_NOTIFY:
               return

     def nsm_call(self, procedure, data=''):
          p = self.packer
          un_p = self.unpacker

          # Pack
          p.reset()
          self.nsm_pack(procedure, data)

          # Call
          res = self.call(procedure, p.get_buffer())

          # Unpack
          un_p.reset(res)
          res = self.nsm_unpack(procedure)
          un_p.done()

          return res

     def null(self):
          return self.nsm_call(SM_NULL, None)

     def mon(self, mon_name=''):
          arg_list=mon(mon_id(mon_name, my_id(self.id, 100024, 1, SM_MON)),'')
          return self.nsm_call(SM_MON,arg_list)

     def notify(self, mon_name='', state=1):
          arg_list=stat_chge(mon_name,state)
          return self.nsm_call(SM_NOTIFY,arg_list)

     def simu_crash(self):
          return self.nsm_call(SM_SIMU_CRASH, None)

     def stat(self, mon_name=''):
          return self.nsm_call(SM_STAT,sm_name(mon_name))

     def unmon(self, mon_name=''):
          return self.nsm_call(SM_UNMON,mon_id(mon_name, my_id(self.id, 100024,
               1, SM_UNMON)))

     def unmon_all(self):
          return self.nsm_call(SM_UNMON_ALL,my_id(self.id, 100024, 1,
               SM_UNMON_ALL))
###############################

def nsmcheck(res, stat=STAT_SUCC, msg=None, warnlist=[], state=None, state_only=False):
     badstate = False
     if state and (state_only or res.res_stat != stat):
          if state != "up" and state != "down":
               raise "State must be \"up\" or \"down\""
          if state == "up" and res.state % 2 != 0:
               badstate = True
          elif state == "down" and res.state % 2 == 0:
               badstate = True
     if not badstate and (state_only or res.res_stat == stat):
          return
     if type(stat) is str:
          raise "No 'msg=' in front of check's string arg"

     if not badstate:
          desired = nsm_stats[stat]
          received = nsm_stats[res.res_stat]
     else:
          desired = state
          received = {"up":"down", "down":"up"}[state]
          received += " (" + str(res.state) + ")"
     if msg:
          msg = "%s should return %s, instead got %s" % (msg, desired, received)

     if not state_only:
          if res.res_stat in warnlist:
               raise WarningException(msg)
          else:
               raise FailureException(msg)
     raise FailureException(msg)
