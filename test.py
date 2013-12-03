#!/usr/bin/python

from pydaemon import Daemon
import time, logging

class myService(Daemon):
    def __init__(self):
        Daemon.__init__(self,"myService")
        
    def run(self):
        while True:
            print "toto"
            logging.info("plop")
            time.sleep(2)
        
if __name__ == "__main__":
    ms = myService()
    ms.main()