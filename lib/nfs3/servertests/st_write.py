from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *
import threading
import time
import os

def testNfs3Write(t, env):
    """ Write test data into a file via WRITE rpc, 
        read the file and verify the output 
        
    FLAGS: nfsv3 write all
    DEPEND:
    CODE: WRITE1
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    test_data = "Test String"
    
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777)
    check(res, msg="CREATE - file %s" % test_file)
    test_file_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c1.write(test_file_fh, offset=0, count=len(test_data), stable=FILE_SYNC, data=test_data)
    
    ### Verification Phase ###
    check(res, msg="WRITE - file %s" % test_file)
    if res.resok.count != len(test_data):
        t.fail_support(" ".join([
            "WRITE - response: data returned [%d]" % res.resok.count,
            "bytes of data written.  [%d] bytes expected" % len(test_data)]))
    res = env.c1.read(test_file_fh, offset=0, count=len(test_data))
    check(res, msg="READ - file %s" % test_file)
    if res.resok.data != test_data:
        t.fail.support(" ".join([
            "WRITE - operation returned [%s]." % res.resok.data,
            "[%s] expected."  % test_data]))
    if res.resok.count != len(test_data):
        t.fail_support(" ".join([
            "WRITE - operation returned [%d] bytes." % res.resok.count,
            "[%d] bytes expected." % len(test_data)]))

    ### Clean-up Phase? ###

def testNfs3MultiWriter(t, env):
    """ Testcase for Mavericks multiwriter

    FLAGS: nfsv3 write all
    DEPEND:
    CODE: WRITEMW1
    """

    WRITECOUNT=1024*1024*20
    OFFSET=1024*WRITECOUNT
    THREADS=10

    test_file = t.name
    test_dir = t.name
    mnt_fh = homedir_fh(env.mc, env.c1)

    data = ""
    for i in range(0, 256):
        data = data + chr(i)

    # Setup
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg = "mkdir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data

    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1,
        file_mode_val=0777)
    check(res, msg = "create %s" % test_file)
    test_file_fh = res.resok.obj.handle.data

    # Preallocate
    print "Preallocating"
    clients = {}
    for thread in range(0, THREADS):
        print "Preallocating at offset = %d" % (thread*OFFSET)
        writeThread(t, env, env.c1, test_file_fh, thread*OFFSET, WRITECOUNT,
            FILE_SYNC, "*")

        # Use a different client connection for each thread
        clients[thread] = NFS3Client('client1_pid%i_thread%i' % (os.getpid(), thread),
            env.opts.server, env.nfs3port, env.opts.path[-1],
            sec_list=[env.sec1], opts=env.opts)

    # Sleep to allow preallocation to settle
    #time.sleep(1)

    # XXX Start timer and write to multiple places at the same time via
    # multiple threads

    print "Running threads"
    threads = []
    fail_event = threading.Event()
    for thread in range(0, THREADS):
        threads.append(threading.Thread(target=writeThread,
            args=(t, env, clients[thread], test_file_fh, thread*OFFSET,
                WRITECOUNT, FILE_SYNC, data, fail_event)))

    start = time.time()
    for thread in range(0, THREADS):
        threads[thread].start()
    for thread in range(0, THREADS):
        threads[thread].join()
    elapsed = time.time() - start
    print "Elapsed time = " + str(elapsed)

    if fail_event.is_set():
        t.fail("One or more of the write threads failed!")

    print "Verifying, threaded"
    threads = []
    for thread in range(0, THREADS):
        threads.append(threading.Thread(target=verifyWriteThread,
            args=(t, env, clients[thread], test_file_fh, thread*OFFSET,
                WRITECOUNT, data, fail_event)))
    for thread in range(0, THREADS):
        threads[thread].start()
    for thread in range(0, THREADS):
        threads[thread].join()

    if fail_event.is_set():
        t.fail("One or more of the write threads failed!")

def verifyWriteThread(t, env, client, test_file_fh, offset, size, exp_data,
    fail_event=None):

    READSIZE=32*1024
    #READSIZE=1024

    try:
        if size % READSIZE != 0:
            t.fail("Read size is not a multiple of total data size!")

        exp_datalen = len(exp_data)
        #print "READ: expected=%d" % exp_datalen
        if size % exp_datalen != 0:
            t.fail("Expected data length is not a multiple of total size!")
        diff = size / exp_datalen
        exp_newdata = exp_data * diff
        exp_newdatalen = exp_datalen * diff
        #print "READ: exp_total=%d" % exp_newdatalen

        if exp_newdatalen != size:
            t.fail("ERROR with converting data length to write size!")

        eof = False
        totaldata = ""
        totalcount = 0

        for off in range(offset, offset+size, READSIZE):
            if eof:
                t.fail("ERROR: Hit EOF, but not expecting it")

            #print "Reading offset=%d, count=%d" % \
            #    (off, READSIZE)
            res = client.read(test_file_fh, offset=off, count=READSIZE)
            check(res, msg="READ: offset = %d, count = %d" % (off, READSIZE))
            #print res
            count = res.resok.count
            eof = res.resok.eof
            data = res.resok.data
            #print "DATA READ: Read %d bytes at offset %d" % (count, off)

            if len(data) != count:
                t.fail("ERROR: Length of data = %d, count = %d" %
                    (len(data), count))

            if count != READSIZE:
                t.fail("ERROR: SHORT READ. Expected %d, read %d" %
                    (READSIZE, count))

            totalcount = totalcount + count
            totaldata = totaldata + data

        print "Total data read = %d" % totalcount

        # Verify read data against expected
        if totalcount != size:
            t.fail("READ: Expected %d bytes, read %d bytes" %
                (exp_newdatalen, totalcount))

        if totaldata != exp_newdata:
            t.fail("READ: Got bad data!")

    except Exception:
        if fail_event is not None:
            fail_event.set()
        raise

# Write (some data) in chunks of a writeable size
# TODO This could be abstracted out more to provide more to callers
def writeThread(t, env, client, test_file_fh, offset, size, stable, data,
    fail_event=None):

    WRITESIZE=32*1024
    #WRITESIZE=1024

    try:
        if size % WRITESIZE != 0:
            t.fail("Write size is not a multiple of total data size!")

        datalen = len(data)
        if WRITESIZE % datalen != 0:
            t.fail("Individual data length is not a multiple of write size!")
        diff = WRITESIZE / datalen
        newdata = data * diff

        if len(newdata) != WRITESIZE:
            t.fail("ERROR with converting data length to write size!")

        datadone = 0

        for off in range(offset, offset+size, WRITESIZE):
            #print "Writing type=%d, offset=%d, count=%d" % \
            #    (stable, off, WRITESIZE)
            res = client.write(test_file_fh, offset=off, count=WRITESIZE,
                stable=stable, data=newdata)
            check(res, msg="WRITE: type = %d, offset = %d, count = %d" %
                (stable, off, WRITESIZE))
            #print res

            datadone = datadone + WRITESIZE

        print "Data done = %d" % datadone

    except Exception:
        if fail_event is not None:
            fail_event.set()
        raise

### ToDo: Add basic negative cases.  Beef up coverage

### Append
### Overwrite
### Offset write
### Partial write (i.e. testing the count param)
### Negative cases (i.e. no permsm  
