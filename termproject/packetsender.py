import queue
from util import *
class PacketSender(object):
    def __init__(self):
        self.packetQueue = queue.Queue()
        self.queueLoop()
    @run_async
    def queueLoop(self):
        while True:
            packetAndSender = self.packetQueue.get()  
            message = packetAndSender[0]
            sender = packetAndSender[1]
            try:
                sender(message)
            except:
                print("send packet failed")
    def add(self,message,sendFunction):
        packetAndSender = (message,sendFunction)
        self.packetQueue.put(packetAndSender)