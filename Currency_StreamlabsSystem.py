# -*- coding: utf-8 -*-
import sys
sys.platform = "win32"
import os, threading, json, codecs, traceback, time
from time import localtime, strftime
from datetime import timedelta
#NOTE: 
#Conflicts with the Visual Studio Python installation. 
#Use the normal Python installation for streamlabs chatbot!

#---------------------------
#   [Required] Script Information
#---------------------------
ScriptName = "[Currency]"
Website = "https://github.com/erickraemer/currency"
Description = "An enhancement script for the streamlabs loyality system which rewards your viewers with points for watching your stream."
Creator = "Eric Krämer"
Version = "1.0.0.4"

#returns script folder path + filename
def getPath(filename):
    return os.path.join(os.path.dirname(__file__), filename)
    
def openWebsite():
    os.system("start \"\" {}".format(Website))
    return

#set variables
def Init():
    global settings
    global stopEvent
    global scoreSummary
    global logActive
    global logData
    global logPath
    global decayLog
    global thread
    
    logActive = False
    logData = list()
    logPath = getPath("currency.log")
    thread = None
    stopEvent = threading.Event()
    settings = ScriptSettings()
    scoreSummary = dict()
    
    if settings.Valid and settings.DecayActive:
        decayLog = DecayTracker("decaylog.json")
    return

#stop thread and calculate point decay
def Unload():
    if thread and thread.isAlive():
        stopEvent.set()
        thread.join()

    sendDiscordInfo()     
    return 

def Tick():
    return

def Execute(Data):
    return

#stop or start thread
def ScriptToggled(state):
    global thread
    
    if not settings.Valid:
        Error("Settings could not be loaded, did you hit the \"Save Settings\" button?")
        return

    if state and not (thread and thread.isAlive()):
        thread = threading.Thread(target=exceptionCatcher)
        stopEvent.clear()
        thread.start()
    elif not state and thread and thread.isAlive():
        stopEvent.set()
        thread.join()
    return
    
def Reloadsettings(jsonData):
    settings.Reload(jsonData)
    return

#contains user settings
class ScriptSettings():

    def __init__(self):
        self.__load()

    def reload(self, jsonData):
        self.__load()
    
    def __load(self):
        self.Valid = False
        try:
            #try loading settings
            file = getPath("settings.json")
            with codecs.open(file, encoding="utf-8-sig", mode="r") as f:
                self.__dict__ = json.load(f, encoding="utf-8")
        except:
            return
            
        #set time format
        self.PayoutAmount = int(self.PayoutAmount)
        self.PayoutInterval = timedelta(minutes=self.PayoutInterval)
        self.DecayCooldown = timedelta(hours=self.DecayCooldown)
        self.DecayInterval = timedelta(hours=self.DecayInterval)
        self.DecayViewerAmount = int(filter(str.isdigit, self.DecayViewerAmount))
        self.DecayFixed = self.DecayFixed == "Fixed"
        self.Valid = True
        self.PollRate = 30
        return

class DecayTracker():
    def __init__(self, filename):
        self.data = dict()
        self.__path = getPath(filename)
        self.load()
        return
        
    def __getitem__(self, key):
        return self.data[key]
        
    def __setitem__(self, key, value):
        self.data[key] = value
        return
        
    def update(self):
        sotv = set(Parent.GetTopCurrency(settings.DecayViewerAmount).keys())
        dlKeys = set(self.data.keys())
        difA = dlKeys.difference(sotv)
        difB = sotv.difference(dlKeys)
        if difA or difB: 
            self.data.update(dict.fromkeys(difB, timedelta()))
            for e in difA:
                del self.data[e]
            self.save()
        return
        
    def load(self):
        if os.path.isfile(self.__path):
            with open(self.__path, "r") as f:
                temp = json.loads(f.read())
                for k,v in temp.iteritems():
                    self.data[k] = timedelta(minutes=v)
            self.update()
            return
        
        dotv = Parent.GetTopCurrency(settings.DecayViewerAmount)
        for k in dotv.keys():
            dotv[k] = timedelta()
        self.data = dotv
        self.save()
        return
        
    def save(self):
        temp = dict()
        with open(self.__path, "w") as f:
            for k,v in self.data.iteritems():
                temp[k] = int(v.total_seconds() / 60)
            f.write(json.dumps(temp))
        return        

#catches exceptions from the thread and prints them to the log console
def exceptionCatcher():
    try:
        run()
    except BaseException as ex:
        Log(str(traceback.format_exc()))
    return
        
#check if stream is live and add points after PayoutInterval
def run():
    #wait until stream is live or script is stopped
    while not Parent.IsLive():
        if stopEvent.wait(settings.PollRate):
            return
    
    setupLogging()
    nextPayout = time.time() + settings.PayoutInterval.total_seconds() - (time.time() % settings.PayoutInterval.total_seconds())
    while Parent.IsLive():
        if stopEvent.wait(nextPayout - time.time()):
            break
        
        nextPayout += settings.PayoutInterval.total_seconds()
        payoutPoints()
    return

#write saved log info to file if the stream goes live
def setupLogging():
    global logActive
    global logData
        
    logActive = True
    with open(logPath, "w") as f:
        f.write("Date: {}\n".format(strftime("%d %B %Y", localtime())))
        for s in logData:
            f.write("{}\n".format(s))
            
    logData[:] = []
    return

#add points for every active viewer and check session presence
def payoutPoints():
    #add points for viewers
    viewer = getActiveUsers()
    if not viewer:
        Log("No viewers to give points to!")  
        return
    
    for v in viewer:
        addPoints(v, settings.PayoutAmount)
    
    updateDecayLog(viewer)
    payoutNotification(viewer)
    return
    
def payoutNotification(viewer):
    msg = "+{} {} for: {}".format(settings.PayoutAmount,
        Parent.GetCurrencyName(),
        ", ".join(Parent.GetDisplayName(v) for v in viewer))
    Log(msg)
    
    if settings.AnnouncePayout:
        Parent.SendStreamMessage("/me {}".format(msg.replace(", ", ", ~")))
    return
    
def getActiveUsers():
    viewer = set()
    
    for user in Parent.GetActiveUsers():
        if Parent.GetDisplayName(user) == Parent.GetChannelName():
            continue
        if Parent.GetPoints(user) <= 0:
            link = "https://api.crunchprank.net/twitch/followed/{}/{}".format(Parent.GetChannelName(), user)
            result = Parent.GetRequest(link, {})
            if (json.loads(result)["status"] != 200 or
            "-" not in json.loads(result)["response"]):
                continue
        
        viewer.add(user)
    return viewer

def updateDecayLog(viewer):
    if not settings.DecayActive:
        return
        
    decayLog.update()
            
    #reset or increase decay for viewers
    for k in decayLog.data.keys():
        if k in viewer:
            decayLog[k] = timedelta()
        else:
            checkDecay(k)
            
    decayLog.save()
    return

def checkDecay(user):
    cooldownReached = decayLog[user] + settings.PayoutInterval >= settings.DecayCooldown
    decayIntervalReached = (decayLog[user] < settings.DecayCooldown or timedelta(seconds=(decayLog[user] - settings.DecayCooldown).total_seconds() % settings.DecayInterval.total_seconds()) + settings.PayoutInterval >= settings.DecayInterval)
    
    decayLog[user] += settings.PayoutInterval
    if not (cooldownReached and decayIntervalReached):
        return

    percent = getDecayAmount(user)
    decay = int((percent / 100.0) * Parent.GetPoints(user))
        
    removePoints(user, decay)
    Log("{}% decay (-{} {}) for: {}, last seen {} hours ago".format(percent, decay, Parent.GetCurrencyName(), Parent.GetDisplayName(user), int(decayLog[user].total_seconds() / 3600)))
    return

def getDecayAmount(user):
    if settings.DecayFixed:
        return settings.DecayAmount 
    
    return int((decayLog[user] - settings.DecayCooldown + settings.DecayInterval).total_seconds() / settings.DecayInterval.total_seconds())

#sends a discord information at the end of the stream
def sendDiscordInfo():
    if not scoreSummary:
        return

    msg1 = ",  ".join(": ".join((Parent.GetDisplayName(k),"+{}".format(v) if v > 0 else str(v))) for k,v in sorted(scoreSummary.iteritems(), key=lambda (k,v): (-v,k)))
    msg = "Today's Score:\n{}".format(msg1);
    Log(msg)
    
    if settings.AnnounceDiscord:
        Parent.SendDiscordMessage(msg)
    return
    
def addPoints(user, amount):
    Parent.AddPoints(user, settings.PayoutAmount)
    scoreSummary[user] = scoreSummary.get(user, 0) + settings.PayoutAmount
    return
    
def removePoints(user, amount):
    Parent.RemovePoints(user, amount)
    scoreSummary[user] = scoreSummary.get(user, 0) - amount
    return
    
#write log to file after stream goes live
#else save info for later
def Log(msg):
    msg = "{} {}".format(strftime("%H:%M", localtime()), msg)
    Parent.Log(ScriptName, msg)
    if not logActive:
        logData.append(msg)
        return

    with open(logPath, "a") as f:
        f.write("{}\n".format(msg))
    return
    
def Error(msg):
    Parent.SendStreamWhisper(Parent.GetChannelName(), "{}: {}".format(ScriptName, msg))
    return
