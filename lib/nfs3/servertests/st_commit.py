from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *

def testNfs3Commit(t, env):
    """Commits changes to a file via the COMMIT rpc 
    
    
    FLAGS: nfsv3 commit all
    DEPEND: 
    CODE: COMMIT1
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    test_data = "Test String"
    mnt_fh = homedir_fh(env.mc, env.c1)
    
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1,
                        file_mode_val=0777)
    check(res, msg="CREATE - file %s" % test_file)
    test_file_fh = res.resok.obj.handle.data
    res = env.c1.write(test_file_fh, offset=0, count=len(test_data), stable=FILE_SYNC, data=test_data)
    check(res, msg="WRITE - file %s" % test_file)
        
    ### Execution Phase ###
    res = env.c1.commit(test_file_fh)
    
    ### Verification Phase ###
    check(res, msg="COMMIT of test file %s" % test_file)

### Variations:
#    Dir
#    Different file types (nodes, symlinks, links, etc)
#    No Permission
#    Different permissions

# XXX Once we have a "--long" option, we should bump up the datalen to 8GB
def testNfs3CommitLarge(t, env):
    """ Tests COMMIT with large amounts of writes beforehand. Dial up the
    datalen for an even larger filesize.

    FLAGS: nfsv3 commit all
    DEPEND:
    CODE: COMMIT2
    """
    ### Setup Phase ###
    datalen = 512 * 1024 * 1024
    writesize = 512 * 1024
    test_data = "a" * writesize

    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)

    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1,
                        file_mode_val=0777)
    check(res, msg="CREATE - file %s" % test_file)
    test_file_fh = res.resok.obj.handle.data

    # WRITE in a loop until we write datalen
    offset = 0
    wlen = writesize
    while (offset < datalen):
        if (datalen - offset < writesize):
            wlen = datalen - offset
            test_data = "a" * wlen

        print "Writing offset = %ld, length = %d" % (offset, wlen)
        res = env.c1.write(test_file_fh, offset=offset, count=wlen, stable=UNSTABLE, data=test_data)
        check(res, msg="WRITE - file %s - offset=%ld - len=%d" % (test_file, offset, wlen))

        offset = offset + wlen

    ### Execution Phase ###
    offset = 0
    print "Committing %d data at offset %d" % (datalen, offset)
    res = env.c1.commit(test_file_fh, offset, datalen)

    ### Verification Phase ###
    check(res, msg="COMMIT of test file %s" % test_file)

def testNfs3CommitLargeValuesNoWrite(t, env):
    """ Tests COMMIT with large values. No reason to write beforehand. This
    repros bug 77753.

    FLAGS: nfsv3 commit all
    DEPEND:
    CODE: COMMIT3
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)

    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1,
                        file_mode_val=0777)
    check(res, msg="CREATE - file %s" % test_file)
    test_file_fh = res.resok.obj.handle.data

    ### Execution Phase ###
    offset = 3500000000
    datalen = 4000000000
    res = env.c1.commit(test_file_fh, offset, datalen)
    check(res, msg="COMMIT of test file %s" % test_file)
