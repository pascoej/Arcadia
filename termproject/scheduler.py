import time
from operator import attrgetter
import sys
import traceback
class TimerTask(object):
    def __init__(self,f,currentTime,duration):
        self.f = f
        self.time = currentTime + duration
        self.duration = duration
    def getTime(self):
        return self.time
    def run(self,scheduler):
        self.f()
class RepeatingTimerTask(TimerTask):
    pass

class Scheduler(object):
    def __init__(self):
        self.tickTime = 0
        self.timeTimers = []
        self.tickTimers = []
    def tick(self):
        self.tickTime += 1
        self.checkTickTimers()
        self.checkTimeTimers()
    def checkTickTimers(self):
        if len(self.tickTimers) == 0:
            return
        current = self.tickTimers[0]
        while (current != None and current.getTime() <= self.tickTime):
            current = self.tickTimers.pop(0)
            try:
                current.run(self)
            except:
                print(traceback.format_exc())
            if isinstance(current,RepeatingTimerTask):
                self.scheduleTickTask(current.f,current.duration)
            if (len(self.tickTimers) > 0):
                current = self.tickTimers[0]
            else:
                current = None
    def checkTimeTimers(self):
        if len(self.timeTimers) == 0:
            return
        currentTime = time.time()
        current = self.timeTimers[0]
        while (current != None and current.getTime() <= currentTime):
            current = self.timeTimers.pop(0)
            try:
                current.run(self)
            except Exception as e:
                print(traceback.format_exc())
            if isinstance(current,RepeatingTimerTask):
                self.scheduleTimeTask(current.f,current.duration,True)
            if (len(self.timeTimers) > 0):
                current = self.timeTimers[0]
            else:
                current = None
    def scheduleTimeTask(self, f, timeToWait, repeating=False):
        task = None
        if repeating:
            task = RepeatingTimerTask(f,time.time(),timeToWait)
        else:
            task = TimerTask(f,time.time(),timeToWait)
        self.timeTimers.append(task)
        self.timeTimers.sort(key=attrgetter('time'))
    def scheduleTickTask(self, f, ticksToWait, repeating=False):
        task = None
        if repeating:
            task = RepeatingTimerTask(f,self.tickTime,ticksToWait)
        else:
            task = TimerTask(f,self.tickTime,ticksToWait)
        self.tickTimers.append(task)
        self.tickTimers.sort(key=attrgetter('time'))


