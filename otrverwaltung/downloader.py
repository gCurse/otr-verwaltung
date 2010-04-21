# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Benjamin Elbers <elbersb@gmail.com>
#This program is free software: you can redistribute it and/or modify it 
#under the terms of the GNU General Public License version 3, as published 
#by the Free Software Foundation.
#
#This program is distributed in the hope that it will be useful, but 
#WITHOUT ANY WARRANTY; without even the implied warranties of 
#MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
#PURPOSE.  See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License along 
#with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import subprocess
import re
import time
import sys

from otrverwaltung.GeneratorTask import GeneratorTask

class DownloadTypes:
    TORRENT     = 0

    BASIC       = 4

    OTR_DECODE  = 2
    OTR_CUT     = 3    

class Download:
    
    def __init__(self, command, filename, download_type):
        self.command = command
        self.filename = filename
        self.download_type = download_type
        
        self.size = ""
        self.progress = "?"
        self.speed = "?" 
        self.est = "?"        
        
        self.__task = None
        self.__process = None
    
    def _clear(self):
        self.progress = ""
        self.est = ""
        self.speed = ""    
        
    def _download(self):   
        self.log = []
      
        if self.download_type == DownloadTypes.BASIC:
            self.__process = subprocess.Popen(self.command['wget'], stderr=subprocess.PIPE)
            while self.__process.poll() == None:
                line = self.__process.stderr.readline().strip()
                        
                if line:
                    if not self.size:
                        result = re.findall(': ([0-9]*) \(', line)
                        if result:
                            self.size = result[0]                            
                    
                    if "%" in line:                                                
                        result = re.findall('([0-9]{1,3}%) (.*)[ =](.*)', line)

                        if result:
                            self.progress = result[0][0]
                            self.speed = result[0][1]
                            if self.progress == "100%":
                                yield "Download.....100%"
                                self.est = "Fertig."
                            else:
                                self.est = result[0][2]
                   
                    else:        
                        yield line    
                                    
                    self.update_view()
                    
                time.sleep(1)
            
            yield self.__process.stderr.read().strip()
            
        elif self.download_type in [DownloadTypes.OTR_DECODE, DownloadTypes.OTR_CUT]:
            self.__process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            line = ''
            while self.__process.poll()==None:
                char = self.__process.stdout.read(1)
                
                if char=='\r' or char=='\n':
                    line = line.strip()
                    if not line:
                        continue
                        
                    if not "%" in line:
                        yield line
                    
                    result = re.findall("[0-9]{1,3}%", line)
                    if result:
                        self.progress = result[0]
                        if self.progress == "100%":
                            yield "Download.....100%"
                            self.est = "Fertig."
                        
                    result = re.findall("[0-9]{1,3}%.*: (.*)", line)
                    if result:
                        self.speed = result[0]
                    
                    self.update_view()
                    
                    line = ''
                else:
                    line += char
                    
            stderr = self.__process.stderr.read()
            for err in stderr.split('\n'):
                yield err.strip()
                
    def start(self):    
        def loop(*args):
            self.log.append(args[0])
        
        def completed():
            self.__task = None
    
        if not self.__task:
            self.__task = GeneratorTask(self._download, loop, completed)
            self.__task.start()
        
    def stop(self):
        print "[Downloader] Stop download of ", self.filename
    
        self._clear()
        self.update_view()        
    
        if self.__process:
            print "[Downloader] ... kill ", self.filename
            self.__process.kill()
    
        if self.__task:
            self.__task.stop()
            self.__task = None
