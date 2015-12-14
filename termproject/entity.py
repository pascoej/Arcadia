from util import *
import packets
import time
from ai import *
import json
class Entity(object):
    def __init__(self,game):
        self.game = game
        self.id = self.game.newEntityId(self)
        self.position = Vector() 
        self.velocity = Vector()
        self.immoveable = False
        self.valid = True
        self.speed = 1
        self.goal = None
        self.lastVelocity = Vector()
        self.collidable = True
    def sendVelocityUpdate(self):
        self.game.sendPacketToAll(packets.VelocityPacket(self))
    def entitiesWithinDistance(self, dist):
        return self.game.spatial.getEntitiesInRange(self.position,dist)
    def onTick(self):
        if (self.goal != None):
            self.goal.updateNext(self.position)
            if (self.goal.isAtGoal(self.position)):
                self.goal = None
                self.velocity = Vector()
            else:
                if (self.position.distanceSquared(self.goal.nextLoc(self.position)) > self.speed**2):
                    self.velocity = self.goal.directionOfGoal(self.position).multiply(self.speed)
                else:
                    self.velocity = self.goal.nextLoc(self.position).minus(self.position)
        if self.immoveable:
            self.velocity = Vector()
        if (self.velocity.distanceSquared(self.lastVelocity) > 10**-3):
            self.sendVelocityUpdate()
        self.lastVelocity = self.velocity
        if not self.immoveable and not self.velocity.isZero():
            newPos = self.position.add(self.velocity)
            self.position = newPos
            
            self.velocity = self.velocity.multiply(.5)
            self.game.onPositionUpdate(self)
            self.lastCollidingEntity = None
    def getType(self):
        return "entity"
    def getAABB(self):
        return AABB(self.position.add(Vector(-12,-12)),self.position.add(Vector(12,12)))
    def getCenter(self):
        return self.getAABB().center()
    def onCollide(self, otherEntity):
        self.lastCollidingEntity = otherEntity
        if (self.collidable and otherEntity.collidable
            and not self.immoveable and 
            self.getAABB().collides(otherEntity.getAABB()) 
            and self.goal != None):
            mtd = self.getAABB().minTranslation(otherEntity.getAABB())
            self.velocity = mtd.multiply(1.2)
            self.goal = None

    def destroy(self):
        if not self.valid:
            return
        self.valid = False
        self.game.removeEntity(self)
    def sendStatePackets(self):
        healthUpdatePacket = packets.HealthUpdatePacket(self)
        self.game.sendPacketToAll(healthUpdatePacket)
        self.game.onPositionUpdate(self)
class LightBeam(Entity):
    speed = 50

    def __init__(self,game):
        super().__init__(game)
        self.collidable = False
    def setDirection(self, vector):
        self.velocity = vector.normalize().multiply(LightBeam.speed)
        if (self.velocity.isZero()):
            return
        self.colliding = self.allInPath()
    def allInPath(self):
        width = 25
        pos = self.position
        collides = set()
        while (self.game.map.isInBounds(pos)):
            pos = pos.add(self.velocity)
            colliding = self.game.spatial.getEntitiesInRange(pos,width)
            collides = collides.union(colliding)
        return collides
    def getType(self):
        return "laser"
    def onTick(self):
        damage = 1
        for entity in self.colliding:
            if (isinstance(entity,LivingEntity) and entity.team != self.team):
                entity.damage(damage,self)

        
    def onCollide(self, otherEntity):
        pass
        
class LivingEntity(Entity):
    def __init__(self,game,maxHealth,team):
        super().__init__(game)
        self.maxHealth = maxHealth
        self.health = maxHealth
        self.team = team
    def damage(self, amount, damager):
        self.health -= amount
        self.lastDamager = damager
        if (amount != 0):
            healthUpdatePacket = packets.HealthUpdatePacket(self)
            self.game.sendPacketToAll(healthUpdatePacket)
        if (self.health < 0):
            self.onDeath()
    def isFriendly(self, otherEntity):
        return otherEntity.team == self.team
    def isValidTarget(self, otherEntity):
        return True
        #return not self.isFriendly(otherEntity)
    def heal(self, amount):
        self.health = min(self.maxHealth, self.health + amount)
        if (amount != 0):
            healthUpdatePacket = packets.HealthUpdatePacket(self)
            self.game.sendPacketToAll(healthUpdatePacket)
    def onDeath(self):
        self.destroy()
class Building(LivingEntity):
    def __init__(self,game,maxHealth,team):
        super().__init__(game,maxHealth,team)
        self.immoveable = True
    def getNewBuilding(game,team,buildingType):
        if (buildingType == "endbuilding"):
            return EndBuilding(game,team)
class EndBuilding(Building):
    maxHealth = 1000
    def __init__(self,game,team):
        super().__init__(game,EndBuilding.maxHealth,team)
    def getAABB(self):
        return AABB(self.position.add(Vector(-50,-45)),self.position.add(Vector(50,45)))
    def getType(self):
        return "endbuilding"
    def onDeath(self):
        super().onDeath()
        winningTeam = self.lastDamager.team
        self.game.win(winningTeam)
class Monster(LivingEntity):
    def __init__(self,game,maxHealth,team,attackRange):
        super().__init__(game,maxHealth,team)
        self.target = None
        self.attackRange = attackRange

    def entitiesWithinAttackRange(self):
        epsilon = 10**-3
        return self.entitiesWithinDistance(self.attackRange-epsilon)
    def isValidTarget(self,other,checkDistance=True):
        if not super().isValidTarget(other):
            return False
        if (checkDistance and self.position.distanceSquared(other.position)
            > self.attackRange**2):
            return False
        return True
    def getTarget(self):
        return self.target
    def setTarget(self, target):
        self.target = target
    def onCollide(self, otherEntity):
        pass
class Minion(Monster):
    maxHealth = 120
    attackRange = 195
    attackDamage = 20
    attackSpeed = 2.5
    def __init__(self,game,ai):
        super().__init__(game,Minion.maxHealth,None,Minion.attackRange) # team defined when by ai
        self.ai = ai
        ai.setEntity(self)
        self.lastAttack = time.time()
        self.speed = 4
    def getType(self):
        return "minion"
    def onTick(self):
        self.ai.onTick()
        super().onTick()
    def timeSinceLastAttack(self):
        currentTime = time.time()
        elapsed = currentTime - self.lastAttack
        return elapsed
    def onDeath(self):
        super().onDeath()
        self.game.spawnMinion()
    def attack(self):
        if self.timeSinceLastAttack() < Minion.attackSpeed:
            return
        if (self.target == None or self.target == self):
            return
        if not isinstance(self.target,LivingEntity):
            return
        if not self.target.valid:
            self.target = None
            return 
        if not self.isValidTarget(self.target):
            return

        self.target.damage(Minion.attackDamage,self)
        #attackPacket = packets.AttackPacket(self,self.target)
        #self.game.sendPacketToAll(attackPacket)
        self.lastAttack = time.time()

class Goal(object):
    epsilon = 10**-2
    def __init__(self,game,goalLocation):
        self.game = game
        self.goalLocation = goalLocation
        self.valid = True
    def calculatePath(self,currentLocation):
        findPathAndSet(self,currentLocation)
    def nextLoc(self,currentLocation):
        if not hasattr(self,'path' or not self.valid):
            return self.goalLocation
        elif self.pathI >= len(self.path):
            return self.goalLocation
        elif self.path == None:
            return self.goalLocation
        return self.path[self.pathI]
    def directionOfGoal(self, fromLocation):
        goalLocation = self.nextLoc(fromLocation)
        directionVector = goalLocation.minus(fromLocation).normalize()
        return directionVector
    def updateNext(self, curLocation):
        if hasattr(self,'pathI') and curLocation.distanceSquared(self.nextLoc(curLocation)) < Goal.epsilon:
            self.pathI = self.pathI + 1
    def isAtGoal(self, location):
        if (not self.valid):
            return True
        return (location.distanceSquared(self.goalLocation) < Goal.epsilon)

class Player(LivingEntity):
    def __init__(self,game,maxHealth,team,sendMessageFunction,moveSpeed):
        super().__init__(game,maxHealth,team)
        self.speed = moveSpeed
        self.sendMessageFunction = sendMessageFunction
        self.goal = None
        self.target = None
        self.username = "noname"
        self.hasConnection = True
        self.recordingPath = False
        self.recordedPath = []
    def sendWSMessage(self,message):
        self.sendMessageFunction(message)
    def isStopVector(self,loc):
        return loc == Vector(-1,-1)
    def sendMessage(self,message):
        chat = packets.ChatPacket(message)
        self.sendWSMessage(chat.getData())
    def sendBanner(self,message,style=None):
        banner = packets.BannerPacket(message,style)
        self.sendWSMessage(banner.getData())
    def handleWSMessage(self,message):
        packet = packets.messageToPacket(message)
        if isinstance(packet,packets.SetTargetPacket):
            if self.isStopVector(packet.getTargetVector()):
                self.goal = None
                self.velocity = Vector()
                return
            goalVector = packet.getTargetVector()
            self.goal = Goal(self.game,goalVector)
            self.goal.calculatePath(self.position)
            if (self.recordingPath):
                locTuple = goalVector.toTuple()
                self.recordedPath.append(locTuple)
        elif isinstance(packet,packets.SetTargetEntityPacket):
            targetId = packet.targetId
            targetEntity = self.game.getEntityById(targetId)
            if targetEntity != None:
                self.target = targetEntity
        elif isinstance(packet,packets.ChatRecvPacket):
            message = packet.message
            if (message == "recordpath"):
                self.recordingPath = not self.recordingPath
            if (message == "printpath"):
                jsonString = json.dumps(self.recordedPath)
                print(jsonString)
            message = "%s: %s" % (self.username,message)
            self.game.sendPacketToAll(packets.ChatPacket(message))

    def getType(self):
        return "player"

    def onTick(self):
        super().onTick()
class Champion(Player):
    def __init__(self, game, maxHealth,team, sendMessageFunction, moveSpeed, 
        meleeAttackStrength, mana, magicResistence, attackSpeed, meleeAttackRange):
        super().__init__(game,maxHealth,team,sendMessageFunction,moveSpeed)
        self.meleeAttackStrength = meleeAttackStrength
        self.mana = mana
        self.magicResistence = magicResistence
        self.attackSpeed = attackSpeed
        self.meleeAttackRange = meleeAttackRange

        self.lastMeleeAttackTime = time.time()
        self.spellTimeouts = {}
        self.spells = {}
        self.respawn()
    def respawn(self):
        self.health = self.maxHealth
        self.velocity = Vector()
        self.goal = None
        self.position = self.game.map.spawns[self.team]
        self.sendStatePackets()
    def handleWSMessage(self,message):
        super().handleWSMessage(message)
        packet = packets.messageToPacket(message)
        if isinstance(packet,packets.CastSpell):
            self.performSpell(packet.spell,packet)

    def getSpellCooldownTime(self,name):
        return 10 #10 sec
    def performSpell(self, name,spellPacket):
        if name not in self.spells:
            return
        target = None
        if (hasattr(spellPacket,'targetEntityId')):
            target = self.game.entitiesById[spellPacket.targetEntityId]
        elif (hasattr(spellPacket,'targetLocation')):
            target = spellPacket.targetLocation
        currentTime = time.time()
        if name in self.spellTimeouts:
            timeoutTime = self.spellTimeouts[name]
            if timeoutTime > currentTime:
                return
            else:
                del spellTimeouts[name]
        self.spells[name](target)

    def timeSinceLastMeleeAttack(self):
        currentTime = time.time()
        elapsed = currentTime - self.lastMeleeAttackTime
        return elapsed
    def isValidTarget(self, target):
        if not super().isValidTarget(target):
            return False
        return (self.getCenter().distanceSquared(target.getCenter()) < 
            self.meleeAttackRange**2)
    def onTick(self):
        super().onTick()
        self.meleeAttack()
    def meleeAttack(self):
        if self.timeSinceLastMeleeAttack() < self.attackSpeed:
            return
        if (self.target == None or self.target == self):
            return
        if not self.target.valid:
            self.target = None
            return 
        if not self.isValidTarget(self.target):
            return
        if self.isFriendly(self.target):
            return
        self.target.damage(self.meleeAttackStrength,self)
        attackPacket = packets.AttackPacket(self,self.target)
        self.game.sendPacketToAll(attackPacket)
        self.lastMeleeAttackTime = time.time()
        return self.meleeAttackStrength
    def getNewChamp(game,champName,username,team,sendMessageFunction):
        champ = None
        if champName == "ghost":
            champ = GhostChamp(game,team,sendMessageFunction)
        elif champName == "angel":
            champ = AngelChamp(game,team,sendMessageFunction)
        elif champName == "firebro":
            champ = FirebroChamp(game,team,sendMessageFunction)
        else:
            champ = TestChamp(game,team,sendMessageFunction)
        champ.champName = champName
        champ.username = username
        return champ
    def onDeath(self):
        banner = None
        if (isinstance(self.lastDamager,Champion)):
            killerUsername = self.lastDamager.username
            banner = packets.BannerPacket("%s has slain %s" % (killerUsername, self.username))
        else:
            banner = packets.BannerPacket("%s has been slain" % self.username)
        self.game.sendPacketToAll(banner)

        self.respawn()
    def blink(self, targetLocation):
        if (not isinstance(targetLocation,Vector)):
            return
        if (self.game.map.isCollision(targetLocation)):
            return False
        self.position = targetLocation
        self.goal = None
        self.velocity = Vector()
        self.game.onPositionUpdate(self)
        self.sendBanner("Blink!")
class TestChamp(Champion):
    maxHealth = 50
    moveSpeed = 4
    meleeAttackStrength = 3
    mana = 50
    magicResistence = 5
    attackSpeed = 2
    meleeAttackRange = 60
    def __init__(self,game,team,sendMessageFunction):
        super().__init__(game,TestChamp.maxHealth,team,sendMessageFunction,
            TestChamp.moveSpeed, TestChamp.meleeAttackStrength, TestChamp.mana,
            TestChamp.magicResistence, TestChamp.attackSpeed,
             TestChamp.meleeAttackRange)
class GhostChamp(Champion):
    maxHealth = 250
    moveSpeed = 8
    meleeAttackStrength = 15
    mana = 50
    magicResistence = 5
    attackSpeed = .14
    meleeAttackRange = 120
    stealFraction = .2
    paralyzeTime = 5
    def __init__(self,game,team,sendMessageFunction):
        super().__init__(game,GhostChamp.maxHealth,team,sendMessageFunction,
            GhostChamp.moveSpeed, GhostChamp.meleeAttackStrength, GhostChamp.mana,
            GhostChamp.magicResistence, GhostChamp.attackSpeed,
             GhostChamp.meleeAttackRange)
        self.stealFraction = GhostChamp.stealFraction
        self.paralyzeTime = GhostChamp.paralyzeTime
        self.spells['blink'] = self.blink
        self.spells['paralyze'] = self.paralyze
        self.champName = "ghost"
    def meleeAttack(self):
        damageDealt = super().meleeAttack()
        if (damageDealt == None):
            return
        toHeal = damageDealt * self.stealFraction
        self.heal(toHeal)
    def paralyze(self,target):
        if isinstance(target,Vector):
            target = self.game.getEntityAtLocation(target)
        if hasattr(target,'paralyzed'):
            return
        if not hasattr(target,'speed'):
            return
        origSpeed = target.speed
        target.speed = 0
        target.paralyze = True
        if (isinstance(target,Player)):
            target.sendBanner("You got paralyzed!!")
        def unParalyze():
            target.speed = origSpeed
            if (isinstance(target,Player)):
                target.sendBanner("You got paralyzed!!")
            if hasattr(target,'paralyzed'):
                del target.paralyzed
        self.game.scheduler.scheduleTimeTask(unParalyze,self.paralyzeTime)
class FirebroChamp(Champion):
    maxHealth = 250
    moveSpeed = 8
    meleeAttackStrength = 15
    mana = 50
    magicResistence = 5
    attackSpeed = .14
    meleeAttackRange = 120
    stormRange = 90
    stormDamage = 50
    def __init__(self,game,team,sendMessageFunction):
        super().__init__(game,FirebroChamp.maxHealth,team,sendMessageFunction,
            FirebroChamp.moveSpeed, FirebroChamp.meleeAttackStrength, FirebroChamp.mana,
            FirebroChamp.magicResistence, FirebroChamp.attackSpeed,
             FirebroChamp.meleeAttackRange)
        self.champName = "firebro"
        self.spells['blink'] = self.blink
        self.spells['storm'] = self.storm
    def storm(self,target):
        if isinstance(target,Entity):
            target = target.position 
        target = target.minus(Vector(50,50))
        inRange = self.game.spatial.getEntitiesInRange(target,
            FirebroChamp.stormRange)
        toDamage = set()
        for entity in inRange:
            if entity.team != self.team:
                toDamage.add(entity)
        for entity in toDamage:
            entity.damage(FirebroChamp.stormDamage,self)
class AngelChamp(Champion):
    maxHealth = 250
    moveSpeed = 8
    meleeAttackStrength = 15
    mana = 50
    magicResistence = 5
    attackSpeed = .14
    meleeAttackRange = 120
    stealFraction = .2
    paralyzeTime = 5
    def __init__(self,game,team,sendMessageFunction):
        super().__init__(game,AngelChamp.maxHealth,team,sendMessageFunction,
            AngelChamp.moveSpeed, AngelChamp.meleeAttackStrength, AngelChamp.mana,
            AngelChamp.magicResistence, AngelChamp.attackSpeed,
             AngelChamp.meleeAttackRange)
        self.champName = "angel"
        self.spells['blink'] = self.blink
        self.spells['beam'] = self.beam

    def beam(self,target):
        time = 3
        if isinstance(target,Entity):
            target = target.position # We just want the position for the vector
        startPosition = self.position
        direction = target.minus(startPosition).normalize()
        while self.getAABB().containsPoint(startPosition):
            startPosition = startPosition.add(direction)
        startPosition.add(direction.multiply(2))
        lightbeam = LightBeam(self.game)
        lightbeam.position = startPosition
        lightbeam.setDirection(direction)
        lightbeam.team = self.team
        self.game.addEntity(lightbeam)
        removeBeam = lambda: lightbeam.destroy()
        self.game.scheduler.scheduleTimeTask(removeBeam,time)


