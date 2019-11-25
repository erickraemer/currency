# -*- coding: utf-8 -*-
import sys
sys.platform = "win32"
import os, threading, json, codecs, traceback, time, subprocess, base64, re
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
Version = "1.0.0.5"

#returns script folder path + filename
def getPath(filename):
    return os.path.join(os.path.dirname(__file__), filename)
    
def openWebsite():
    os.system("start \"\" {}".format(Website))
    return
    
def toJson(object):
    return json.dumps(object, sort_keys=True, indent=2)

def readJson(path, enc):
    with codecs.open(path, encoding=enc, mode="r") as f:
        return json.load(f, encoding="utf-8")

def writeJson(path, jsonData, enc):
    with codecs.open(path, encoding=enc, mode="w") as f:
        f.write(jsonData)
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
    global discordPreCommand
   
    logActive = False
    logData = list()
    logPath = getPath("currency.log")
    thread = None
    stopEvent = threading.Event()
    settings = ScriptSettings()
    scoreSummary = dict()
    discordPreCommand = "py \"{}\"".format(os.getcwd() + getPath("DiscordNotifier.py")[1:])
    
    if settings.valid() and settings.DecayActive:
        decayLog = DecayTracker("decaylog.json")
    return

#stop thread and calculate point decay
def Unload():
    if thread and thread.isAlive():
        stopEvent.set()
        thread.join()
    return 

def Tick():
    return

def Execute(Data):
    return

#stop or start thread
def ScriptToggled(state):
    global thread
    
    if not settings.valid():
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
    
def ReloadSettings(jsonData):
    settings.reload(jsonData)
    return

#contains user settings
class ScriptSettings():
    __jsonPath = getPath("settings.json")
    __jsPath = getPath("settings.js")

    def __init__(self):
        try:
            self.__dict__ = readJson(ScriptSettings.__jsonPath, "utf-8-sig")
        except:
            return
        self.__adjustValues()
        return

    def reload(self, jsonData):
        self.__dict__ = json.loads(jsonData)
        self.__adjustValues()
        return
    
    def __checksum(self):
        if not re.search("[^*]", self.DiscordToken):
            return
            
        self.Checksum = base64.encodestring(self.DiscordToken)
        self.DiscordToken = 20 * '*' 
        s = toJson(self.__dict__)
        writeJson(ScriptSettings.__jsonPath, s, "utf-8-sig")
        writeJson(ScriptSettings.__jsPath, "var settings = {};".format(s), "utf-8-sig")
        return

    def __adjustValues(self):
        global discordPostCommand
        
        self.__checksum()
        discordPostCommand = "\"{}\" \"{}\"".format(self.DiscordChannel, base64.decodestring(self.Checksum))
        self.PayoutAmount = int(self.PayoutAmount)
        self.PayoutInterval = timedelta(minutes=self.PayoutInterval)
        self.DecayCooldown = timedelta(hours=self.DecayCooldown)
        self.DecayInterval = timedelta(hours=self.DecayInterval)
        self.DecayViewerAmount = int(filter(str.isdigit, self.DecayViewerAmount))
        self.DecayFixed = self.DecayFixed == "Fixed"
        self.PollRate = 30
        
        #indicates that settings are correctly loaded 
        self.flag = True
        return
        
    def valid(self):
        return "flag" in self.__dict__.keys()
    
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
            temp = readJson(self.__path, "utf-8")
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
        for k,v in self.data.iteritems():
            temp[k] = int(v.total_seconds() / 60)
        writeJson(self.__path, toJson(temp), "utf-8")
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
    sendDiscordInfo() 
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
    if not(scoreSummary and
        settings.AnnounceDiscord):
        return

    prefix = "Today's Score:"
    msg = ",  ".join(": ".join((Parent.GetDisplayName(k),"+{}".format(v) if v > 0 else str(v))) for k,v in sorted(scoreSummary.iteritems(), key=lambda (k,v): (-v,k)))
    command = "{} \"{}\" \"{}\" {}".format(discordPreCommand, msg, prefix, discordPostCommand)
    
    sp = subprocess.Popen(command, stderr=subprocess.PIPE, shell=True)
    err = sp.communicate()[1]
    
    if err:
        Log("Sending score summary to Discord failed with:\n{}".format(err))
        settings.AnnounceDiscord = False

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