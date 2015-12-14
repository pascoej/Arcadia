import math
import timeout_decorator
import jps
import json
from heapq import *
def almostEqual(x,y):
    return abs(x-y) < 10**-4

class Vector(object):
    def __init__(self,x=0,y=0):
        self.x = x 
        self.y = y
    def add(self,other):
        return Vector(self.x + other.x, self.y + other.y)
    def minus(self,other):
        return Vector(self.x - other.x, self.y - other.y)
    def magnitude(self):
        norm = math.sqrt(self.x ** 2 + self.y ** 2)
        return norm
    def normalize(self):
        if (self.isZero()):
            return Vector()
        norm = self.magnitude()
        normalizedX = self.x / norm 
        normalizedY = self.y / norm
        return Vector(normalizedX, normalizedY)
    def multiply(self,factor):
        return Vector(self.x * factor, self.y * factor)
    def distanceSquared(self, other):
        return (self.x - other.x) **2 + (self.y - other.y)**2
    def __repr__(self):
        return "%f,%f" % (self.x, self.y)
    def __eq__(self,other):
        return (isinstance(other,Vector) and 
            self.x == other.x and self.y == other.y)
    def toTuple(self):
        return (self.x,self.y)
    def fromString(inputString):
        split = inputString.split(",")
        x = float(split[0])
        y = float(split[1])
        return Vector(x,y)
    def fromTuple(inputTuple):
        (x,y) = inputTuple
        return Vector(x,y)
    def roundToInteger(self):
        x = int(round(self.x))
        y = int(round(self.y))
        return Vector(x,y)
    def isZero(self):
        return almostEqual(self.x,0) and almostEqual(self.y,0)
    def toDict(self):
        rawDict = {}
        rawDict['x'] = self.x
        rawDict['y'] = self.y
        return rawDict
    def toJson(self):
        #6-7 hours on zooming, why
        return json.dumps(self.toDict())
    def __hash__(self):
        return hash((self.x, self.y))
class AABB(object):
    def __init__(self,minV,maxV):
        self.minV = minV
        self.maxV = maxV
    def containsPoint(self,v):
        if v.x < self.minV.x or v.y < self.minV.y:
            return False
        if v.x > self.maxV.x or v.y > self.maxV.y:
            return False
        return True
    def collides(self, other):
        if (self.maxV.x < other.minV.x
            or self.maxV.y < other.minV.y
            or self.minV.x > other.maxV.x
            or self.minV.y > other.maxV.y):
            return False
        return True
    def center(self):
        return self.minV.add(self.maxV).multiply(.5)
    #other is the thing u wanna stop colliding with
    def minTranslation(self, other):
        mt = Vector()
        left = other.minV.x - self.maxV.x
        right = other.maxV.x - self.minV.x
        top = other.minV.y - self.maxV.y
        bottom = other.maxV.y - self.minV.y
        if (left > 0 or right < 0):
            return mt
        if (top > 0 or bottom < 0):
            return mt
        if abs(left) < right:
            mt.x = left
        else:
            mt.x = right
        if abs(top) < bottom:
            mt.y = top
        else:
            mt.y = bottom
        if abs(mt.x) < abs(mt.y):
            mt.y = 0
        else:
            mt.x = 0
        return mt
    def __repr__(self):
        return str((self.minV,self.maxV))

def heuristic(p1, p2):
    return abs(p2[0]-p1[0]) + abs(p2[1]-p1[1])
dirs = [(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]
#handle trying to diagnal when 2 in way
specialCheck = {(1,1):[(0,1),(1,0)],(-1,1):[(-1,0),(1,0)],
(-1,-1):[(-1,0),(0,-1)],
(1,-1):[(1,0),(0,-1)]}
def isValid(array,locTuple):
    x,y = locTuple
    if x < 0 or x >= len(array):
        return False
    if y < 0 or y >= len(array[0]):
        return False
    if array[x][y] == True:
        return False
    return True
#def findPath(mapdata,startVector,goalVector):
#    naivePath = findNaivePath(mapdata,startVector,goalVector)
#    if (naivePath != -1):
#        return naivePath
#    jpsPath = performJps(mapdata,startVector,goalVector)
#    return jpsPath
def findPathAndSet(goal,currentLocation):
    mapdata = goal.game.map
    startVector = currentLocation
    goalVector = goal.goalLocation
    naivePath = findNaivePath(mapdata,startVector,goalVector)
    if (naivePath != -1 and naivePath != None):
        goal.path = naivePath
        goal.pathI = 1
        return
    doJPSAsync(goal,mapdata,startVector,goalVector)
#http://code.activestate.com/recipes/576684-simple-threading-decorator/
def run_async(func):
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target = func, args = args, kwargs = kwargs)
        func_hl.start()
        return func_hl
    return async_func
@run_async
def doJPSAsync(goal,mapdata,startVector,goalVector):
    jpsPath = performJps(mapdata,startVector,goalVector)
    goal.path = jpsPath
    if goal.path == -1:
        goal.valid = False
    elif goal.path != None:
        goal.pathI = 1
    else:
        del goal.path
def findNaivePath(mapdata,startVector,goalVector):
    collision = mapdata.collision.array
    start = startVector.multiply(1/mapdata.collisionFactor).roundToInteger()
    goal = goalVector.multiply(1/mapdata.collisionFactor).roundToInteger()
    if (start == goal):
        return -1
    if (not isValid(collision,start.toTuple()) or not isValid(collision,goal.toTuple())):
        return -1
    directionVector = goal.minus(start).normalize()
    current = start
    while (current.distanceSquared(goal) > 1.2):
        current = current.add(directionVector)
        if (not isValid(collision,current.roundToInteger().toTuple())):
            return -1
    return [startVector,goalVector]
def performJps(mapdata,startVector, goalVector):
    collision = mapdata.collision.array
    jps.pad_field(collision)
    start = startVector.multiply(1/mapdata.collisionFactor).roundToInteger().toTuple()
    goal = goalVector.multiply(1/mapdata.collisionFactor).roundToInteger().toTuple()

    (startX, startY) = start
    (endX, endY) = goal
    try:
        rawPath = jps.jps(collision,startX,startY,endX,endY)
    except:
        return -1
    path = []
    for coord in rawPath:
        path.append(Vector.fromTuple(coord).multiply(mapdata.collisionFactor))
    return path

#Returns path of vectors, none if no path
#path finding based currently on pseudocode availiable on wikipedia
#In the future I want to implement another search that will solve the 
#timeout issues
#More than 150ms is trouble
@timeout_decorator.timeout(.15, use_signals=False)
def aStarPath(mapdata, startVector, goalVector):
    collision = mapdata.collision.array
    start = startVector.multiply(1/mapdata.collisionFactor).roundToInteger().toTuple()
    goal = goalVector.multiply(1/mapdata.collisionFactor).roundToInteger().toTuple()
    if not isValid(collision,goal):
        return None
    closeSet = set()
    prev = {}
    g = {start:0}
    f = {start:heuristic(start,goal)}
    openHeap = []
    #This is just the python version of a priority queue
    heappush(openHeap,(f[start],start))
    while openHeap:
        cur = heappop(openHeap)[1]
        if (cur == goal):
            path = []
            while cur in prev:
                path.append(Vector.fromTuple(cur).multiply(mapdata.collisionFactor))
                cur = prev[cur]
            path = list(reversed(path))
            return path
        closeSet.add(cur)
        for oX,oY in dirs:
            neighbor = cur[0] + oX, cur[1] + oY
            tentGscore = g[cur] + heuristic(cur,neighbor)
            if (neighbor[0] < 0 or neighbor[0] >= len(collision) or 
                neighbor[1] < 0 or neighbor[1] >= len(collision[0])
                or not isValidMove(collision,cur,neighbor,(oX,oY))):
                continue
            if neighbor in closeSet and tentGscore > g.get(neighbor,0):
                continue
            if tentGscore < g.get(neighbor,0) or neighbor not in [i[1] for i in openHeap]:
                prev[neighbor] = cur
                g[neighbor] = tentGscore
                f[neighbor] = tentGscore + heuristic(neighbor,goal)
                heappush(openHeap,(f[neighbor],neighbor))
    return None
#http://stackoverflow.com/questions/12435211/python-threading-timer-repeat-function-every-n-seconds
import threading

def setInterval(interval):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = threading.Event()

            def loop(): # executed in another thread
                while not stopped.wait(interval): # until stopped
                    function(*args, **kwargs)

            t = threading.Thread(target=loop)
            t.daemon = True # stop if the program exits
            t.start()
            return stopped
        return wrapper
    return decorator