import sys, os
sys.path = [os.path.abspath(os.path.dirname(__file__))] + sys.path

from util import *
from spatial import *
from nose.tools import *
def setup():
    print("SETUP!")

def teardown():
    print("ok")
def test_vector():
    epsilon = 10**-5
    v1 = Vector(0,0)
    v2 = Vector(1,1)
    v3 = Vector(2,2)
    assert(v1 != v2)
    assert(v2.minus(v1) == v2)
    assert(v2.add(v1) == v2)
    assert(v1.add(v1.multiply(2)) == v1)
    assert(v3.minus(v2) == v2)
    assert(v3.normalize().distanceSquared(v2.normalize()) < epsilon)
def test_aabb():
    box1 = AABB(Vector(0,0),Vector(50,50))
    box2 = AABB(Vector(25,25),Vector(50,50))
    box3 = AABB(Vector(51,51),Vector(100,100))
    box4 = AABB(Vector(0,50),Vector(50,100))
    assert(box1.collides(box2))
    assert(box2.collides(box1))
    assert(not box1.collides(box3))
    assert(not box3.collides(box2))
    assert(box1.collides(box4))
    assert(box4.collides(box2))
class FakeEntity(object):
    def __init__(self,x,y,xRadius,yRadius):
        self.x = x
        self.y = y
        self.aabb = AABB(Vector(x-xRadius,y-yRadius),Vector(x+xRadius,y+yRadius))
        self.position = Vector(x,y)
    def getAABB(self):
        return self.aabb


def testSpatial():
    fakeEntity1 = FakeEntity(220,440,100,100)
    fakeEntity2 = FakeEntity(210,430,50,50)
    fakeEntity3 = FakeEntity(500,500,10,10)
    spatial = Spartial(100)
    spatial.addEntity(fakeEntity1)
    spatial.addEntity(fakeEntity2)
    spatial.addEntity(fakeEntity3)
    print(fakeEntity1,"\n",fakeEntity2,"\n",fakeEntity3)
    assert(spatial.getEntitiesInRange(fakeEntity1.position,195)
     == set([fakeEntity2]))
    assert(spatial.getEntitiesInRange(fakeEntity2.position,195) 
        == set([fakeEntity1]))
    assert(spatial.getEntitiesInRange(fakeEntity1.position,100)
     == set([fakeEntity2]))
    assert(spatial.getEntitiesInRange(fakeEntity2.position,100) 
        == set([fakeEntity1]))
    assert(spatial.getEntitiesInRange(fakeEntity1.position,20) 
        == set([fakeEntity2]))
    assert(spatial.getEntitiesInRange(fakeEntity2.position,20)
     == set([fakeEntity1]))
    assert(spatial.getEntitiesInRange(fakeEntity1.position,5) 
        == set([]))
    assert(spatial.getEntitiesInRange(fakeEntity2.position,5) 
        == set([]))
    assert(spatial.getCollidingEntities() 
        == [Spartial.entityTuple(fakeEntity1,fakeEntity2)])
    test1 = FakeEntity(7032.544652,2324.626887,12,12)
    test2 = FakeEntity(7023.0528,2270.307,12,12)
    spatial.addEntity(test1)
    spatial.addEntity(test2)
    print(spatial.getEntitiesInRange(test1.position,195))
    assert(spatial.getEntitiesInRange(test1.position,195) == set([test2]))
