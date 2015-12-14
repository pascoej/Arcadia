import png
import json
import util
from entity import *
def make2dList(rows, cols):
    a=[]
    for row in range(rows): a += [[False]*cols]
    return a
class Image(object):
    def __init__(self, width, length, array):
        self.width = width
        self.length = length
        self.array = array
        self.numArray = Image.toNumArray(self.array)
    def toNumArray(array):
        numArray = make2dList(len(array),len(array[0]))
        for i in range(len(array)):
            for j in range(len(array[0])):
                numArray[i][j] = int(array[i][j])
        return numArray
    def getValueFromFrac(self,x,y):
        x = int(x*self.width)
        y = int(y*self.length)
        return self.array[x][y]
    def fromFile(path):
        r = png.Reader(file=open(path,'rb'))
        read = r.read()
        width = read[0]
        height = read[1]
        array = make2dList(width,height)
        pixels = list(read[2])
        for x in range(width):
            for y in range(height):
                array[x][y] = not pixels[y][x]
        return Image(width,height,array)
class BuildingInfo(object):
    def __init__(self,buildingType,team,location):
        self.buildingType = buildingType
        self.team = team
        self.location = location
class AIInfo(object):
    def __init__(self,paths,entityType,autoAttack,team):
        self.paths = paths
        self.entityType = entityType
        self.autoAttack = autoAttack
        self.team = team

class GameMap(object):
    def __init__(self, folder):
        configFilePath = folder + "/config.json"
        collisionMapImage = folder + "/collision_250.png"
        self.collision = Image.fromFile(collisionMapImage)
        configJson = json.load(open(configFilePath))
        self.width = configJson['width']
        self.length = configJson['length']
        self.collisionFactor = self.width/len(self.collision.array)
        self.loadSpawns(configJson)
        self.loadBuildings(configJson)
        self.loadPaths(configJson)
        self.loadAIInfos(configJson)
    def loadAIInfos(self,configJson):
        self.aiInfos = {}
        aiJson = configJson['ai']
        for aiName, ai in aiJson.items():
            paths = []
            pathStrings = ai['paths']
            for pathString in pathStrings:
                paths.append(self.paths[pathString])
            entityType = ai['type']
            autoAttack = ai['autoattack']
            team = ai['team']
            aiinfo = AIInfo(paths,entityType,autoAttack,team)
            self.aiInfos[aiName] = aiinfo 

    def loadPaths(self,configJson):
        self.paths = {}
        pathsJson = configJson['paths']
        for pathName,pathStringList in pathsJson.items():
            path = []
            for pathString in pathStringList:
                path.append(util.Vector.fromTuple(pathString))
            self.paths[pathName] = path
    def loadBuildings(self,configJson):
        self.buildings = []
        jsonBuildings = configJson['buildings']
        for jsonBuilding in jsonBuildings:
            loc = util.Vector.fromString(jsonBuilding['location'])
            team = jsonBuilding['team']
            buildingType = jsonBuilding['type']
            building = BuildingInfo(buildingType,team,loc)
            self.buildings.append(building)

    def loadSpawns(self,configJson):
        self.spawns = {}
        jsonSpawns = configJson['spawns']
        for key, value in jsonSpawns.items():
            self.spawns[key] = util.Vector.fromString(value)
    def isInBounds(self, loc):
        if (loc.x < 0 or loc.y < 0):
            return False
        if (loc.x > self.width or loc.y > self.length):
            return False
        return True
    def isCollision(self,loc):
        if not self.isInBounds(loc):
            return True
        fracX = loc.x / self.width
        fracY = loc.y / self.length
        return self.collision.getValueFromFrac(fracX,fracY)
    def collisionMapToJson(self):
        return json.dumps(self.collision.numArray)
    def getSpawn(entity):
        if isinstance(entity,Champion):
            return self.spawns[entity.team]
    def spawnBuildings(self,game):
        for buildingInfo in self.buildings:
            team = buildingInfo.team
            buildingType = buildingInfo.buildingType
            building = Building.getNewBuilding(game,team,buildingType)
            building.position = buildingInfo.location
            game.addEntity(building)



