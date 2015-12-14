from tornado import websocket, web, ioloop

from game import *
import packets
import packetsender
game = Game()
class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True
    def open(self):
        self.packetsender = packetsender.PacketSender()
        self.directSendFunction = lambda message: self.write_message(message)
        self.sendFunction = self.sendMessage
        self.sendFunction(packets.MapdataPacket(game.map).getData())
        self.open = True
    def sendMessage(self, message):
        if self.open:
            ioloop.IOLoop.instance().add_callback(self.directSendFunction,message)
    def on_message(self,message):
        if hasattr(self,'clientId'):
            game.onMsg(self.clientId,message)
        else:
            packet = packets.messageToPacket(message)
            if isinstance(packet,packets.ReconnectPacket):
                player = game.entitiesById[packet.entityId]
                player.sendMessageFunction = self.sendFunction
                player.hasConnection = True
            if isinstance(packet,packets.LoginPacket):
                username = packet.name
                champ = packet.champ
                team = packet.team
                self.clientId = game.connectPlayer(username,team,champ,self.sendFunction)
                print("connected client", self.clientId, username)
    def on_close(self):
        self.open = False
        if hasattr(self, 'clientId'):
            game.onDisconnect(self.clientId)


app = web.Application([(r'/', SocketHandler)])
if __name__ == "__main__":
    app.listen(8888) 
    ioloop.IOLoop.instance().start()