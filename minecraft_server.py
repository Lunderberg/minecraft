#!/usr/bin/env python

from archive import archive
from passthrough import PassThrough
import os
from os.path import join
import shutil
from time import sleep
from threading import Thread
from datetime import datetime

class Server:
    def __init__(self,folder):
        self.archivefolder = folder
        self.foldername = 'minecraft_server'
        #self.runningfolder = '/dev/shm'
        self.runningfolder = '/tmp'
        self.isRunning = False
        self.passthrough = PassThrough(
            #['java','-Xmx1024M','-Xms1024M',
            ['java','-Xmx512M','-Xms512M',
             '-jar','minecraft_server.jar','nogui'],
            cwd=join(self.runningfolder,self.foldername))
    def CopyToWorking(self):
        try:
            shutil.rmtree(join(self.runningfolder,self.foldername))
        except OSError:
            pass
        mostrecent = 'hourly' if 'hourly' in os.listdir(self.archivefolder) \
            else 'currentref'
        shutil.copytree(
            join(self.archivefolder,mostrecent,self.foldername),
            join(self.runningfolder,self.foldername))
    def StopAutoSave(self,*args):
        with WaitForLine(self.passthrough,'Turned off world auto-saving'):
            self.passthrough.UserInput('save-off\n')
        with WaitForLine(self.passthrough,'Saved the world'):
            self.passthrough.UserInput('save-all\n')
    def ResumeAutoSave(self,*args):
        with WaitForLine(self.passthrough,'Turned on world auto-saving'):
            self.passthrough.UserInput('save-on\n')
    def DailyBackup(self,*args):
        print 'Performing daily backup'
        if self.running:
            self.StopAutoSave()
        archive(join(self.runningfolder,self.foldername),self.archivefolder)
        if os.path.exists(join(self.archivefolder,'hourly')):
            shutil.rmtree(join(self.archivefolder,'hourly'))
        if self.running:
            self.ResumeAutoSave()
        print 'Daily backup complete'
    def HourlyBackup(self,*args):
        print 'Performing hourly save'
        if self.running:
            self.StopAutoSave()
        archive(join(self.runningfolder,self.foldername),self.archivefolder,
                folder='hourly',update_currentref=False,overwrite=True)
        if self.running:
            self.ResumeAutoSave()
        print 'Hourly save complete'
    def run(self):
        self.CopyToWorking()
        self.passthrough.AddUserCond('^hourly$',self.HourlyBackup)
        self.passthrough.AddUserCond('^daily$',self.DailyBackup)
        BackupThread(self)
        self.running = True
        self.passthrough.run()
        self.running = False
        self.HourlyBackup()

class BackupThread(Thread):
    def __init__(self,server,*args,**kwargs):
        super(BackupThread,self).__init__()
        self.server = server
        self.daemon = True
        self.start()
    def WaitForHour(self):
        t = datetime.now()
        sec = 60*t.minute + t.second
        sleep(3600-sec)
    def run(self):
        while True:
            self.WaitForHour()
            if datetime.now().hour==2:
                self.server.DailyBackup()
            else:
                self.server.HourlyBackup()

class WaitForLine:
    def __init__(self,passthrough,regex):
        self.done = False
        self.regex = regex
        self.passthrough = passthrough
    def __enter__(self):
        self.done = False
        def temp(line):
            self.done = True
            return True
        self.passthrough.AddProgCond(self.regex,temp,count=1)
        return self
    def __exit__(self,*args):
        while not self.done:
            sleep(0.1)

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-a','--archive',dest='folder',
                        action='store',default=os.getcwd(),
                        help="The archive folder to be used.")
    args = parser.parse_args()
    s = Server(args.folder)
    s.run()
