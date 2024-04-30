# -*- coding: utf-8 -*-
#                           ██╗██████╗ ██╗           
#                           ██║╚════██╗██║           
#                           ██║ █████╔╝██║           
#                      ██   ██║██╔═══╝ ██║           
#                      ╚█████╔╝███████╗███████╗      
#                       ╚════╝ ╚══════╝╚══════╝      
#                       https://jusdeliens.com
#
# Designed with 💖 by Jusdeliens
# Under CC BY-NC-ND 3.0 licence 
# https://creativecommons.org/licenses/by-nc-nd/3.0/ 

import paho.mqtt.client as mqtt

import json
import random
import time
import pyanalytx.logger as anx
import sys
import traceback

from typing import Any,Callable
from getpass import getpass
from threading import Lock
from client import IClient

def _onMqttConnect(client, idealClient:"IdealMqttClient", flags, rc):
    idealClient._onConnect()

def _onMqttDisconnect(client, idealClient:"IdealMqttClient", rc):
    idealClient._onDisconnect()

def _onMqttSubscribe(client, idealClient:"IdealMqttClient", mid, granted_qos):
    idealClient._onSubscribe(mid)

def _onMqttUnsubscribe(client, idealClient:"IdealMqttClient", mid):
    idealClient._onUnsubscribe(mid)

def _onMqttMessage(client, idealClient:"IdealMqttClient", msg):
    idealClient._onMessage(msg)

class IdealMqttClient(IClient):
    def __init__(self, serverAddress:str|None=None, serverPort:int|None=None, topics:tuple[str]=(), username:str|None=None, userpassword:str|None=None, clientId:str|None=None, logger:anx.ILogger|None=None, onConnectionChangedCallback:Callable[[bool],None]|None=None):
        """
        Build a IClient using mqtt protocol
        :param      serverAddress:              The ip or the domaine name to join the server
        :type       serverAddress:              str
        :param      serverPort:                 The port number listening for websocket on the server to be sent
        :type       serverPort:                 int
        :param      username:                   The name credential to login. "" to log as anonymous. None to prompt
        :type       username:                   str or None
        :param      userpassword:               The password credential to login. "" to log as anonymous. None to prompt
        :type       userpassword:               str or None
        :param      topics:                     An array of string, each string is a mqtt topic to subscribe
        :type       topics:                     tuple(str)
        :param      onConnectionChangedCallback:A callback to be called each time the client connects/disconnects to/from the broker
        """
        if type(serverAddress) is not str:
            serverAddress = input("🌐 broker url (default: mqtt.jusdeliens.com): ")
        if len(serverAddress) == 0:
            serverAddress = "mqtt.jusdeliens.com"
        if type(serverPort) is not int:
            serverPort = input("📫 broker port (default: 1883): ")
            if len(serverPort) == 0:
                serverPort = 1883
            serverPort = int(serverPort)
        if type(username) is not str:
            username = input("👤 broker username (default: demo): ")
            if len(username) == 0:
                username = "demo"
        if len(username) == 0:
            username = None
        if type(userpassword) is not str:
            print("🔑 broker password: ")
            userpassword = getpass("> ")
        if len(userpassword) == 0:
            userpassword = None
        if ( clientId == None ):
            clientId = "PyIdealMqttClient"+str(random.randint(0,999999))
        self.__id = clientId
        self.__bufferCapacity = 1000
        self.__buffer = []
        self.__isConnectedToBroker = False
        self.__onConnectionChangedCallback = onConnectionChangedCallback
        self.__isLoopStarted = False
        self.__serverUrl = serverAddress
        self.__serverPort = serverPort
        self.__username = username
        self.__password = userpassword
        self.__topics = topics
        self.__readMutex = Lock()
        self.__qos = 0
        self.__logger = logger
        anx.info("⌛ Creating mqtt instance with client id "+self.__id, self.__logger)
        self.__client = None
        try:
            self.__client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1, client_id = self.__id, userdata=self)
        except Exception as e:
            self.__client = mqtt.Client(client_id = self.__id, userdata=self)
        self.__client.on_connect = _onMqttConnect
        self.__client.on_disconnect = _onMqttDisconnect
        self.__client.on_subscribe = _onMqttSubscribe
        self.__client.on_unsubscribe = _onMqttUnsubscribe
        self.__client.on_message = _onMqttMessage

    def _onConnect(self):
        anx.info("🟢 "+str(self.__id)+" connected to "+self.__serverUrl+":"+str(self.__serverPort), self.__logger)
        self.__isConnectedToBroker = True
        for topic in self.__topics:
            anx.info("⏳ Subscribing "+str(self.__id)+" to topic "+str(topic)+" ...", self.__logger)
            self.__client.subscribe(topic)
        if self.__onConnectionChangedCallback != None:
            self.__onConnectionChangedCallback(True)

    def _onDisconnect(self):
        anx.info("🔴 "+str(self.__id)+" disconnected from "+self.__serverUrl+":"+str(self.__serverPort), self.__logger)
        self.__isConnectedToBroker = False
        if self.__onConnectionChangedCallback != None:
            self.__onConnectionChangedCallback(False)

    def _onSubscribe(self, topic):
        anx.info("🔔  "+str(self.__id)+" subscribed to topic "+str(topic), self.__logger)

    def _onUnsubscribe(self, topic):
        anx.info("🔔  "+str(self.__id)+" unubscribed from topic "+str(topic), self.__logger)

    def _onMessage(self, msg):
        self.__readMutex.acquire()
        try:
            self.__buffer.append(msg) # TODO : make a deep copy ? 
            # self.__buffer.append(copy.deepcopy(self.msg))
            if ( len(self.__buffer) >= self.__bufferCapacity ):
                self.__buffer.pop(0)
        finally:
            self.__readMutex.release()

    def isConnected(self):
        return self.__isConnectedToBroker
    
    def connect(self):
        if self.__isLoopStarted and self.__isConnectedToBroker:
            anx.warning("⚠️ Fail to connect "+str(self.__id)+" since already connected", self.__logger)
            return False
        if ( self.__username != None and self.__password != None ):
            anx.info("🔑 Setting username "+self.__username +" and password for "+str(self.__id), self.__logger)
            self.__client.username_pw_set(self.__username, self.__password)
        try:
            if ( self.__isConnectedToBroker == False ):
                anx.info("⏳ Connecting "+str(self.__id)+" to broker "+self.__serverUrl+":"+str(self.__serverPort)+"...", self.__logger)
                self.__client._connect_timeout = 5.0
                rc=self.__client.connect(self.__serverUrl, self.__serverPort)
            if ( self.__isLoopStarted == False ):
                anx.info("⏳ Starting mqtt thread loop ...", self.__logger)
                self.__client.loop_start()
                time.sleep(2)
                anx.info("🟢 Started mqtt loop", self.__logger)
                self.__isLoopStarted = True
            return rc == 0
        except Exception as e:
            anx.error("⚠️ FAIL connecting "+str(self.__id)+" to broker "+self.__serverUrl+":"+str(self.__serverPort)+": "+str(e), self.__logger)
            return False
        
    def disconnect(self):
        ret = False
        if self.__isLoopStarted:
            anx.info("⌛ Stopping "+str(self.__id)+" mqtt thread loop ...", self.__logger)
            try:
                try: self.__client.loop_stop(force=True)
                except:  self.__client.loop_stop()
            except Exception as e:
                anx.info("⚠️ Fail to stop "+str(self.__id)+". Error: "+str(sys.exc_info()[0]), self.__logger)
                return False
            anx.info("🔴 Stopped "+str(self.__id)+" mqtt thread loop", self.__logger)
            self.__isLoopStarted = False
            ret = True

        if self.__isConnectedToBroker:
            anx.info("⌛ Disconnecting "+str(self.__id)+" from "+self.__serverUrl+":"+str(self.__serverPort)+". Waiting disconnection confirmation from thread ...", self.__logger)
            try:
                self.__client.disconnect()
            except Exception as e:
                anx.info("⚠️ Fail to disconnect "+str(self.__id)+". Error: "+str(sys.exc_info()[0]), self.__logger)
                return False
            ret = ret and True
        return ret
        
    def read(self, whereToRead:str|None=None, payloadAsString=True):
        whatWasRead = None
        self.__readMutex.acquire()
        try:
            sizeBuffer = len(self.__buffer)
            anx.debug(str(sizeBuffer)+" msg awaiting in "+str(self.__id)+" read buffer", self.__logger)
            if ( sizeBuffer > 0 ):
                msg = self.__buffer.pop(0)
                topic = msg.topic
                payload = msg.payload
                anx.debug("📩 Pop msg from topic "+str(topic), self.__logger)
                if payloadAsString:
                    payload = ""
                    try:
                        payload = msg.payload.decode()
                    except Exception as e:
                        anx.warning("⚠️ FAIL parsing msg "+str(e)+": "+str(msg.payload), self.__logger)
                        anx.warning(traceback.format_exc(), self.__logger)
                    if ( payload != "" ):
                        try:
                            anx.debug("🔍 Parsing json str payload", self.__logger)
                            payloadParsed = json.loads(payload)
                            if ( len(payloadParsed) != 0 ):
                                anx.debug("📦 Parsed "+str(len(payloadParsed))+" elements", self.__logger)
                                if ( 'topic' in payloadParsed and 'payload' in payloadParsed and (whereToRead == payloadParsed['topic'] or whereToRead==None)):
                                    whatWasRead = (payloadParsed['topic'], payloadParsed['payload'])
                                else:
                                    whatWasRead = (topic, payloadParsed)
                            else:
                                anx.debug("📦 Parsed 0 elements in json payload", self.__logger)
                                whatWasRead = (topic, payload)
                        except:
                            anx.debug("⚠️ Fail parsing json payload. Error: "+str(sys.exc_info()[0]), self.__logger)
                            whatWasRead = (topic, payload)
                else:
                    whatWasRead = (topic, payload)
        finally:
            self.__readMutex.release()
            if ( whatWasRead == None ):
                return (None, None)
            else:
                return whatWasRead
            
    def write(self, whatToWrite:str|dict[Any]|bytes, whereToWrite:str):
        try:
            anx.debug("📡 Tx "+str(self.__id)+" msg typed "+str(type(whatToWrite))+" of len "+str(len(whatToWrite)), self.__logger)
            if ( type(whatToWrite) is str ):
                info = self.__client.publish(whereToWrite, whatToWrite, self.__qos)
                return len(whatToWrite)*int(info.is_published())
            elif ( type(whatToWrite) is dict ):
                msg = json.dumps(whatToWrite)
                info = self.__client.publish(whereToWrite, msg, self.__qos)
                return len(msg)*int(info.is_published())
            else:
                info = self.__client.publish(whereToWrite, whatToWrite, self.__qos)
                return len(whatToWrite)*int(info.is_published())
        except:
            anx.error("⚠️ Fail to write. Error: "+str(sys.exc_info()[0]), self.__logger)
            return 0
