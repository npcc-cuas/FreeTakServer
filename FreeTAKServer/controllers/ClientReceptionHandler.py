#######################################################
# 
# ClientReceptionHandler.py
# Python implementation of the Class ClientReceptionHandler
# Generated by Enterprise Architect
# Created on:      19-May-2020 7:17:21 PM
# Original author: Natha Paquette
# 
#######################################################
import time
from xml.dom.minidom import parseString
import threading
from queue import Queue
from logging.handlers import RotatingFileHandler
import logging
import sys

from constants.ClientReceptionLoggingConstants import ClientReceptionLoggingConstants
loggingConstants = ClientReceptionLoggingConstants()
#TODO: add more rigid exception management

def newHandler(filename, log_level, log_format):
    handler = RotatingFileHandler(
        filename,
        maxBytes=loggingConstants.MAXFILESIZE,
        backupCount=loggingConstants.BACKUPCOUNT
    )
    handler.setFormatter(log_format)
    handler.setLevel(log_level)
    return handler


log_format = logging.Formatter(loggingConstants.LOGFORMAT)
logger = logging.getLogger(loggingConstants.LOGNAME)
logger.setLevel(logging.DEBUG)
logger.addHandler(newHandler(loggingConstants.DEBUGLOG, logging.DEBUG, log_format))
logger.addHandler(newHandler(loggingConstants.WARNINGLOG, logging.WARNING, log_format))
logger.addHandler(newHandler(loggingConstants.INFOLOG, logging.INFO, log_format))
console = logging.StreamHandler(sys.stdout)
console.setFormatter(log_format)
console.setLevel(logging.DEBUG)
logger.addHandler(console)

class ClientReceptionHandler:
    def __init__(self):
        self.dataPipe = ''
        self.eventPipe = ''
        self.threadDict = {}
        self.dataArray = []

    def startup(self, dataPipe, eventPipe):
        try:
            self.dataPipe = dataPipe
            self.eventPipe = eventPipe
            threading.Thread(target=self.monitorEventPipe, args=(), daemon=True).start()
            threading.Thread(target=self.returnDataToOrchestrator, args=(), daemon=True).start()
            logger.propagate = False
            logger.info("client reception handler has finished startup")
            logger.propagate = True
            while True:
                time.sleep(1000)
        except Exception as e:
            logger.error('there has been an error in client reception startup'+str(e))

    def monitorEventPipe(self):
        while True:
            try:
                while self.eventPipe.poll():
                    command = self.eventPipe.recv()
                    if command[0] == "create":
                        self.createClientMonitor(command[1])
                    elif command[0] == "destroy":
                        self.destroyClientMonitor(command[1])
            except Exception as e:
                logger.error('there has been an error in a client reception Event Pipe'+str(e))

    def returnDataToOrchestrator(self):
        while True:
            try:
                while len(self.dataArray)>0:
                    value = self.dataArray.pop(0)
                    self.dataPipe.send(value)
            except Exception as e:
                logger.error('there has been an error in client reception returning data to the orchestrator'+str(e))

    def createClientMonitor(self, clientInformation):
        try:
            alive = threading.Event()
            alive.set()
            clientMonitorThread = threading.Thread(target=self.monitorForData, args = (clientInformation, alive), daemon=True)
            clientMonitorThread.start()
            self.threadDict[clientInformation.ID] = [clientMonitorThread, alive]
            logger.info('client reception handler thread has finished being created')
        except Exception as e:
            logger.error('there has been an error in client reception with the creation of a client monitor'+str(e))

    def destroyClientMonitor(self, clientInformation):
        try:

            thread = self.threadDict.pop(clientInformation.clientInformation.ID)
            logger.info(thread)
            thread[1].clear()
            thread[0].join()
            logger.info('client reception handler thread has finished being terminated')
        except Exception as e:
            logger.error('there has been an error in client reception with the destruction of a clients thread '+str(e))

    def monitorForData(self, clientInformation, alive):
        '''
        updated receive all 
        '''
        try:
            try:                
                BUFF_SIZE = 8087
                client = clientInformation.socket
                data = b''
            except Exception as e:
                logger.error('there has been an error in a clients reception thread section A '+str(e))
                self.returnReceivedData(clientInformation, b'')
            while alive.isSet():
                try:
                    part = client.recv(BUFF_SIZE)
                except OSError as e:
                    logger.error('there has been an error in a clients reception thread section B '+str(e))
                    self.returnReceivedData(clientInformation, b'')
                    break
                try:
                    if part == b'' or part == None:
                        self.returnReceivedData(clientInformation, b'')
                        break
                    elif len(part) < BUFF_SIZE:
                        # either 0 or end of data
                        data += part 
                        self.returnReceivedData(clientInformation, data)
                        data = b''
                    else:
                        data += part
                except Exception as e:
                    logger.error('there has been an error in a clients reception thread section C '+str(e))
                    self.returnReceivedData(clientInformation, b'')
                    break
            return 1
        except Exception as e:
            logger.error('there has been an error in a clients reception thread section D '+str(e))
            self.returnReceivedData(clientInformation, b'')

    def returnReceivedData(self, clientInformation, data):
        try:
            from model.RawCoT import RawCoT
            RawCoT = RawCoT()
            #print(data)
            RawCoT.clientInformation = clientInformation
            RawCoT.xmlString = data
            self.dataArray.append(RawCoT)

        except Exception as e:
            logger.error('there has been an error in a clients reception thread with the returning of received data '+str(e))