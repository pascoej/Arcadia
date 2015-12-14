from util import *
from entity import *
from mapdata import *
from packets import *
from scheduler import *
from ai import *
import time
from spatial import *
import os

class Game(object):
    def __init__(self):
        self.tps = 20
        self.players = []
        self.playersByClient = {}
        self.entityCount = 0
        self.clientCount = 0
        self.map = GameMap("./map")
        self.scheduler = Scheduler()
        self.entitiesById = {}
        self.entities = []
        self.tickDebt = 0
        self.spatial = Spartial(100)
        self.map.spawnBuildings(self)
        self.startTickLoop()
        self.startMinionLoop()
        self.lastTPS = self.tps
        self.isGameOver = False
        self.badTickTimeAmount = 0
    def minionCount(self):
        count = 0
        for entity in self.entities:
            if isinstance(entity,Minion):
                count = count + 1
        return count
    def updateSpatial(self):
        self.spatial.clear()
        for entity in self.entities:
            self.spatial.addEntity(entity)
    def startMinionLoop(self):
        timeBetweenWaves = 25
        self.scheduler.scheduleTimeTask(self.spawnMinionWave,
            timeBetweenWaves,True)
    def spawnMinionWave(self):
        if self.minionCount() >= 12 or self.isGameOver:
            return
        perLane = 2
        aiInfos = [self.map.aiInfos['red-minion'],
            self.map.aiInfos['blue-minion']]
        pathsAmount = len(aiInfos[0].paths)
        for minionAIInfo in aiInfos:
            for i in range(pathsAmount):
                for j in range(perLane):
                    ai = MinionAI(minionAIInfo,i)
                    entity = Minion(self,ai)
                    self.addEntity(entity)

    def spawnMinion(self):
        aiInfo = self.map.aiInfos['red-minion']
        ai = MinionAI(aiInfo,1)
        entity = Minion(self,ai)
        self.addEntity(entity)
    def connectPlayer(self,username,team,champ,sendMessageFunction):
        player = Champion.getNewChamp(self,champ,username,team,
            sendMessageFunction)
        self.players.append(player)
        clientId = self.newClientId()
        self.playersByClient[clientId] = player 
        self.onNewEntity(player)
        self.onPositionUpdate(player)
        self.sendAllentitiesById(player)
        spellsPacket = ListSpellsPacket(player)
        player.sendWSMessage(spellsPacket.getData())
        player.sendWSMessage(ChatPacket("Welcome to Arcadia").getData())
        return clientId
    def getEntityAtLocation(self, loc):
        for entity in self.entities:
            if (entity.getAABB().containsPoint(loc)):
                return entity
    def getEntityById(self, entityId):
        if entityId in self.entitiesById:
            return self.entitiesById[entityId]
        return None
    def sendAllentitiesById(self, toPlayer):
        for entity in self.entities:
            if entity != toPlayer:
                packet = NewEntityPacket(entity)
                toPlayer.sendWSMessage(packet.getData())
                packet = PositionUpdatePacket(entity.id, entity.position,force=True)
                toPlayer.sendWSMessage(packet.getData())
                if isinstance(entity,LivingEntity):
                    packet = HealthUpdatePacket(entity)
                    toPlayer.sendWSMessage(packet.getData())
    def onDisconnect(self,clientId):
        player = self.playersByClient[clientId]
        player.hasConnection = False
        self.scheduler.scheduleTimeTask(lambda: self.timeoutPlayer(clientId),10)
    def timeoutPlayer(self,clientId):
        player = self.playersByClient[clientId]#The player didn't reconnect
        if (player.hasConnection): #The player regained connection in time
            return True
        self.players.remove(player)
        del self.playersByClient[clientId]
        self.removeEntity(player)
        self.sendMessageToAll("%s has disconnected" % player.username)
    def sendMessageToAll(self,message):
        packet = ChatPacket(message)
        self.sendPacketToAll(packet)
    def removeEntity(self,entity):
        del self.entitiesById[entity.id]
        self.entities.remove(entity)
        packet = DestroyEntityPacket(entity)
        for player in self.players:
            player.sendWSMessage(packet.getData())

    def onMsg(self,clientId,message):
        self.playersByClient[clientId].handleWSMessage(message)
    def addEntity(self,entity):
        self.onNewEntity(entity)
        return entity.id
    def newEntityId(self, entity):
        self.entityCount += 1
        self.entitiesById[self.entityCount] = entity
        self.entities.append(entity)
        entity.id = self.entityCount
        return self.entityCount
    def newClientId(self):
        self.clientCount += 1
        return self.clientCount
    def sendPacketToAll(self, packet):
        for player in self.players:
            player.sendWSMessage(packet.getData())
    def onNewEntity(self,entity):
        self.sendPacketToAll(NewEntityPacket(entity))
        if isinstance(entity,LivingEntity):
            self.sendPacketToAll(HealthUpdatePacket(entity))
    def shutdown(self):
        os._exit(1)
    def win(self,team):
        if not self.isGameOver:
            self.isGameOver = True
            self.sendPacketToAll(BannerPacket("%s has won" % team))
            self.sendPacketToAll(ChatPacket("%s Won!!!!" % team))
            self.sendPacketToAll(
                ChatPacket("Server shutting down in 10 seconds"))   
            self.scheduler.scheduleTimeTask(self.shutdown,10)         
    #Possible performance problems, o(n^2), can be reduced to roughtly o(n)
    def collidesWithEntity(self,point):
        for entity in self.entities:
            if (entity.getAABB().containsPoint(point)):
                return True
        return False
    def checkCollisions(self):
        for (entity1,entity2) in self.spatial.getCollidingEntities():
            entity1.onCollide(entity2)
            entity2.onCollide(entity1)

    def onPositionUpdate(self, entity):
        packet = PositionUpdatePacket(entity.id, entity.position)
        for player in self.players:
            player.sendWSMessage(packet.getData())
    # Are we going to have terrible async problems later?
    # probably
    def recordTick(self):
        self.lastTick = time.time()
        if hasattr(self,'tickI'):
            self.tickI = self.tickI + 1
        else:
            self.tickI = 0
            self.last10Tick = time.time()
        if (self.tickI % 10 == 0):
            currentTime = time.time()
            lastTime = self.last10Tick
            elapsed = currentTime - lastTime
            try:
                ticksPerSecond = 10 / elapsed
                self.lastTPS = ticksPerSecond
                #print("tps",ticksPerSecond)
                if (ticksPerSecond < 17):
                    print("ticks really low: %f" % ticksPerSecond)
                if (ticksPerSecond < 5):
                    timeout = 5
                    self.badTickTimeAmount = self.badTickTimeAmount + 1
                    if (self.badTickTimeAmount > timeout):
                        #something is horribly wrong, restart the server.
                        self.shutdown()
            except:
                return
            self.last10Tick = currentTime
            #if (self.tickI > 100):
            #    #On some host servers, sleep is constantly slightly off
            #    #Second ajustment layer
            #    desiredTicksDiff = self.tps - ticksPerSecond
            #    virtualTPS = self.tps + desiredTicksDiff
            #    self.adjustedTickInterval = 1/virtualTPS
                #print("tps: %f" % ticksPerSecond)
    @run_async
    def startTickLoop(self):
        tps = self.tps
        self.adjustedTickInterval = 1/self.tps
        startTime = time.time()
        #hasStats = False
        while True:
            currentTime = time.time()
            nextTickPlanned = currentTime + self.adjustedTickInterval
            #yappi.start()
            self.tick()
            #if (time.time() - startTime > 100 and not hasStats):
                #yappi.get_func_stats().print_all()
                #hasStats = True
            afterTickTime = time.time()
            timeLeft = nextTickPlanned - afterTickTime
            if (self.tickDebt > 0):
                print(self.tickDebt,len(self.entities))
            if timeLeft < 0:
                self.tickDebt = self.tickDebt + abs(timeLeft)
            if (timeLeft > 0 and self.tickDebt > 0):
                toRemove = min(timeLeft,self.tickDebt)
                self.tickDebt = self.tickDebt - toRemove
                timeLeft = self.tickDebt - toRemove
            if (timeLeft > 0):
                time.sleep(timeLeft*.9)
    def tick(self):
        self.updateSpatial()
        self.scheduler.tick()
        self.checkCollisions()
        for entity in self.entities:
            entity.onTick()
        self.recordTick()

