from nfs4.nfs4_const import *
from environment import check

def testDoConfigExports(t, env):
    """ISILON specific, will configure a new export for use w/ these tests

    FLAGS: exports
    DEPEND:
    CODE: EXP1
    """
    # XXX shaber: write this
    # For now: configure /ifs/data as an export with
    #      --security-flavors=sys:krb5:krb5i:krb5p
    # And /ifs with
    #      --security-flavors=sys
    pass

def testSecinfoPseudoToExport(t, env):
    """SECINFO pseudo->export should return NFS4_OK

    FLAGS: exports
    DEPEND: EXP1
    CODE: EXP2
    """ 
    c = env.c1
    ops = [c.putrootfh_op()]
    ops += [c.secinfo_op("ifs")]
    res = c.compound(ops)
    check(res)
    # Make sure at least one security mechanisms is returned.
    if len(res.resarray[-1].switch.switch) == 0:
        t.fail("SECINFO returned empty mechanism list")
    
def testSecinfoExportToExport(t, env):
    """SECINFO across exports should return NFS4_OK

    FLAGS: exports
    DEPEND: EXP1
    CODE: EXP3
    """ 
    c = env.c1
    
    # Check /ifs export
    ops = [c.putrootfh_op()]
    ops += [c.secinfo_op("ifs")]
    res = c.compound(ops)
    check(res)
    if len(res.resarray[-1].switch.switch) != 1:
        t.fail("SECINFO on /ifs returned incorrect number of flavors")

    # Check /ifs/data export
    ops = [c.putrootfh_op()]
    ops += [c.lookup_op("ifs")]
    ops += [c.secinfo_op("data")]
    res = c.compound(ops)
    check(res)
    if len(res.resarray[-1].switch.switch) != 4:
        t.fail("SECINFO on /ifs/data returned incorrect number of flavors")

def testSecinfoHiddenPseudo(t, env):
    """SECINFO on a hidden directory in pseudo should return ENOENT

    FLAGS: exports
    DEPEND: EXP1
    CODE: EXP4
    """
    c = env.c1
    ops = [c.putrootfh_op()]
    ops += [c.secinfo_op("root")]
    res = c.compound(ops)
    check(res, NFS4ERR_NOENT)

def testLookupHiddenPseudo(t, env):
    """LOOKUP on a hidden directory in pseudo should return ENOENT

    FLAGS: exports
    DEPEND: EXP1
    CODE: EXP5
    """
    c = env.c1
    ops = [c.putrootfh_op()]
    ops += [c.lookup_op("root")]
    res = c.compound(ops)
    check(res, NFS4ERR_NOENT)

def testLookupRootDotDot(t, env):
    """LOOKUP on .. from root should not roll off the top of the FS

    FLAGS: exports
    DEPEND: EXP1
    CODE: EXP6
    """
    c = env.c1
    ops = [c.putrootfh_op()]
    ops += [c.lookup_op("..")]
    ops += [c.getfh_op()]
    res = c.compound(ops)
    check(res, NFS4ERR_BADNAME)

def testSecinfoRootDotDot(t, env):
    """SECINFO on .. from root should not roll off the top of the FS

    FLAGS: exports
    DEPEND: EXP1
    CODE: EXP7
    """
    c = env.c1
    ops = [c.putrootfh_op()]
    ops += [c.secinfo_op("..")]
    res = c.compound(ops)
    check(res, NFS4ERR_BADNAME)
