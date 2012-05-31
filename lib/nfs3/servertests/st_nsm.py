from nsm.nsm_const import *
from nsm.nsm import *

def testNSM(t, env):
    """ Just checks the NSM option.

    FLAGS: nfsv3 nsm
    DEPEND:
    CODE: NSM0
    """

    print "Checking for --nsm support:"
    if not env.nsm:
        t.fail("  NSM not supported. You need to run with --nsm")
    print "  Supported"

def testNSMNull(t, env):
    """ NSM null call.

    FLAGS: nfsv3 nsm
    DEPEND: NSM0
    CODE: NSM1
    """
    env.nsm.null()
    env.nsm_local.null()

def testNSMSimuCrash(t, env):
    """ Calls the simulate crash routine.

    FLAGS: nfsv3 nsm
    DEPEND: NSM0
    CODE: NSM2
    """
    env.nsm.simu_crash()

def testNSMMonClient(t, env):
    """ Monitor and unmonitor the test machine.

    FLAGS: nfsv3 nsm
    DEPEND: NSM0
    CODE: NSM3
    """
    # In the RPC library, ipaddress is the local IP
    # Monitor the test client
    res = env.nsm.mon(env.nsm.ipaddress)
    nsmcheck(res, msg="Monitor self", state="up")

    # Monitor a nonsense client
    res = env.nsm.mon("1.2.3.4")
    nsmcheck(res, msg="Monitor bogus", state="up")

    # Unmonitor them
    res = env.nsm.unmon(env.nsm.ipaddress)
    nsmcheck(res, msg="Unmonitor self", state="down", state_only=True)
    res = env.nsm.unmon("1.2.3.4")
    nsmcheck(res, msg="Unmonitor bogus", state="down", state_only=True)

def testNSMMonInvalid(t, env):
    """ Monitor invalid hosts

    FLAGS: nfsv3 nsm
    DEPEND: NSM0
    CODE: NSM4
    """
    res = env.nsm.mon("")
    nsmcheck(res, STAT_FAIL, "Monitor a blank string")
    # I guess this is actually valid:
    # res = env.nsm.mon("localhost")
    # nsmcheck(res, STAT_FAIL, "Monitor localhost")

def testNSMUnmonAll(t, env):
    """ We can't really see what hosts the server is monitoring, so this test
    just checks to make sure it doesn't fail at the RPC layer.

    FLAGS: nfsv3 nsm
    DEPEND: NSM0
    CODE: NSM5
    """
    res = env.nsm.mon(env.nsm.ipaddress)
    nsmcheck(res, state="up")
    res = env.nsm.unmon_all()
    nsmcheck(res, state="down", state_only=True)
    
def testNotify(t, env):
    """ This test monitors a client and then notifies that the client crashed.

    FLAGS: nfsv3 nsm
    DEPEND: NSM0
    CODE: NSM6
    """
    res = env.nsm.mon(env.nsm.ipaddress)
    nsmcheck(res, state="up")
    state = res.state
    env.nsm.notify(env.nsm.ipaddress, state+1)
    res = env.nsm.stat(env.nsm.ipaddress)
    nsmcheck(res, state="down")
