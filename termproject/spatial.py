from util import *
import math
#nothing like last minute performance problems :p
#Note the cell size must be such that the longestEdge of AABBs are not
#bigger than the grid
class Spartial(object):
    def __init__(self,cellSize):
        self.cellSize = cellSize
        self.map = {}
        self.cellsByEntity = {}
        self.aabbsByEntity = {}
        self.cachedCollding = None
    def clear(self):
        self.cachedCollding = None
        self.map.clear()
        self.cellsByEntity.clear()
        self.aabbsByEntity.clear()

    def addEntity(self, entity):
        cellSize = self.cellSize
        aabb = entity.getAABB()
        self.aabbsByEntity[entity] = aabb
        maxX = int(aabb.maxV.x//cellSize)
        minX = int(aabb.minV.x//cellSize)

        maxY = int(aabb.maxV.y//cellSize)
        minY = int(aabb.minV.y//cellSize)
        occupyingCells = []
        for x in range(minX,maxX+1):
            for y in range(minY,maxY+1):
                key = (x,y)
                if key in self.map:
                    self.map[key].append(entity)
                else:
                    self.map[key] = [entity]
                occupyingCells.append(key)
        self.cellsByEntity[entity] = occupyingCells
    def entityTuple(entity1,entity2):
        if hash(entity1) < hash(entity2):
            return (entity1,entity2)
        else:
            return (entity2,entity1)
    #Returns tuples of colliding entities    
    def getCollidingEntities(self):
        if self.cachedCollding != None:
            return self.cachedCollding
        checked = set()
        colliding = []
        for entity in self.cellsByEntity.keys():
            occupyingCells = self.cellsByEntity[entity]
            for cell in occupyingCells:
                for otherEntity in self.map[cell]:
                    if (otherEntity != entity):
                        checkedTuple = Spartial.entityTuple(entity,otherEntity)
                        if checkedTuple not in checked:
                            checked.add(checkedTuple)
                            aabb1 = self.aabbsByEntity[entity]
                            aabb2 = self.aabbsByEntity[otherEntity]
                            if (aabb1.collides(aabb2)):
                                colliding.append(checkedTuple)
        self.cachedCollding = colliding
        return colliding

    def getEntitiesInRange(self,loc,distance):
        distSquared = distance**2
        (cellX, cellY) = int(loc.x//self.cellSize),int(loc.y//self.cellSize)
        maxCellsAway = int(math.ceil(distance/self.cellSize))
        minX = cellX - maxCellsAway
        maxX = cellX + maxCellsAway
        minY = cellY - maxCellsAway
        maxY = cellY + maxCellsAway
        inRange = set()
        checked = set()
        for x in range(minX,maxX+1):
            for y in range(minY,maxY+1):
                key = (x,y)
                if key in self.map:
                    for possibleEntity in self.map[key]:
                        if (possibleEntity not in checked 
                            and not (possibleEntity.position is loc) 
                            and possibleEntity.position.distanceSquared(loc) 
                            < distSquared):
                            inRange.add(possibleEntity)
        return inRange





