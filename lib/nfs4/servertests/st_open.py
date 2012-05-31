from nfs4.nfs4_const import *
from environment import check, checklist, checkdict, get_invalid_utf8strings
from nfs4.nfs4lib import get_bitnumattr_dict

# Any test that uses create_confirm should depend on this test
def testOpen(t, env):
    """OPEN normal file with CREATE and GUARDED flags

    FLAGS: open openconfirm all
    DEPEND: INIT
    CODE: MKFILE
    """
    c = env.c1
    c.init_connection()
    c.create_confirm(t.code)

def testCreateUncheckedFile(t, env):
    """OPEN normal file with create and unchecked flags

    FLAGS: open all
    DEPEND: INIT
    CODE: OPEN2
    """
    c = env.c1
    c.init_connection()

    # Create the file
    orig_attrs = { FATTR4_MODE: 0644, FATTR4_SIZE: 32 }
    res = c.create_file(t.code, attrs=orig_attrs,  deny=OPEN4_SHARE_DENY_NONE)
    check(res, msg="Trying to create file %s" % t.code)
    fh, stateid = c.confirm(t.code, res)
    rcvd_attrs = c.do_getattrdict(fh, orig_attrs.keys())
    checkdict(orig_attrs, rcvd_attrs, get_bitnumattr_dict(),
              "Checking attrs on creation")
    # Create the file again...it should ignore attrs
    attrs = { FATTR4_MODE: 0600, FATTR4_SIZE: 16 }
    res = c.create_file(t.code, attrs=attrs,  deny=OPEN4_SHARE_DENY_NONE)
    check(res, msg="Trying to recreate file %s" % t.code)
    fh, stateid = c.confirm(t.code, res)
    rcvd_attrs = c.do_getattrdict(fh, orig_attrs.keys())
    checkdict(orig_attrs, rcvd_attrs, get_bitnumattr_dict(),
              "Attrs on recreate should be ignored")
    # Create the file again, should truncate size to 0 and ignore other attrs
    attrs = { FATTR4_MODE: 0600, FATTR4_SIZE: 0 }
    res = c.create_file(t.code, attrs=attrs,  deny=OPEN4_SHARE_DENY_NONE)
    check(res, msg="Trying to truncate file %s" % t.code)
    fh, stateid = c.confirm(t.code, res)
    rcvd_attrs = c.do_getattrdict(fh, orig_attrs.keys())
    expect = { FATTR4_MODE: 0644, FATTR4_SIZE: 0 }
    checkdict(expect, rcvd_attrs, get_bitnumattr_dict(),
              "Attrs on recreate should be ignored, except for size")
        
def testCreatGuardedFile(t, env):
    """OPEN normal file with create and guarded flags

    FLAGS: open all
    DEPEND: INIT
    CODE: OPEN3
    """
    c = env.c1
    c.init_connection()
    res = c.create_file(t.code, mode=GUARDED4)
    check(res, msg="Trying to do guarded create of file %s" % t.code)
    c.confirm(t.code, res)
    # Create the file again, should return an error
    res = c.create_file(t.code, mode=GUARDED4)
    check(res, NFS4ERR_EXIST,
          "Trying to do guarded recreate of file %s" % t.code)

# FRED - CITI does not return an attr - warn about this?
def testCreatExclusiveFile(t, env):
    """OPEN normal file with create and exclusive flags

    FLAGS: open all
    DEPEND: INIT
    CODE: OPEN4
    """
    c = env.c1
    c.init_connection()
    # Create the file
    res = c.create_file(t.code, mode=EXCLUSIVE4, verifier='12345678', deny=OPEN4_SHARE_DENY_NONE)
    checklist(res, [NFS4_OK, NFS4ERR_NOTSUPP],
              "Trying to do exclusive create of file %s" % t.code)
    if res.status == NFS4ERR_NOTSUPP:
        c.fail_support("Exclusive OPEN not supported")
    fh, stateid = c.confirm(t.code, res)
    # Create the file again, should return an error
    res = c.create_file(t.code, mode=EXCLUSIVE4, verifier='87654321', deny=OPEN4_SHARE_DENY_NONE)
    check(res, NFS4ERR_EXIST,
          "Trying to do exclusive recreate of file %s w/ new verifier" % t.code)
    # Create with same verifier should return same object
    res = c.create_file(t.code, mode=EXCLUSIVE4, verifier='12345678', deny=OPEN4_SHARE_DENY_NONE)
    check(res, msg="Trying to do exclusive recreate of file %s with old verifier" % t.code)
    newfh, stateid = c.confirm(t.code, res)
    if fh != newfh:
        c.fail("Filehandle changed on duplicate exclusive create")

def testExclusiveFileSupport(t, env):
    """OPEN normal file with create and exclusive flags

    FLAGS: open all
    DEPEND: INIT
    CODE: OPEN4a
    """
    c = env.c1
    c.init_connection()
    # Create the file
    res = c.create_file(t.code, mode=EXCLUSIVE4, verifier='12345678', deny=OPEN4_SHARE_DENY_NONE)
    checklist(res, [NFS4_OK, NFS4ERR_NOTSUPP],
              "Trying to do exclusive create of file %s" % t.code)
    if res.status == NFS4ERR_NOTSUPP:
        c.fail_support("Exclusive OPEN not supported")
    fh, stateid = c.confirm(t.code, res)

def testOpenFile(t, env):
    """OPEN normal file with nocreate flag

    FLAGS: open openconfirm file all
    DEPEND: INIT LOOKFILE
    CODE: OPEN5
    """
    c = env.c1
    c.init_connection()
    c.open_confirm(t.code, env.opts.usefile)
                       
def testOpenVaporFile(t, env):
    """OPEN non-existant file with nocreate flag should return NFS4ERR_NOENT

    FLAGS: open all
    DEPEND: INIT MKDIR
    CODE: OPEN6
    """
    c = env.c1
    c.init_connection()
    res = c.create_obj(c.homedir + [t.code])
    check(res)
    res = c.open_file(t.code, c.homedir + [t.code, 'vapor'])
    check(res, NFS4ERR_NOENT,
          "Trying to open nonexistant file %s/vapor" % t.code)

    
def testDir(t, env):
    """OPEN with a directory should return NFS4ERR_ISDIR

    FLAGS: open dir all
    DEPEND: INIT LOOKDIR
    CODE: OPEN7d
    """
    c = env.c1
    c.init_connection()
    res = c.open_file(t.code, env.opts.usedir)
    check(res, NFS4ERR_ISDIR, "Trying to OPEN dir")
    
def testLink(t, env):
    """OPEN with a symlink should return NFS4ERR_SYMLINK

    FLAGS: open symlink all
    DEPEND: INIT LOOKLINK
    CODE: OPEN7a
    """
    c = env.c1
    c.init_connection()
    res = c.open_file(t.code, env.opts.uselink)
    check(res, NFS4ERR_SYMLINK, "Trying to OPEN symbolic link")
    
def testBlock(t, env):
    """OPEN with a block device should return NFS4ERR_INVAL

    FLAGS: open block all
    DEPEND: INIT LOOKBLK
    CODE: OPEN7b
    """
    c = env.c1
    c.init_connection()
    res = c.open_file(t.code, env.opts.useblock)
    check(res, NFS4ERR_INVAL, "Trying to OPEN block device")

def testChar(t, env):
    """OPEN with a character device should return NFS4ERR_INVAL

    FLAGS: open char all
    DEPEND: INIT LOOKCHAR
    CODE: OPEN7c
    """
    c = env.c1
    c.init_connection()
    res = c.open_file(t.code, env.opts.usechar)
    check(res, NFS4ERR_INVAL, "Trying to OPEN character device")

def testSocket(t, env):
    """OPEN with a socket should return NFS4ERR_INVAL

    FLAGS: open socket all
    DEPEND: INIT LOOKSOCK
    CODE: OPEN7s
    """
    c = env.c1
    c.init_connection()
    res = c.open_file(t.code, env.opts.usesocket)
    check(res, NFS4ERR_INVAL, "Trying to OPEN socket")

def testFifo(t, env):
    """OPEN with a fifo should return NFS4ERR_INVAL

    FLAGS: open fifo all
    DEPEND: INIT LOOKFIFO
    CODE: OPEN7f
    """
    c = env.c1
    c.init_connection()
    res = c.open_file(t.code, env.opts.usefifo)
    check(res, NFS4ERR_INVAL, "Trying to OPEN fifo")

def testNoFh(t, env):
    """OPEN should fail with NFS4ERR_NOFILEHANDLE if no (cfh)

    FLAGS: open emptyfh all
    DEPEND: INIT
    CODE: OPEN8
    """
    c = env.c1
    c.init_connection()
    ops = [c.open(t.code, t.code)]
    res = c.compound(ops)
    c.advance_seqid(t.code, res)
    check(res, NFS4ERR_NOFILEHANDLE, "OPEN with no <cfh>")
    
def testZeroLenName(t, env):
    """OPEN with zero length name should return NFS4ERR_INVAL

    FLAGS: open all
    DEPEND: INIT
    CODE: OPEN10
    """
    c = env.c1
    c.init_connection()
    res = c.create_file(t.code, c.homedir + [''])
    check(res, NFS4ERR_INVAL, "OPEN with zero-length name")

def testLongName(t, env):
    """OPEN should fail with NFS4ERR_NAMETOOLONG with long filenames

    FLAGS: open longname all
    DEPEND: INIT
    CODE: OPEN11
    """
    c = env.c1
    c.init_connection()
    res = c.create_file(t.code,  c.homedir + [env.longname])
    check(res, NFS4ERR_NAMETOOLONG, "OPEN with very long name")
    
def testNotDir(t, env):
    """OPEN with cfh not a directory should return NFS4ERR_NOTDIR

    FLAGS: open file all
    DEPEND: INIT LOOKFILE
    CODE: OPEN12
    """
    c = env.c1
    c.init_connection()
    res = c.open_file(t.code, env.opts.usefile + ['foo'])
    check(res, NFS4ERR_NOTDIR, "Trying to OPEN with cfh a file")
       
def testInvalidUtf8(t, env):
    """OPEN with bad UTF-8 name strings should return NFS4ERR_INVAL

    FLAGS: open utf8 all
    DEPEND: MKDIR
    CODE: OPEN13
    """
    c = env.c1
    c.init_connection()
    res = c.create_obj(c.homedir + [t.code])
    check(res)
    for name in get_invalid_utf8strings():
        res = c.create_file(t.code, c.homedir + [t.code, name])
        check(res, NFS4ERR_INVAL, "Trying to open file with invalid utf8 "
                                  "name %s/%s" % (t.code, repr(name)[1:-1]))

def testInvalidAttrmask(t, env):
    """OPEN should fail with NFS4ERR_INVAL on invalid attrmask

    Comments: We are using a read-only attribute on OPEN, which
    should return NFS4ERR_INVAL.

    FLAGS: open all
    DEPEND: INIT
    CODE: OPEN14
    """
    c = env.c1
    c.init_connection()
    res = c.create_file(t.code, attrs={FATTR4_LINK_SUPPORT: TRUE})
    check(res, NFS4ERR_INVAL, "Trying to OPEN with read-only attribute")

def testUnsupportedAttributes(t, env):
    """OPEN should fail with NFS4ERR_ATTRNOTSUPP on unsupported attrs

    FLAGS: open all
    DEPEND: INIT LOOKFILE
    CODE: OPEN15
    """
    c = env.c1
    c.init_connection()
    supported = c.supportedAttrs(env.opts.usefile)
    count = 0
    for attr in env.attr_info:
        if attr.writable and not supported & attr.mask:
            count += 1
            res = c.create_file(t.code, attrs={attr.bitnum : attr.sample})
            check(res, NFS4ERR_ATTRNOTSUPP,
                  "Trying to OPEN with unsupported attribute")
    if count==0:
        t.pass_warn("There were no unsupported writable attributes, "
                    "nothing tested")

def testClaimPrev(t, env):
    """OPEN with CLAIM_PREVIOUS should return NFS4ERR_RECLAIM_BAD

    Note this assumes test is run after grace period has expired.
    (To actually ensure return of _NO_GRACE, see REBT3 test)
    
    FLAGS: open all
    DEPEND: MKFILE
    CODE: OPEN16
    """
    c = env.c1
    c.init_connection()
    fh, stateid = c.create_confirm(t.code)
    res = c.open_file(t.code, fh, claim_type=CLAIM_PREVIOUS, deleg_type=OPEN_DELEGATE_NONE)
    check(res, NFS4ERR_RECLAIM_BAD, "Trying to OPEN with CLAIM_PREVIOUS",
          [NFS4ERR_NO_GRACE])

def testModeChange(t, env):
    """OPEN conflicting with mode bits

    FLAGS: open all
    DEPEND: MODE MKFILE
    CODE: OPEN17
    """
    c = env.c1
    c.init_connection()
    fh, stateid = c.create_confirm(t.code)
    res = c.close_file(t.code, fh, stateid)
    check(res)
    ops = c.use_obj(fh) + [c.setattr({FATTR4_MODE:0})]
    res = c.compound(ops)
    check(res, msg="Setting mode of file %s to 000" % t.code)
    res = c.open_file(t.code, access=OPEN4_SHARE_ACCESS_BOTH,
                      deny=OPEN4_SHARE_DENY_NONE)
    check(res, NFS4ERR_ACCESS, "Opening file %s with mode=000" % t.code)

def testShareConflict1(t, env):
    """OPEN conflicting with previous share
    FLAGS: multiconn open all
    DEPEND: MKFILE MULTICONN
    CODE: OPEN18
    """
    c = env.c1
    c.init_connection()
    c2 = env.get_and_init_secondconn(c)
    file = c.homedir + [t.code]
    c.create_confirm(t.code, file, access=OPEN4_SHARE_ACCESS_BOTH)
    res = c2.open_file('newowner', file, deny=OPEN4_SHARE_DENY_WRITE)
    check(res, NFS4ERR_SHARE_DENIED,
          "Trying to open a file with deny=WRITE "
          "that was already opened with access=WRITE")

# FRED - is this right response? or should it be allowed?
def testShareConflict2(t, env):
    """OPEN with deny=write when don't have write permissions

    FLAGS: open all
    DEPEND: MKFILE MODE
    CODE: OPEN19
    """
    c1 = env.c1
    c1.init_connection()
    c1.create_confirm(t.code, attrs={FATTR4_MODE:0644},
                      access=OPEN4_SHARE_ACCESS_READ,
                      deny=OPEN4_SHARE_DENY_NONE)
    c2 = env.c2
    c2.init_connection()
    res = c2.open_file(t.code, access=OPEN4_SHARE_ACCESS_READ,
                       deny=OPEN4_SHARE_DENY_WRITE)
    check(res, NFS4ERR_ACCESS,
          "Trying to deny write permissions to others when "
          "don't have write permissions")

def testFailedOpen(t, env):
    """MULTIPLE: failed open should not mess up other clients' filehandles

    FLAGS: open all
    DEPEND: MKFILE MODE MKDIR
    CODE: OPEN20
    """
    c1 = env.c1
    c1.init_connection()
    # Client 1: create a file and deny others access
    fh, stateid = c1.create_confirm(t.code)
    ops = c1.use_obj(fh) + [c1.setattr({FATTR4_MODE: 0700})]
    check(c1.compound(ops))
    # Client 2: try to open the file
    c2 = env.c2
    c2.init_connection()
    res = c2.open_file(t.code)
    check(res, NFS4ERR_ACCESS, "Opening file with mode 0700 as 'other'")
    # Client 1: try to use fh, stateid
    res1 = c1.lock_file(t.code, fh, stateid)
    check(res1, msg="Locking file after another client had a failed open")
    res = c1.write_file(fh, 'data', 0, stateid)
    check(res, msg="Writing with write lock")
    res = c1.unlock_file(1, fh, res1.lockid)
    check(res, msg="Unlocking file after write")
    res = c1.close_file(t.code, fh, stateid)
    check(res, msg="Closing file after lock/write/unlock sequence")

def testDenyRead1(t, env):
    """OPEN with access=read on a read-denied file

    FLAGS: open all
    DEPEND: MKFILE
    CODE: OPEN21
    """
    c = env.c1
    c.init_connection()
    fh, stateid = c.create_confirm(t.code, access=OPEN4_SHARE_ACCESS_BOTH,
                                   deny=OPEN4_SHARE_DENY_READ)
    # Same owner, should fail despite already having read access
    # This is stated in both 14.2.16 and 8.9
    res = c.open_file(t.code, access=OPEN4_SHARE_ACCESS_READ,
                      deny=OPEN4_SHARE_DENY_NONE)
    check(res, NFS4ERR_SHARE_DENIED,
          "OPEN with access==read on a read-denied file")

def testDenyRead2(t, env):
    """OPEN with access=read on a read-denied file

    NFS4ERR_SHARE_DENIED return is specified in 14.2.16
    NFS4ERR_DENIED return is specified in  8.9

    FLAGS: multiconn open all
    DEPEND: MKFILE MULTICONN
    CODE: OPEN22
    """
    c = env.c1
    c.init_connection()
    c2 = env.get_and_init_secondconn(c)
    file = c.homedir + [t.code]
    fh, stateid = c.create_confirm('owner1', file,
                                   access=OPEN4_SHARE_ACCESS_BOTH,
                                   deny=OPEN4_SHARE_DENY_READ)
    res = c2.open_file('owner2', file, access=OPEN4_SHARE_ACCESS_READ,
                      deny=OPEN4_SHARE_DENY_NONE)
    check(res, NFS4ERR_SHARE_DENIED,
          "OPEN with access==read on a read-denied file")

def testDenyRead3(t, env):
    """READ (with stateid all 0s) on a read-denied file

    NFS4ERR_LOCKED return is specified in 8.1.4:
        seems to apply to conflicts due to an OPEN(deny=x)
    NFS4ERR_ACCESS return is specified in 14.2.16:
        seems to apply to principle not having access to file
    NFS4ERR_OPENMODE return is specified in 8.1.4:
        (does not apply to special stateids) Why is this again?
        seems to apply to doing WRITE on OPEN(allow=read)

    FLAGS: multiconn open read all
    DEPEND: MKFILE MULTICONN
    CODE: OPEN23
    """
    c = env.c1
    c.init_connection()
    c2 = env.get_and_init_secondconn(c)
    fh, stateid = c.create_confirm(t.code,
                                   access=OPEN4_SHARE_ACCESS_BOTH,
                                   deny=OPEN4_SHARE_DENY_READ)
    res = c.write_file(fh, 'data', 0, stateid)
    check(res)
    # Try to read file w/o opening
    res = c2.read_file(fh)
    check(res, NFS4ERR_LOCKED, "Trying to READ a read-denied file, 0 stateid")

def testDenyRead3a(t, env):
    """READ on a access_write file

    NFS4_OK is allowed per sect 8.1.4 of RFC, and many clients expect it
    
    FLAGS: open read all
    DEPEND: MKFILE
    CODE: OPEN23b
    """
    c = env.c1
    c.init_connection()
    fh, stateid = c.create_confirm(t.code,
                                   access=OPEN4_SHARE_ACCESS_WRITE,
                                   deny=OPEN4_SHARE_DENY_NONE)
    res = c.write_file(fh, 'data', 0, stateid)
    check(res)
    # Try to read file 
    res2 = c.read_file(fh, stateid=stateid)
    check(res2, NFS4_OK, "Read an access_write file", [NFS4ERR_OPENMODE])

def testDenyRead4(t, env):
    """WRITE on a read-denied file

    FLAGS: multiconn open write all
    DEPEND: MULTICONN MKFILE
    CODE: OPEN24
    """
    c = env.c1
    c.init_connection()
    c2 = env.get_and_init_secondconn(c)
    file = c.homedir + [t.code]
    fh1, stateid1 = c.create_confirm('owner1', file,
                                     access=OPEN4_SHARE_ACCESS_BOTH,
                                     deny=OPEN4_SHARE_DENY_READ)
    res = c.write_file(fh1, 'data', 0, stateid1)
    check(res)
    # Try to write file
    fh2, stateid2 = c2.open_confirm('owner2', file,
                                     access=OPEN4_SHARE_ACCESS_WRITE,
                                     deny=OPEN4_SHARE_DENY_NONE)
    res2 = c2.write_file(fh2, 'data', 0, stateid2)
    check(res2, msg="WRITE a read-denied file")

def testDenyWrite1(t, env):
    """OPEN with access=write on a write-denied file

    FLAGS: multiconn open all
    DEPEND: MKFILE MULTICONN
    CODE: OPEN25
    """
    c = env.c1
    c.init_connection()
    c2 = env.get_and_init_secondconn(c)
    fh, stateid = c.create_confirm(t.code, access=OPEN4_SHARE_ACCESS_BOTH,
                                   deny=OPEN4_SHARE_DENY_WRITE)
    # Same owner, should fail despite already having read access
    # This is stated in both 14.2.16 and 8.9
    res = c2.open_file(t.code, access=OPEN4_SHARE_ACCESS_WRITE,
                      deny=OPEN4_SHARE_DENY_NONE)
    check(res, NFS4ERR_SHARE_DENIED,
          "OPEN with access==write on a write-denied file")
    
def testDenyWrite2(t, env):
    """OPEN with access=write on a write-denied file

    NFS4ERR_SHARE_DENIED return is specified in 14.2.16
    NFS4ERR_DENIED return is specified in  8.9

    FLAGS: multiconn open all
    DEPEND: MULTICONN MKFILE
    CODE: OPEN26
    """
    c = env.c1
    c.init_connection()
    c2 = env.get_and_init_secondconn(c)
    file = c.homedir + [t.code]
    fh, stateid = c.create_confirm('owner1', file,
                                   access=OPEN4_SHARE_ACCESS_BOTH,
                                   deny=OPEN4_SHARE_DENY_WRITE)
    res = c2.open_file('owner2', file, access=OPEN4_SHARE_ACCESS_WRITE,
                      deny=OPEN4_SHARE_DENY_NONE)
    check(res, NFS4ERR_SHARE_DENIED,
          "OPEN with access==write on a write-denied file")

def testDenyWrite3(t, env):
    """WRITE a write-denied file

    see OPEN23 comments

    FLAGS: multiconn open write all
    DEPEND: MKFILE MULTICONN
    CODE: OPEN27
    """
    c = env.c1
    c.init_connection()
    c2 = env.get_and_init_secondconn(c)
    fh, stateid = c.create_confirm(t.code,
                                   access=OPEN4_SHARE_ACCESS_BOTH,
                                   deny=OPEN4_SHARE_DENY_WRITE)
    res = c.write_file(fh, 'data', 0, stateid)
    check(res)
    # Try to write using stateid=0
    res = c2.write_file(fh, 'moredata')
    check(res, NFS4ERR_LOCKED, "Trying to WRITE a write-denied file")

def testDenyWrite4(t, env):
    """READ on a write-denied file

    FLAGS: multiconn open read all
    DEPEND: MKFILE MULTICONN
    CODE: OPEN28
    """
    c = env.c1
    c.init_connection()
    c2 = env.get_and_init_secondconn(c)
    file = c.homedir + [t.code]
    fh1, stateid1 = c.create_confirm('owner1', file,
                                     access=OPEN4_SHARE_ACCESS_BOTH,
                                     deny=OPEN4_SHARE_DENY_WRITE)
    res = c.write_file(fh1, 'data', 0, stateid1)
    check(res)
    # Try to read file
    fh2, stateid2 = c2.open_confirm('owner2', file,
                                     access=OPEN4_SHARE_ACCESS_READ,
                                     deny=OPEN4_SHARE_DENY_NONE)
    res2 = c2.read_file(fh2, stateid=stateid2)
    check(res2, msg="READ a write-denied file")
    if res2.eof != TRUE or res2.data != 'data':
        t.fail("READ returned %s, expected 'data'" % repr(res2.data))

def testNoMode(t, env):
    """CREATE a file with no mode. This is possible according to the spec.

    FLAGS: open all
    DEPEND:
    CODE: OPEN29
    """
    c = env.c1
    c.init_connection()
    res = c.create_file(t.code, attrs={})
    check(res)

def testOpenUpgrade1(t, env):
    """ OPEN UPGRADE 1
    Test open upgrades and make sure a CLOSE will close all outstanding opens.

    This test succeeds on Ubuntu0906, but fails on OpenSolaris? See
    testSolarisOpens.

    FLAGS: open all
    DEPEND: MKFILE
    CODE: OPENUP1
    """
    c = env.c1
    c.init_connection()
    file_obj = c.homedir + [t.code]

    # Open twice
    fh1, stateid1 = c.create_confirm(t.code, file_obj, access=OPEN4_SHARE_ACCESS_READ,
        deny=OPEN4_SHARE_DENY_READ)
    fh2, stateid2 = c.open_confirm(t.code, file_obj, access=OPEN4_SHARE_ACCESS_WRITE,
        deny=OPEN4_SHARE_DENY_WRITE)

    # Try invalid opens
    res2 = c.open_file(t.code, file_obj, access=OPEN4_SHARE_ACCESS_READ,
        deny=OPEN4_SHARE_DENY_NONE)
    check(res2, NFS4ERR_SHARE_DENIED,
        msg="READ/DENY_NONE should NOT be compatible with READ/DENY_READ")
    res3 = c.open_file(t.code, file_obj, access=OPEN4_SHARE_ACCESS_WRITE,
        deny=OPEN4_SHARE_DENY_NONE)
    check(res3, NFS4ERR_SHARE_DENIED,
        msg="WRITE/DENY_NONE should NOT be compatible with WRITE/DENY_WRITE")

    # Close once
    res4 = c.close_file(t.code, fh2, stateid2)
    check(res4, msg="Close should work fine")

    # Make sure no opens survive.
    res5 = c.open_file(t.code, file_obj, access=OPEN4_SHARE_ACCESS_READ,
        deny=OPEN4_SHARE_DENY_READ)
    check(res5, msg="No opens should survive.")

def accessToStr(acc):
    if acc == 1:
        return "read"
    elif acc == 2:
        return "write"
    elif acc == 3:
        return "both"
    else:
        return "error in access type"

def denyToStr(deny):
    if deny == 0:
        return "none"
    elif deny == 1:
        return "read"
    elif deny == 2:
        return "write"
    elif deny  == 3:
        return "both"
    else:
        return "error in deny type"

def openErrorToStr(acc1, deny1, acc2, deny2):
    return ("Wrong share semantics for %d%d%d%d. Open1: acc=%s, deny=%s. Open2: acc=%s, deny=%s" %
        (acc1, deny1, acc2, deny2, accessToStr(acc1), denyToStr(deny1),
         accessToStr(acc2), denyToStr(deny2)))

def testOpenUpgrade2(t, env):
    """ OPEN UPGRADE 2: Try all combinations of 2 opens in a row

    FLAGS: multiconn open all
    DEPEND: MKFILE OPENUP1 MULTICONN
    CODE: OPENUP2
    """
    c = env.c1
    c.init_connection()
    c2 = env.get_and_init_secondconn(c)
    file_obj = c.homedir + [t.code]

    # Create file initially, then close it.
    fh, stateid = c.create_confirm(t.code, file_obj, access=OPEN4_SHARE_ACCESS_BOTH)
    res = c.close_file(t.code, fh, stateid)
    check(res)

    # acc = 1,2,3
    acc = [OPEN4_SHARE_ACCESS_READ, OPEN4_SHARE_ACCESS_WRITE, OPEN4_SHARE_ACCESS_BOTH]
    # deny = 0,1,2,3
    deny = [OPEN4_SHARE_DENY_NONE, OPEN4_SHARE_DENY_READ,
        OPEN4_SHARE_DENY_WRITE, OPEN4_SHARE_DENY_BOTH]

    for acc1 in acc:
        for deny1 in deny:
            for acc2 in acc:
                for deny2 in deny:
                    # Open with 1st access/deny
                    fh1, stateid1 = c.open_confirm(t.code, file_obj, access=acc1,
                        deny=deny1)

                    # Open with 2nd access/deny
                    secondopen = 0
                    res = c2.open_file(t.code, file_obj, access=acc2,
                        deny=deny2)

                    # Check result of 2nd open
                    if (acc1 & deny2) or (acc2 & deny1):
                        check(res, NFS4ERR_SHARE_DENIED, msg=openErrorToStr(acc1, deny1, acc2, deny2))
                    else:
                        check(res, msg=openErrorToStr(acc1, deny1, acc2, deny2))
                        secondopen = 1
                        fh2, stateid2 = c2.confirm(t.code, res)

                    # Close (both opens)
                    res = c.close_file(t.code, fh1, stateid1)
                    #check(res)
                    if secondopen:
                        res = c2.close_file(t.code, fh2, stateid2)
                        #check(res)

def testSolarisOpens(t, env):
    """ SOLARIS OPEN discovery test 1
    Discover what Solaris open semantics look like (Solaris does not pass
    OPENUP1 or OPENUP2).

    FLAGS: open all
    DEPEND: MKFILE
    CODE: OPENSOLARIS1
    """
    # XXX TODO Combine this test with OPENUP2

    c = env.c1
    c.init_connection()
    file_obj = c.homedir + [t.code]

    # Create file initially, then close it.
    fh, stateid = c.create_confirm(t.code, file_obj, access=OPEN4_SHARE_ACCESS_BOTH)
    res = c.close_file(t.code, fh, stateid)
    check(res)

    # acc = 1,2,3
    acc = [OPEN4_SHARE_ACCESS_READ, OPEN4_SHARE_ACCESS_WRITE, OPEN4_SHARE_ACCESS_BOTH]
    # deny = 0,1,2,3
    deny = [OPEN4_SHARE_DENY_NONE, OPEN4_SHARE_DENY_READ,
        OPEN4_SHARE_DENY_WRITE, OPEN4_SHARE_DENY_BOTH]

    for acc1 in acc:
        for deny1 in deny:
            for acc2 in acc:
                for deny2 in deny:
                    # Open with 1st access/deny
                    fh1, stateid = c.open_confirm(t.code, file_obj, access=acc1,
                        deny=deny1)

                    # Open with 2nd access/deny
                    secondopen = 0
                    res = c.open_file(t.code, file_obj, access=acc2,
                        deny=deny2)

                    # Check result of 2nd open
                    failed = 0
                    if (acc1 & deny2) or (acc2 & deny1):
                        try:
                            check(res, NFS4ERR_SHARE_DENIED, msg=openErrorToStr(acc1, deny1, acc2, deny2),
                                warnlist=[NFS4_OK])
                            failed = 1
                        except Exception as msg:
                            print msg

                    if failed == 0:
                        try:
                            check(res, msg=openErrorToStr(acc1, deny1, acc2, deny2))
                            secondopen = 1
                            fh2, stateid = c.confirm(t.code, res)
                        except Exception as msg:
                            print msg

                    # Close (both opens)
                    res = c.close_file(t.code, fh1, stateid)
                    check(res)

def testOpenDelete1(t, env):
    """ OPEN DELETE 1
    Single client: Test "delete" share reservations; deny_read stops nothing.

    FLAGS: open remove all
    DEPEND: MKFILE
    CODE: OPENDEL1
    """
    c = env.c1
    c.init_connection()

    file_obj = c.homedir + [t.code]

    # Create/open without write access, attempt to delete
    fh1, stateid1 = c.create_confirm(t.code, file_obj,
        access=OPEN4_SHARE_ACCESS_READ, deny=OPEN4_SHARE_DENY_READ)
    res = c.remove_obj(c.homedir, t.code)
    check(res)
    
    # Create/open with read/write access, delete file
    fh1, stateid1 = c.create_confirm(t.code, file_obj,
        access=OPEN4_SHARE_ACCESS_BOTH, deny=OPEN4_SHARE_DENY_READ)
    res = c.remove_obj(c.homedir, t.code)
    check(res)

    # Delete file without it being open
    fh1, stateid1 = c.create_confirm(t.code, file_obj)
    res = c.close_file(t.code, fh1, stateid1)
    check(res)
    res = c.remove_obj(c.homedir, t.code)
    check(res)


def testOpenDelete2(t, env):
    """ OPEN DELETE 2
    Two clients (same uid): Test "delete" share reservations; deny_read stops nothing.

    FLAGS: open remove all
    DEPEND: MKFILE
    CODE: OPENDEL2
    """
    c = env.c1
    c.init_connection()
    # c3 = same auth/UID as c1, different clientid
    c3 = env.c3
    c3.init_connection()

    file_obj = c.homedir + [t.code]

    # C1: create, then close
    # C3: attempt to delete unopened file
    fh1, stateid1 = c.create_confirm(t.code, file_obj)
    res = c.close_file(t.code, fh1, stateid1)
    check(res)
    res = c3.remove_obj(c.homedir, t.code)
    check(res)

    # C1: create/open without write access, no deny
    # C3: attempt to delete file
    fh1, stateid1 = c.create_confirm(t.code, file_obj,
        access=OPEN4_SHARE_ACCESS_READ, deny=OPEN4_SHARE_DENY_NONE)
    res = c3.remove_obj(c3.homedir, t.code)
    check(res)

    # C1: create/open without write access
    # C3: attempt to delete file
    fh1, stateid1 = c.create_confirm(t.code, file_obj,
        access=OPEN4_SHARE_ACCESS_READ, deny=OPEN4_SHARE_DENY_READ)
    res = c3.remove_obj(c3.homedir, t.code)
    check(res)
    
    # C1: create/open with read/write access
    # C3: attempt to delete file
    fh1, stateid1 = c.create_confirm(t.code, file_obj,
        access=OPEN4_SHARE_ACCESS_BOTH, deny=OPEN4_SHARE_DENY_READ)
    res = c3.remove_obj(c3.homedir, t.code)
    check(res)

# XXX Single-server: Linux and Solaris both fail this test. We don't.
# XXX With 2 nodes, we fail too.
def testOpenDelete3(t, env):
    """ OPEN DELETE 3
    Test "delete" share reservations by removing open files

    FLAGS: open remove all
    DEPEND: MKFILE
    CODE: OPENDEL3
    """
    # uid 0, clientid 1
    c = env.c1
    # uid 1, clientid 2
    c2 = env.c2
    # uid 0, clientid 3
    c3 = env.c3

    c.init_connection()
    file_obj = c.homedir + [t.code]

    # deny = 0,1,2,3
    deny = [OPEN4_SHARE_DENY_NONE, OPEN4_SHARE_DENY_READ,
        OPEN4_SHARE_DENY_WRITE, OPEN4_SHARE_DENY_BOTH]

    if env.opts.secondserver:
        print "secondserver"
        # secondserver. uid 0, clientid 1
        c1node2 = env.c1node2
        connections = [("clientid3", c3) , ("clientid1-node2", env.c1node2)]
    else:
        print "singleserver"
        connections = [("clientid3", c3)]
 
    # Loop through connections for the second connection
    for (connstr, conn) in connections:
        print "connstr = %s, id = %s" % (connstr, conn.id)
        conn.init_connection()

        # 1st client creates with RW/deny*, 2nd client tries to delete
        for deny1 in deny:
            print deny1
            fh1, stateid1 = c.create_confirm(t.code, file_obj,
                access=OPEN4_SHARE_ACCESS_BOTH, deny=deny1)
            res = conn.remove_obj(conn.homedir, t.code)
            if deny1 & OPEN4_SHARE_DENY_WRITE:
                print "should fail"
                check(res, NFS4ERR_FILE_OPEN,
                    msg="remove should not succeed with '%s' deny mode" %
                    denyToStr(deny1))

                # Make sure we close & delete the file, for next iteration
                res = c.close_file(t.code, fh1, stateid1)
                check(res)
                res = c.remove_obj(c.homedir, t.code)
                check(res)
            else:
                print "should succeed"
                check(res)

# XXX Use this to test Solaris & Linux.
#def testOpenRemoveReadWrite(t, env):

def testOpenRename1(t, env):
    """ OPEN RENAME 1
    Test "delete" share reservations by renaming open files

    XXX Linux?
    XXX Solaris?

    FLAGS: open rename all
    DEPEND: MKFILE
    CODE: OPENREN1
    """
    # XXX


def testOpenRemoveUnconfirmed(t, env):
    """ OPEN and REMOVE without confirming

    FLAGS: open remove all
    DEPEND: MKFILE
    CODE: OPENREMOVE
    """

    c = env.c1
    c.init_connection()
    res = c.create_file(t.code, deny=OPEN4_SHARE_DENY_BOTH, mode=GUARDED4)
    check(res, msg="creating")
    res = c.remove_obj(c.homedir, t.code)
    check(res, msg="removing")
    res = c.create_file(t.code, deny=OPEN4_SHARE_DENY_BOTH, mode=GUARDED4)
    check(res, msg="creating2");

#FRED - dot test
