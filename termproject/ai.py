import random
import entity
from util import *
class AIController(object):
    def __init__(self):
        pass
    def onTick(self):
        pass
    def onDamage(self):
        pass
    def setEntity(self,entity):
        self.entity = entity
class PathBasedAIController(AIController):
    def __init__(self,paths):
        super().__init__()
        self.paths = paths
        self.randomRadius = 0
    def choosePath(self):
        self.path = random.choice(self.paths)
        self.pathPos = 1
    def findRandomizedPathLocation(self,loc):
        if (self.randomRadius == 0):
            return loc
        tries = 15
        for i in range(tries):
            deltaX = random.randint(-self.randomRadius,self.randomRadius)
            deltaY = random.randint(-self.randomRadius,self.randomRadius)
            offsetVector = Vector(deltaX,deltaY)
            randomizedVector = loc.add(offsetVector)
            if (not self.entity.game.map.isCollision(randomizedVector)
                and not self.entity.game.collidesWithEntity(randomizedVector)):
                return randomizedVector
        return loc
    def onTick(self):
        super().onTick()
        if self.pathPos >= len(self.path):
            return
        if self.entity.goal == None:
            location = self.findRandomizedPathLocation(self.path[self.pathPos])
            self.entity.goal = entity.Goal(self.entity.game,location)
            self.entity.goal.calculatePath(self.entity.position)
            self.pathPos += 1
class MinionAI(PathBasedAIController):
    def __init__(self,aiInfo,pathI):
        super().__init__(aiInfo.paths)
        self.aiInfo = aiInfo
        self.target = None
        self.path = aiInfo.paths[pathI % len(aiInfo.paths)]
        self.pathPos = 1
        self.randomRadius = 60
        self.targetCheckI = 0
    def isValidTarget(self,other,checkDistance=True):
        if self.entity.isValidTarget(other,checkDistance) and other.team != self.aiInfo.team:
            return True
        return False
    def findTarget(self):
        if self.targetCheckI % 12:
            for entity in self.entity.entitiesWithinAttackRange():
                if self.isValidTarget(entity,checkDistance=False):
                    self.target = entity
                    return
            self.target = None
        self.targetCheckI = self.targetCheckI + 1
    def onTick(self):
        if self.target == None or not self.isValidTarget(self.target):
            self.findTarget()
        if self.target != None:
            self.entity.target = self.target
            self.entity.immoveable = True
            self.entity.attack()
        else:
            self.entity.immoveable = False
        super().onTick()
    def setEntity(self,entity):
        super().setEntity(entity)
        entity.team = self.aiInfo.team
        entity.position = self.findRandomizedPathLocation(self.path[0])
