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
# Under CC BY-NC-ND 4.0 licence 
# https://creativecommons.org/licenses/by-nc/4.0/deed.en

from typing import Any

class IClient:
    """
    Interface methods to interact with a distant server whatever the procotol used
    """
    def connect(self):
        """
        Connect to the server
        """
        ...
    def disconnect(self):
        """
        Disconnect from the server
        """
        ...
    def isConnected(self):
        """
        :return:    Returns True if connected to server, False otherwise
        :rtype:     bool 
        """
        ...
    def read(self, whereToRead:str|None=None, payloadAsString=True):
        """
        Send/write specified data
        :param      whatToWrite:    A string to be sent
        :type       whatToWrite:    str
        :param      whereToRead:    The topic to read. If none, read every topics
        :type       whereToRead:    str
        :param      payloadAsString:True to decode payload bytes into string. False to keep payload as bytes
        :type       payloadAsString:bool
        :return:    A tuple containing the topic read followed by the data. Returns (None, None) if nothing read
        :rtype:     tuple(str, str)
        """
        ...
    def write(self, whatToWrite:str|dict[Any], whereToWrite:str):
        """
        Send/write specified data
        :param      whatToWrite:    A string to be sent
        :type       whatToWrite:    str
        :param      whereToWrite:   The topic where to send to data
        :type       whereToWrite:   str
        :return:    The number of characters written/send. 0 if nothing happened
        :rtype:     int
        """
        ...
