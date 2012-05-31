# testmod.py - run tests from a suite
#
# Requires python 2.3
# 
# Written by Fred Isaman <iisaman@citi.umich.edu>
# Copyright (C) 2004 University of Michigan, Center for 
#                    Information Technology Integration
#
import nfs4.nfs4lib
import nfs3.mountlib
import nfs3.nfs3lib
import re
import sys
import time
import traceback
from traceback import format_exception

if 'sum' not in __builtins__:
    def sum(seq, start=0):
        return reduce(lambda x,y: x+y, seq, start)

# Possible outcomes
TEST_NOTRUN  = 0    # Not yet considered
TEST_RUNNING = 1    # Test actually running
TEST_WAIT    = 2    # Waiting for dependencies to run
TEST_OMIT    = 3    # Test skipped
TEST_FAIL    = 4    # Test failed
TEST_NOTSUP  = 5    # Counts as WARN, but considered a failed dependency
TEST_WARN    = 6    # Technically a PASS, but there was a better way
TEST_PASS    = 7    # Test passed
TEST_TOOLONG = 8    # Test succeeded, but took too long!
TEST_TOOLONGFAIL = 9 # Test failed AND took too long!
DEP_FUNCT    = 100  # Used for depency functions

class Result(object):
    outcome_names = { TEST_NOTRUN : "NOT RUN",
                      TEST_RUNNING: "RUNNING",
                      TEST_WAIT   : "WAITING TO RUN",
                      TEST_OMIT   : "OMIT",
                      TEST_FAIL   : "FAILURE",
                      TEST_NOTSUP : "UNSUPPORTED",
                      TEST_WARN   : "WARNING",
                      TEST_PASS   : "PASS",
                      TEST_TOOLONG: "TOOLONG",
                      TEST_TOOLONGFAIL: "TOOLONGFAIL",
                      DEP_FUNCT   : "DEPENDENCY FUNCTION"
                      }

    def __init__(self, outcome=TEST_NOTRUN, msg="", tb=None, default=False):
        self.outcome = outcome
        self.msg = str(msg)
        self.default = default
        if tb is None:
            self.tb = []
        else:
            #self.tb = ''.join(format_exception(*tb))
            self.tb = format_exception(*tb)

    def __str__(self):
        return self.outcome_names[self.outcome]

    def __repr__(self):
        return '\n'.join([self.__str__(), self.msg])

    def __eq__(self, other):
        if type(other) == type(0):
            return self.outcome == other
        else:
            return id(self) == id(other)

    def __ne__(self, other):
        if type(other) == type(0):
            return self.outcome != other
        else:
            return id(self) != id(other)

class TestException(Exception):
    pass

class UnsupportedException(TestException):
    def __init__(self, *args):
        self.type = TEST_NOTSUP
        TestException.__init__(self, *args)

class FailureException(TestException):
    def __init__(self, *args):
        self.type = TEST_FAIL
        TestException.__init__(self, *args)

class WarningException(TestException):
    def __init__(self, *args):
        self.type = TEST_WARN
        TestException.__init__(self, *args)

class Test(object):
    _keywords = ["FLAGS", "DEPEND", "CODE"]
    _pass_result = Result(TEST_PASS, default=True)
    _run_result = Result(TEST_RUNNING, default=True)
    _wait_result = Result(TEST_WAIT, "Circular dependency", default=True)
    _omit_result = Result(TEST_OMIT, "Failed runfilter", default=True)
    _funct_result = Result(DEP_FUNCT, default=True)
    _toolong_result = Result(TEST_TOOLONG, default=True)
    _toolongfail_result = Result(TEST_TOOLONGFAIL, default=True)
    __re = re.compile(r'(\D*)(\d*)(.*)')

    def __init__(self, function, module=""):
        """Needs function to be run"""
        self.runtest = function
        self.multiconn = False
        self.afterrun_list = []
        self.name = function.__name__
        if module:
            self.fullname = module.split('.')[-1] + '.' + self.name
        else:
            self.fullname = self.name
        self.doc = function.__doc__.split('\n')[0].strip()
        #self.doc = function.__doc__.strip()
        self.result = Result()
        self._read_docstr(function.__doc__)

    def _read_docstr(self, s):
        """Searches s for 'keyword: list' and stores resulting lists"""
        for key in self._keywords:
            p = re.compile(r'^\s*' + key +':(.*$)', re.MULTILINE)
            match = p.search(str(s))
            if match is None:
                setattr(self, key.lower() + '_list', [])
            else:
                setattr(self, key.lower() + '_list', match.group(1).split())

    def __getstate__(self):
        """Remove function reference when pickling

        This vastly reduce size of the output file, while at the same
        time making it more robust to function/class renames.  However,
        if we need to restore this info for some reason, will need a
        __setstate__ function to try and recover it.
        """
        d = self.__dict__.copy()
        del d["runtest"]
        del d["dependencies"]
        del d["flags"]
        return d

##     def __cmp__(self, other):
##         if self.code < other.code:
##             return -1
##         elif self.code == other.code:
##             return 0
##         else:
##             return 1

    def __cmp__(self, other):
        me = self.__re.match(self.code)
        me = (me.group(1), int(me.group(2).zfill(1)), me.group(3))
        you = self.__re.match(other.code)
        you = (you.group(1), int(you.group(2).zfill(1)), you.group(3))
        if me < you:
            return -1
        elif me == you:
            return 0
        else:
            return 1

    def __str__(self):
        return "%-8s %s" % ( self.code, self.fullname)

    def __repr__(self):
        if self.result.msg:
            return "%-65s : %s\n%s" % (self, self.result, self._format(self.result.msg))
        else:
            return "%-65s : %s" % (self, self.result)

    def display(self, showdoc=False, showtrace=False):
        out = "%-65s : %s" % (str(self), str(self.result))
        if showdoc:
            out += "\n%s" % self._format(self.doc, 5, 70)
        if showtrace and self.result.tb:
            out += "\n%s" % ''.join(self.result.tb)
        elif self.result.msg:
            out += "\n%s" % self._format(self.result.msg, 11, 64)
        return out


    def _format(self, s, start_col=11, end_col=64):
        s = str(s)
        indent = ' ' * (start_col - 1)
        out = indent
        lout = len(out)
        words = s.split()
        for w in words:
            lw = len(w)
            if lout + lw > end_col and lout > start_col:
                out += '\n' + indent
                lout = start_col - 1
            out += ' ' + w
            lout += lw + 1
        return out
            
    def fail(self, msg):
        raise FailureException(msg)

    def fail_support(self, msg):
        raise UnsupportedException(msg)

    def pass_warn(self, msg):
        raise WarningException(msg)

    def __info(self):
        #return sys.exc_info()
        exctype, excvalue, tb = sys.exc_info()
        if sys.platform[:4] == 'java': ## tracebacks look different in Jython
            return (exctype, excvalue, tb)
        newtb = tb.tb_next
        if newtb is None:
            return (exctype, excvalue, tb)
        return (exctype, excvalue, newtb)

    def run(self, environment, options):
        """Run self.runtest, storing result"""
        verbose = getattr(options, 'verbose', False)
        timeout = getattr(options, 'timeout', 0)
        showtime = getattr(options, 'showtime', True)

        #print "*********Running test %s (%s)" % (self.name, self.code)
        self.result = self._run_result
        if verbose:
            print repr(self)
        try:
            time1 = time.time()
            environment.startUp()
            self.runtest(self, environment)
            self.result = self._pass_result
        except KeyboardInterrupt:
            raise
        except TestException, e:
            self.result = Result(e.type, e, sys.exc_info())
        except StandardError, e:
            self.result = Result(TEST_FAIL, '', sys.exc_info())
            self.result.msg = self.result.tb[-1]
            traceback.print_exc()
        except Exception, e:
            self.result = Result(TEST_FAIL, e, sys.exc_info())
            traceback.print_exc()
        try:
            environment.shutDown()
        except StandardError, e:
            self.result = Result(TEST_FAIL, '', sys.exc_info())
            self.result.msg = self.result.tb[-1]
            traceback.print_exc()

        # Print out test time if 'showtime' is enabled.
        time2 = time.time()
        testtime = time2 - time1
        if showtime:
            print "test took %f seconds!" % (testtime)

        # Change result to TOOLONG or TOOLONGFAIL if the test ran over the
        # "timeout" time. If "timeout" == 0, don't change the result.
        if timeout > 0 and testtime > timeout:
            print "test took %f seconds, which exceeded the timeout of %d " \
                "seconds!" % (testtime, timeout)
            if self.result == self._pass_result:
                self.result = self._toolong_result
            else:
                self.result = self._toolongfail_result

        if verbose:
            print repr(self) + "\n"

    def runmulticonn(self, env, options):
        #print "\nRunning MULTICONN test=%s" % self

        num = 1
        testcode = self.code

        for (connstr, conn) in env.secondconns:
            #print "%d: connstr = %s, id = %s" % (num, connstr, conn.id)

            # Set environment's "second connection"
            env.secondconn = conn

            # Set test's code name, temporarily
            self.code = testcode + str(num)

            # Run test
            self.run(env, options)
            num = num + 1

        # OMIT test if no secondconns
        if num == 1:
            self.result = self._omit_result

        env.secondconn = None
        self.code = testcode

class Environment(object):
    """Base class for a test environment"""
    def __init__(self, opts):
        self.opts = opts

    def init(self):
        """Run once before any test is run"""
        pass

    def finish(self):
        """Run once after all tests are run"""
        pass

    def startUp(self):
        """Run before each test"""
        pass

    def shutDown(self):
        """Run after each test"""
        pass
        
def _run_filter(test, options):
    """Returns True if test should be run, False if it should be skipped"""
    return True

def runtests(tests, options, environment, runfilter=_run_filter):
    """tests is an array of test objects, to be run in order
    
    (as much as possible)
    """
    for t in tests:
        if t.result == TEST_NOTRUN:
            _runtree(t, options, environment, runfilter)
        else:
            # Test has already been run in a dependency tree
            pass

def _runtree(t, options, environment, runfilter=_run_filter):
    if t.result == TEST_WAIT:
        return
    t.result = t._wait_result
    if not runfilter(t, options):
        # Check flags to see if test should be omitted
        t.result = t._omit_result
        return
    if options.rundeps:
        runfilter = lambda x, y : True
    for dep in t.dependencies:
        if dep.result == DEP_FUNCT:
            if (not options.force) and (not dep(t, environment)):
                t.result = Result(TEST_OMIT, 
                                  "Dependency function %s failed" %
                                  dep.__name__)
                return
            continue
        if dep.result == t._omit_result and options.rundeps:
            _runtree(dep, options, environment, runfilter)
        elif dep.result in [TEST_NOTRUN, TEST_WAIT]:
            _runtree(dep, options, environment, runfilter)
            # Note dep.result has now changed
        if dep.result == TEST_WAIT:
            return
        elif (not options.force) and \
                 (dep.result in [TEST_OMIT, TEST_FAIL, TEST_NOTSUP]):
            t.result = Result(TEST_OMIT, 
                              "Dependency %s had status %s." % \
                              (dep, dep.result))
            return

    # ISILON: MULTICONN
    if t.multiconn:
        t.runmulticonn(environment, options)
    else:
        t.run(environment, options)

    # MULTICONN: Run after-run tests.
    for t2 in t.afterrun_list:
        _runtree(t2, options, environment)

def _import_by_name(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def get_multiconn_testname(name):
    return name + "_MULTICONN"

def createtests(testdirs):
    """ Tests are functions that start with "test".  Their docstring must
    contain a line starting with "FLAGS:" and a line starting with "CODE:".
    It may optionall contain a line starting with "DEPEND:".  Each test must
    have a unique code string.  The space seperated list of flags must
    not contain any code names.  The depend list is a list of code names for
    tests that must be run before the given test.
    """
    # Find all tests in testdir
    tests = []
    for testdir in testdirs:
        package = _import_by_name(testdir)
        for testfile in package.__all__:
            if testfile.endswith('.py'):
                testfile = testfile[:-3]
            testmod = ".".join([testdir, testfile])
            mod = _import_by_name(testmod)
            for attr in dir(mod):
                if attr.startswith("test"):
                    f = getattr(mod, attr)
                    t = Test(f, testmod)
                    tests.append(t)
                    # ISILON: Add additional MULTICONN test
                    if "multiconn" in t.flags_list:
                        t2 = Test(f, testmod)
                        t2.multiconn = True
                        t2.code_list[0] = get_multiconn_testname(t2.code_list[0])
                        # Force the _MULTICONN test to run after the original test
                        t.afterrun_list.append(t2)
                        tests.append(t2)

    # Reduce doc string info into format easier to work with
    used_codes = {}
    flag_dict = {}
    bit = 1L
    for t in tests:
        if not t.flags_list:
            raise Exception("%s has no flags" % t.fullname)
        for f in t.flags_list:
            if f not in flag_dict:
                flag_dict[f] = bit
                bit <<= 1
        if len(t.code_list) != 1:
            raise Exception("%s needs exactly one code" % t.fullname)
        t.code = t.code_list[0]
        if t.code in used_codes:
            raise Exception("%s trying to use a code already used"  % t.fullname)
        used_codes[t.code] = t
        del t.code_list
    # Check that flags don't contain a code word
    for f in flag_dict:
        if f in used_codes:
            raise Exception("flag %s is also used as a test code" % f)
    # Now turn dependency names into pointers, and flags into a bitmask
    for t in tests:
        t.flags = sum([flag_dict[x] for x in t.flags_list])
        t.dependencies = []
        for d in t.depend_list:
            if d in used_codes:
                t.dependencies.append(used_codes[d])
            else:
                mod = _import_by_name(t.runtest.__module__)
                if not hasattr(mod, d):
                    raise Exception("Could not find reference to dependency %s" % str(d))
                funct = getattr(mod, d)
                if not callable(funct):
                    raise Exception("Dependency %s of %s does not exist" %
                          (d, t.fullname))
                funct.result = t._funct_result
                t.dependencies.append(funct)
    return tests, flag_dict, used_codes


def printresults(tests, opts, file=None):
    failures = 0
    NOTRUN, OMIT, SKIP, FAIL, WARN, PASS, TOOLONG, TOOLONGFAIL = range(8)
    count = [0] * 8
    for t in tests:
        if not hasattr(t, "result"):
            print dir(t)
            print t.__dict__
            raise
        if t.result == TEST_NOTRUN:
            count[NOTRUN] += 1
        elif t.result == TEST_OMIT and t.result.default:
            count[OMIT] += 1
        elif t.result in [TEST_WAIT, TEST_OMIT]:
            count[SKIP] += 1
        elif t.result == TEST_FAIL:
            count[FAIL] += 1
        elif t.result in [TEST_NOTSUP, TEST_WARN]:
            count[WARN] += 1
        elif t.result == TEST_PASS:
            count[PASS] += 1
        elif t.result == TEST_TOOLONG:
            count[TOOLONG] += 1
        elif t.result == TEST_TOOLONGFAIL:
            count[TOOLONGFAIL] += 1
    print >> file, "*"*50
    for t in tests:
        if t.result == TEST_NOTRUN:
            continue
        if t.result == TEST_OMIT and t.result.default:
            continue
        if (not opts.showomit) and t.result == TEST_OMIT:
            continue
        if (not opts.showpass) and t.result == TEST_PASS:
            continue
        if (not opts.showwarn) and t.result in [TEST_NOTSUP, TEST_WARN]:
            continue
        if (not opts.showfail) and t.result == TEST_FAIL:
            continue
        print >> file, t.display(0,0)
    print >> file, "*"*50
    if count[NOTRUN]:
        print >> file, "Tests interrupted! Only %i tests run" % \
              sum(count[SKIP:])
    else:
        print >> file, "Command line asked for %i of %i tests" % \
              (sum(count[SKIP:]), len(tests))
    print >> file, "Of those: %i Skipped, %i Failed, %i Warned," \
          "%i Passed, %i TooLongPass, %i TooLongFail" % \
          (count[SKIP], count[FAIL], count[WARN], count[PASS], \
           count[TOOLONG], count[TOOLONGFAIL])

    # TEMP_FAILURES / TEMP_WARNINGS are the tests that we have yet to fix.
    # COMP3 - Unicode. FIXME
    # OPDG2/OPDG3 - Open downgrade subset issues.
    # OPEN19 - Needs spec clarification. Inconclusive data here:
    #          http://old.nabble.com/open-share-modes-and-file-permissions-td26340522r0.html
    # OPENDEL3 - Share modes FIXME
    # OPENUP2_MULTICONN - Share modes FIXME
    TEMP_FAILURES = ['COMP3', 'OPDG2', 'OPDG3', 'OPEN19', 'OPENDEL3',
                     'EXP5', 'XPT8']

    # If secondserver is configured SECONDSERV1 should pass and dependent
    # tests that are not normally run will run and fail
    if (opts.secondserver == None):
        TEMP_FAILURES += ['SECONDSERV1']
    else:
        TEMP_FAILURES += ['LKU1m_MULTICONN', 'LOCK1m_MULTICONN']

    #Appending nfsv3 expected failures
    # CREATE7: Fails unless vfs.nfsrv.create_attributes_ids_enabled = 1
    TEMP_FAILURES.extend(['MKNOD1', 'CREATE7'])

    TEMP_WARNINGS = ['LOCK8c', 'MKBLK', 'MKCHAR', 'RD12', 'SATT2c',
    'SATT9']

    # The following failures/warnings are expected to fail/warn because of
    # various reasons, as explained below:

    # WRT12, RD11: fail unless sysctl vfs.nfsrv.nfsv4.nfs4_returnoldstateid = 1
    # SATT2c: Returning BAD_STATEID makes sense to me... (ZLK)
    # LINK2: fails due to order of errors - works as expected with adjusted input
    # LOOKBLK / LOOKCHAR: requires test client to run as root and the export
    #	must have --maproot=root
    # CID1: order of errors - STALECLIENTID defaults to EXPIRED.
    # OPEN16: We now trust all reclaims, at least until lk can failover nfs
    #   locks.
    # SEC7: This works on an export with '--security-options=sys:krb5'
    # GATTACL: This works with sysctl vfs.nfsrv.nfsv4.acls_return_synthetic=1
    ALLOWED_FAILURES = ['WRT12', 'RD11', 'SATT2c', 'LINK2', 'LOOKBLK', 'LOOKCHAR',
    'CID1', 'OPEN16', 'SEC7', 'GATTACL']

    # Missing features
    FSLOCATIONS_FAILURES = ['FSLOC1', 'FSLOC2', 'FSLOC4a', 'FSLOC4b', 'FSLOC5a',
    'FSLOC6a', 'FSLOC6b', 'FSLOC7a', 'FSLOC8a', 'FSLOC8b']
    BLOCKING_LOCKS_WARNINGS = ['LOCK18', 'LOCK19', 'LOCK21', 'LOCK22']
    DELEGATIONS_WARNINGS = ['DELEG1', 'DELEG11', 'DELEG12', 'DELEG13a',
    'DELEG13b', 'DELEG13c', 'DELEG13d', 'DELEG13e', 'DELEG14', 'DELEG15',
    'DELEG2', 'DELEG3a', 'DELEG3b', 'DELEG3c', 'DELEG3d', 'DELEG3e', 'DELEG4',
    'DELEG5', 'DELEG6', 'DELEG7', 'DELEG8', 'DELEG9']

    # The following tests have intermittent failures but we are keeping them
    # for now because they have caused panics
    IGNORE_RESULTS = ['XPT1', 'XPT2', 'XPT3', 'XPT4', 'XPT5', 'XPT6', 'XPT7',
                      'XPT8', 'XPT9', 'XPT10']

    EXPECTED_FAILURES = TEMP_FAILURES + FSLOCATIONS_FAILURES + ALLOWED_FAILURES
    EXPECTED_WARNINGS = TEMP_WARNINGS + BLOCKING_LOCKS_WARNINGS + DELEGATIONS_WARNINGS

    print >> file, "*"*50
    print >> file, "Isilon results:"
    for t in tests:
        ignore_results = t.code in IGNORE_RESULTS
        if t.result == TEST_FAIL or t.result == TEST_TOOLONGFAIL:
            if t.code in EXPECTED_FAILURES:
                EXPECTED_FAILURES.remove(t.code)
            elif t.code in EXPECTED_WARNINGS:
                print >> file, "Unexpected test FAILURE: %s (expected WARNING)" % t.code
                if not ignore_results:
                    failures += 1
                else:
                    print >> file, "Ignoring FAILURE for test %s" % t.code
            else:
                print >> file, "Unexpected test FAILURE: %s (expected PASS)" % t.code
                if not ignore_results:
                    failures += 1
                else:
                    print >> file, "Ignoring FAILURE for test %s" % t.code
        elif t.result in [TEST_NOTSUP, TEST_WARN]:
            if t.code in EXPECTED_WARNINGS:
                EXPECTED_WARNINGS.remove(t.code)
            elif t.code in EXPECTED_FAILURES:
                print >> file, "Unexpected test WARNING: %s (expected FAILURE)" % t.code
                if not ignore_results:
                    failures += 1
                else:
                    print >> file, "Ignoring WARNING for test %s" % t.code
            else:
                print >> file, "Unexpected test WARNING: %s (expected PASS)" % t.code
                if not ignore_results:
                    failures += 1
                else:
                    print >> file, "Ignoring WARNING for test %s" % t.code
        elif t.result == TEST_PASS:
            if t.code in EXPECTED_FAILURES:
                print >> file, "Unexpected test PASS: %s (expected FAILURE)" % t.code
                if not ignore_results:
                    failures += 1
                else:
                    print >> file, "Ignoring PASS for test %s" % t.code
            elif t.code in EXPECTED_WARNINGS:
                print >> file, "Unexpected test PASS: %s (expected WARNING)" % t.code
                if not ignore_results:
                    failures += 1
                else:
                    print >> file, "Ignoring PASS for test %s" % t.code

    if (failures == 0):
        print >> file, "\nYou have PASSED with flying colors.\n"

    return failures

#    faillist = []
#    warnlist = []
#    for t in tests:
#        if t.result == TEST_FAIL:
#            faillist.append(t.code)
#        elif t.result in [TEST_NOTSUP, TEST_WARN]:
#            warnlist.append(t.code)
#    print "Failing tests = ", faillist
#    print "(Length = ", len(faillist), ")"
#    print "Warning tests = ", warnlist
#    print "(Length = ", len(warnlist), ")"
