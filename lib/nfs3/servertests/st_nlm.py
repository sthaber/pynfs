import random
from nfs3.nfs3_const import *
from nlm.nlm_prot_const import *
from environment import homedir_fh
from nfs3.nfs3lib import *
from nlm.nlm import *

def testNLM(t, env):
    """ Just checks the NLM option

    FLAGS: nfsv3 nlm
    DEPEND:
    CODE: NLM0
    """

    print "Checking for --nlm support:"
    if env.ipv6:
        t.fail("  IPv6 is not yet supported for the NLM tests.")
    elif not env.nlm:
        t.fail("  NLM not supported. You need to run with --nlm")
    print "  Supported"

def testNLM4Test(t, env):
     """ Test the NLM TEST op.
         It's a test to test TEST.

     FLAGS: nfsv3 nlm
     DEPEND: NLM0
     CODE: NLM1
     """
     ### Setup Phase ###
     mnt_fh = homedir_fh(env.mc, env.c1)

     ### Execution Phase ###
     res = env.nlm.test(nlm4_lock(t.name, mnt_fh, 'owner', env.pid, 0, 1024)
          ,'cookie', True)

     ### Verification Phase ###
     nlm4check(res.stat, msg="TEST")

def testNLM4Lock(t,env):
     """ Lock and unlock a directory.


     FLAGS: nfsv3 nlm
     DEPEND: NLM0 NLM1
     CODE: NLM2
     """
     ### Setup Phase ###
     mnt_fh = homedir_fh(env.mc, env.c1)
     lock = nlm4_lock(t.name, mnt_fh, 'owner', env.pid, 0, 1024)
     res = env.nlm.test(lock, 'cookie', True)
     nlm4check(res.stat, msg="Initial TEST of unlocked dir")

     ### Execution Phase ###
     res = env.nlm.lockk(lock, 'cookie', False, True, False, 1)
     nlm4check(res.stat,msg="LOCK")

     ### Verification Phase ###
     res = env.nlm.test(lock, 'cookie', True)
     nlm4check(res.stat, msg="TEST of previously locked dir")

     lock2 = nlm4_lock(t.name + 'bad', mnt_fh, 'owner', env.pid, 0, 1024)
     res = env.nlm.test(lock2, 'badcookie', True)
     nlm4check(res.stat, msg="TEST of previously locked dir with bad creds", stat=NLM4_DENIED)

     res = env.nlm.unlock(lock, 'cookie')
     nlm4check(res.stat,msg="UNLOCK")

     res = env.nlm.test(lock, 'cookie', True)
     nlm4check(res.stat, msg="Final TEST of unlocked dir")

def testNLM4LoopTestExclusive(t,env):
     """ Loop, sending NLM4TEST(Exclusive) messages. This is to find a specific
         LK bug (related to SAS escalation bug 85961).

         To run, use multiple clients to run this test against multiple nodes.

         This test should be SAFE to run alongside itself or NLMLOOP2.

     FLAGS: nfsv3 nlm
     DEPEND: NLM0
     CODE: NLMLOOP1
     """

     failed = False

     for i in range(10000):
         # Do an EXCLUSIVE Test
         mnt_fh = homedir_fh(env.mc, env.c1)
         lock = nlm4_lock(t.name, mnt_fh, 'owner', env.pid, 0, 1024)
         res = env.nlm.test(lock, 'cookie', True)
         if res.stat.stat != NLM4_GRANTED:
             print "(%d) res.stat = %s" % (i, nlm4_stats[res.stat.stat])
             print res
             failed = True

     if failed:
         t.fail("FAILED TestExclusive test")

def testNLM4LoopTestExclusive2(t,env):
     """ Loop, sending NLM4TEST(Exclusive) messages. This is to find a specific
         LK bug (related to SAS escalation bug 85961).

         To run, use multiple clients to run this test against multiple nodes.

         This test should be SAFE to run alongside itself or NLMLOOP1 or
         NLMLOOPLOCK2.

     FLAGS: nfsv3 nlm
     DEPEND: NLM0
     CODE: NLMLOOP2
     """

     failed = False
     count = 0
     mnt_fh = homedir_fh(env.mc, env.c1)
     lock = nlm4_lock(t.name, mnt_fh, 'owner', env.pid, 0, 1024)

     for i in range(10000):
         # Do an EXCLUSIVE Test
         res = env.nlm.test(lock, 'cookie', True)
         if res.stat.stat != NLM4_GRANTED:
             count = count + 1
             if res.holder.exclusive:
                 print "(%d) res.stat = %s" % (i, nlm4_stats[res.stat.stat])
                 print res
                 failed = True

     if count > 0:
         print "Got %d shared BLOCKED messages (which may be a bug " \
             "depending on what other tests are running)" % (count)

     if failed:
         t.fail("FAILED TestExclusive test")

def testNLM4LoopLocks(t,env):
     """ Loop, sending NLM4LOCK(Shared) and NLM4LOCK(Exclusive) messages. In
         Posix, a particular locker can own both a shared and an exclusive.

         This test is NOT SAFE to run concurrently with other tests.

     FLAGS: nfsv3 nlm
     DEPEND: NLM0
     CODE: NLMLOOPLOCK1
     """

     mnt_fh = homedir_fh(env.mc, env.c1)
     lock = nlm4_lock(t.name, mnt_fh, 'owner', env.pid, 0, 1024)
     failed = False

     for i in range(10000):
         # Do a SHARED lock
         res = env.nlm.lockk(lock, 'cookie', True, False)
         if res.stat.stat != NLM4_GRANTED:
             print "(%d) res.stat = %s" % (i, nlm4_stats[res.stat.stat])
             print res
             failed = True

         res = env.nlm.lockk(lock, 'cookie', True, True)
         if res.stat.stat != NLM4_GRANTED:
             print "(%d) res.stat = %s" % (i, nlm4_stats[res.stat.stat])
             print res
             failed = True


     for i in range(10000):
         # Unlock SHARED locks
         res = env.nlm.unlock(lock, 'cookie')
         nlm4check(res.stat, msg="UNLOCK")

     if failed:
         t.fail("FAILED TestSharedLock test")

def testNLM4LoopLockAndTest(t,env):
     """ Loop, sending NLM4LOCK(Shared) and NLM4TEST(Exclusive) messages.

         This is to find a specific LK bug (related to SAS escalation bug 85961)

         To run, use multiple clients to run this test against multiple nodes.

     FLAGS: nfsv3 nlm
     DEPEND: NLM0
     CODE: NLMLOOPLOCK2
     """

     mnt_fh = homedir_fh(env.mc, env.c1)
     lock = nlm4_lock(t.name, mnt_fh, t.name, env.pid, 0, 1024)
     testlock = nlm4_lock(t.name, mnt_fh, t.name, env.pid + 1, 0, 1024)
     #lock = nlm4_lock(t.name, mnt_fh, 'owner', env.pid, 0, 1024)
     failed = False
     te_count = 0
     blocked_count = 0

     for i in range(10000):
         # Do a SHARED lock, alternating blocked and not
         if i % 2 == 0:
             blocked = False
         else:
             blocked = True

         res = env.nlm.lockk(lock, 'cookie', blocked, False)
         if res.stat.stat != NLM4_GRANTED:
             if res.stat.stat == NLM4_BLOCKED:
                 blocked_count = blocked_count + 1
             else:
                 print "(%d) LOCK_SHARED: res.stat = %s" % (i, nlm4_stats[res.stat.stat])
                 print res
                 failed = True

         # TEST for shared, should succeed
         res = env.nlm.test(testlock, 'cookie', False)
         if res.stat.stat != NLM4_GRANTED:
             print "(%d) TEST_SHARED: res.stat = %s" % (i, nlm4_stats[res.stat.stat])
             print res
             failed = True

         # TEST for exclusive, should fail
         res = env.nlm.test(testlock, 'cookie', True)
         if res.stat.stat == NLM4_GRANTED:
             te_count = te_count + 1
             print "(%d) TEST_EXCLUSIVE: res.stat = GRANTED"
             failed = True
         elif res.holder.exclusive:
             print "(%d) TEST_EXCLUSIVE: res.stat = %s" % (i, nlm4_stats[res.stat.stat])
             print res
             failed = True

         # Unlock SHARED locks
         res = env.nlm.unlock(lock, 'cookie')
         nlm4check(res.stat, msg="UNLOCK")

     if te_count > 0:
         print "%d TEST_EXCLUSIVEs returned GRANTED and should have failed!" % te_count
     if blocked_count > 0:
         print "%d LOCK_SHARED returned BLOCKED" % blocked_count

     if failed:
         t.fail("FAILED TestSharedLock test")

# XXX FIXME lock_msg() doesn't seem to work if you pass in "True" for blocking.
# It just times out.
def testNLM4LockAsync(t,env):
    """ Asynchronously lock and unlock

    FLAGS: nsv3 nlm
    DEPEND: NLM0
    CODE: NLM3
    """

    mnt_fh = homedir_fh(env.mc, env.c1)
    lock = nlm4_lock(t.name, mnt_fh, 'owner', env.pid, 0, 1024)
    event = threading.Event()

    env.nlm.lock_msg(lock, 'cookie', False, True, False, 1, None, event)
    if event.wait(10.0):
        raise FailureException("NLM Async lock request timed out!")
    else:
        res = env.nlm.cb_server.get_cb_res('cookie')
        if res:
            nlm4check(res.stat, msg="Async LOCK")
        else:
            raise FailureException("NLM Async lock request timed out!")

    env.nlm.unlock_msg(lock, 'cookie', None, event)
    if event.wait(10.0):
        raise FailureException("NLM Async unlock request timed out!")
    else:
        res = env.nlm.cb_server.get_cb_res('cookie')
        if res:
            nlm4check(res.stat, msg="Async UNLOCK")
        else:
            raise FailureException("NLM Async lock request timed out!")

# XXX TODO This mucks up the client because it opens and uses ALL reserved
# ports! After one run, you'll get:
# RPCError: MSG_DENIED: AUTH_ERROR: AUTH_TOOWEAK
# Maybe there is a way to reuse ports or close them properly
def testNLMathon(t, env):
    """ NLM it up!

    FLAGS: nfsv3 nlm
    DEPEND: NLM0
    CODE: NLM4
    """
    print "Running NLM Stress..."
    mnt_fh = homedir_fh(env.mc, env.c1)
    lock = nlm4_lock(t.name, mnt_fh, 'owner', env.pid, 0, 1024)
    threads = []
    for i in range(0,1000):
        threads.append(threading.Thread(target=runRandomProc,args=(lock,i,env)))
        threads[i].start()
    for i in range(0,1000):
        threads[i].join()

def runRandomProc(lock, n, env):
    random.seed()
    proc = random.randint(0, 12)
    if proc >= 5:
        proc += 1 #skip GRANTED
    if proc >= 10:
        proc += 6 #skip callbacks
    if proc == 0:
        env.nlm.nlm4_call(NLMPROC4_NULL, '')
    elif proc <= 9:
        functs = {1:env.nlm.test,2:env.nlm.lockk,3:env.nlm.unlock,
         4:env.nlm.cancel, 6:env.nlm.test_msg,7:env.nlm.lock_msg,
         8:env.nlm.unlock_msg,9:env.nlm.cancel_msg}
        if proc < 5:
            res = functs[proc](lock, netobj_cookie="cookie"+str(n))
            #print "%i: %s" % (n, res.stat)
        elif proc < 10:
            event = threading.Event()
            functs[proc](lock, netobj_cookie="cookie%i"%n,cb_event=event)
            event.wait(10)
            res = env.nlm.cb_server.get_cb_res("cookie%i"%n)
            #if(res):
            #    print "%i: %s" % (n,res.stat)

