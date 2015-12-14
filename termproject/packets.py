import json
from util import *
from entity import *
class Packet(object):
    def __init__(self,packetType):
        self.data = {}
        self.data['packetType'] = packetType
    def getData(self):
        return json.dumps(self.data)
class MapdataPacket(Packet):
    def __init__(self,mapdata):
        super().__init__('Mapdata')
        self.data['collision'] = mapdata.collision.numArray
class PositionUpdatePacket(Packet):
    def __init__(self,entityId,position, force=True):
        super().__init__('PositionUpdate')
        self.data['entityId'] = entityId
        self.data['positionX'] = str(position.x)
        self.data['positionY'] = str(position.y)
        if force:
            self.data['force'] = True
class NewEntityPacket(Packet):
    def __init__(self,entity):
        super().__init__('NewEntity')
        self.data['entityType'] = entity.getType()
        if entity.getType() == "player":
            self.data['champ'] = entity.champName
        if entity.getType() == "laser":
            start = entity.position.toTuple()
            end = entity.velocity.multiply(500).toTuple()
            self.data['start'] = start
            self.data['end'] = end
        self.data['entityId'] = entity.id
        self.data['team'] = entity.team
        if hasattr(entity,'username'):
            self.data['username'] = entity.username
class DestroyEntityPacket(Packet):
    def __init__(self,entity):
        super().__init__('DestroyEntity')
        self.data['entityId'] = entity.id
class HealthUpdatePacket(Packet):
    def __init__(self,entity):
        super().__init__('HealthUpdate')
        self.data['entityId'] = entity.id
        self.data['health'] = entity.health
        self.data['maxHealth'] = entity.maxHealth
class AttackPacket(Packet):
    def __init__(self, attacker, attacked):
        super().__init__('Attack')
        self.data['attackingId'] = attacker.id
        self.data['attackedId'] = attacked.id
class ChatPacket(Packet):
    def __init__(self, message):
        super().__init__('Chat')
        self.data['message'] = message
class BannerPacket(Packet):
    def __init__(self, message, style = None):
        super().__init__('Banner')
        self.data['message'] = message
        if style != None:
            self.style = style
class PathPacket(Packet):
    def __init__(self,entity):
        super().__init__('Path')
        path = entity.goal.path
        jsonPath = []
        for vector in path:
            jsonPath.append(vector.toDict())
        self.data['entityId'] = entity.id
        self.data['path'] = jsonPath
        self.data['speed'] = entity.speed * entity.game.tps #tick rate
class VelocityPacket(Packet):
    def __init__(self,entity):
        super().__init__('Velocity')
        self.data['velocity']=entity.velocity.multiply(entity.game.tps).toDict()
        self.data['velocityNorm'] = entity.velocity.normalize().toDict()
        self.data['speed'] = entity.velocity.magnitude() * entity.game.lastTPS
        self.data['entityId'] = entity.id
class ListSpellsPacket(Packet):
    def __init__(self,champ):
        super().__init__('ListSpells')
        spellNames = list(sorted(champ.spells.keys()))
        self.data['spells'] = spellNames

class RecvPacket(object):
    def fromJson(json):
        packet = None
        packetType = json['packetType']
        if (packetType == "SetTarget"):
            packet = SetTargetPacket(json)
        elif (packetType == "SetTargetEntity"):
            packet = SetTargetEntityPacket(json)
        elif (packetType == "Login"):
            packet = LoginPacket(json)
        elif (packetType == "ChatRecv"):
            packet = ChatRecvPacket(json)
        elif (packetType == "CastSpell"):
            packet = CastSpell(json)
        elif (packetType == "Reconnect"):
            packet = ReconnectPacket(json)
        return packet
class SetTargetPacket(RecvPacket):
    def __init__(self,json):
        self.x = json['x']
        self.y = json['y']
    def getTargetVector(self):
        return Vector(self.x,self.y)
class SetTargetEntityPacket(RecvPacket):
    def __init__(self,json):
        self.targetId = json['targetId']
class LoginPacket(RecvPacket):
    def __init__(self,json):
        self.name = json['username']
        self.champ = json['champ']
        self.team = json['team']
class ChatRecvPacket(RecvPacket):
    def __init__(self,json):
        self.message = json['message']
class ReconnectPacket(RecvPacket):
    def __init__(self,json):
        self.clientId = json['clientId']
class CastSpell(RecvPacket):
    def __init__(self,json):
        self.spell = json['spell']
        if "targetEntity" in json:
            self.targetEntityId = json['targetEntity']
        if "targetLocation" in json:
            self.targetLocation = Vector.fromString(json['targetLocation'])

def messageToPacket(message):
    rawJson = json.loads(message)
    packet = RecvPacket.fromJson(rawJson)
    return packet