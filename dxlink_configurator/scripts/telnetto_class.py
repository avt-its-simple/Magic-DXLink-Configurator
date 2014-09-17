"""Opens a subprocess to launch the telnet client"""

import threading 
import subprocess
import os

class TelnetToThread(threading.Thread):
    """Telnet to thread"""

    def __init__(self, parent, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.parent = parent

    def run(self):
        while True:
            # gets the job from the queue
            obj = self.queue.get()

            if os.name == 'nt':
                if self.parent.telnet_client == 'putty.exe':
                    subprocess.call([(self.parent.path + 
                                      self.parent.telnet_client),
                                      ('telnet://' + obj.ip_address)])
                else:                
                    subprocess.call((self.parent.path + self.parent.telnet_client +
                                  " " + obj.ip_address))
            if os.name == 'posix':
                subprocess.call(('telnet', obj.ip_address)) 

