#!/usr/bin/python

### no licence, the author declare this code is in the public domain in a comment ###
#website : http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
#orignal author : Sander Marechal
#

LOGPATH = "/var/log/"

import sys, os, time, atexit, logging
from signal import SIGTERM

def getLogNextId(MAINREP):
    return len([name for name in os.listdir(MAINREP) if os.path.isfile(MAINREP+name)])

def usage():
    print "usage: %s start|stop|restart|test [nolog]" % sys.argv[0]

class Daemon:
    nextId = -1

    """
    A generic daemon class.
       
    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, processname, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.logrep        = LOGPATH+processname+"/"
        self.localid       = -1
        self.stdin         = stdin
        self.stdout        = stdout
        self.stderr        = stderr
        self.pidfile       = "/tmp/daemon-"+processname+".pid"
        self.processname   = processname
        self.debug         = False
        self.loggingEnable = True
    
    def setLogPath(self,logpath):
        self.logrep = logpath+processname+"/"
    
    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)
       
        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)
       
        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)
       
        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
       
        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)
       
    def delpid(self):
        os.remove(self.pidfile)
 
    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
       
        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)
           
        # Start the daemon
        self.daemonize()
        self.localRun()
 
    def info(self,msg):
        logging.info(msg)
 
    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
       
        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart
 
        # Try killing the daemon process       
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)
 
    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()
 
    def localRun(self):
        #prepare loggin information
        if self.loggingEnable:
            self.localid = nextId = getLogNextId(self.logrep)
            if self.debug:
                logging.basicConfig(format='%(asctime)s %(message)s',level=logging.DEBUG)
            else:    
                logging.basicConfig(format='%(asctime)s %(message)s', filename=self.logrep+'messages_'+str(nextId)+"_"+str(os.getpid())+'.log',level=logging.INFO)        
            print "start"
            logging.info(self.processname+" start, log id : "+str(nextId))
        
        self.run()
 
    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        pass #XXX override

    def main(self):
        if len(sys.argv) > 1:
            if len(sys.argv) > 2:
                if "nolog" == sys.argv[2]:
                    self.loggingEnable = False
                else:
                    print "unknown second parameter: "+sys.argv[2]
        
            #check if can write the log directory and log file
            if self.loggingEnable:
                if not os.path.exists(self.logrep):
                    print "directory <"+self.logrep+"> does not exist or is not accessible"
                
                    try:
                        os.makedirs(self.logrep, 0755)
                    except OSError as e:
                        print "    failed to create log directory : "+str(e.strerror)
                        print "    maybe you need root privilege or file system is read only"
                        print ""
                        sys.exit(2)
                elif not os.access(self.logrep, os.W_OK):
                    print "directory <"+self.logrep+"> is not writtable"
                    print " maybe you need root privilege or file system is read only"
                    print ""
                    sys.exit(2)
                    
            if 'start' == sys.argv[1]:
                self.start()
            elif 'stop' == sys.argv[1]:
                self.stop()
            elif 'restart' == sys.argv[1]:
                self.restart()
            elif 'test' == sys.argv[1]:
                self.debug = True
                self.localRun()
            else:
                print "Unknown command"
                sys.exit(2)
            sys.exit(0)
        else:
            usage()
            sys.exit(2)
    