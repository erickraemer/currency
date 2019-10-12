# -*- coding: utf-8 -*-
import os, sys, threading, json, codecs, logging, traceback, time
from time import localtime, strftime
from datetime import timedelta
#NOTE: 
#Conflicts with the Visual Studio Python installation. 
#Use the normal Python installation for streamlabs chatbot!

#---------------------------
#   [Required] Script Information
#---------------------------
ScriptName = "[Currency]"
Website = "https://www.twitch.tv/blackoutroulette"
Description = "Gives every viewer a custom amount of currency every x seconds."
Creator = "BlackoutRoulette"
Version = "1.3.2.2"

#returns script folder path + filename
def getPath(filename):
    return os.path.join(os.path.dirname(__file__), filename)

def openReadme():
    os.startfile(getPath("readme.txt"))
    return
    
def donate():
    return

#set variables
def Init():
    global settings
    global stopEvent
    global thread
    global sessionPresence
    global logActive
    global logData
    global decayLog
    
    logActive = False
    logData = list()

    stopEvent = threading.Event()
    
    settings = ScriptSettings()
    
    sessionPresence = dict()
    
    thread = threading.Thread(target=exceptionCatcher)
    #thread.setDaemon(True)
    decayLog = FileManager("decay_log.json")
    return

#stop thread and calculate point decay
def Unload():
    if thread.isAlive():
        stopEvent.set()
        thread.join()
        
    if not sessionPresence:
        return
        
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

    if state and not thread.isAlive():
        stopEvent.clear()
        thread.start()
    elif not state and thread.isAlive():
        stopEvent.set()
        thread.join()
        thread = threading.Thread(target=exceptionCatcher)
        #thread.setDaemon(True)
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
            
            #set time format
            self.PayoutInterval = timedelta(minutes=self.PayoutInterval)
            self.DecayCooldown = timedelta(hours=self.DecayCooldown)
            self.DecayInterval = timedelta(hours=self.DecayInterval)
            self.DecayViewerAmount = int(filter(str.isdigit, self.DecayViewerAmount))
            self.DecayFixed = self.DecayFixed == "Fixed"
            self.Valid = True
        except:
            pass
        self.sPFileName = "session_presence.txt"
        self.PollRate = 30
        return

class FileManager():
    def __init__(self, filename):
        self.data_ = dict()
        self.__path = getPath(filename)
        self.load()
        return
        
    def load(self):
        if os.path.isfile(self.__path):
            f = open(self.__path, "r")
            self.data_ = json.loads(f.read())
            f.close()
            return
       
        dotv = Parent.GetTopCurrency(settings.DecayViewerAmount)
        for k in dotv.keys():
            dotv[k] = 0
        self.data_ = dotv
        self.save()
        return
        
    def save(self):
        f = open(self.__path, "w")
        f.write(json.dumps(self.data_))
        f.close()
        return        

#catches exceptions from the thread and prints them to the log console
def exceptionCatcher():
    try:
        run()
    except BaseException as ex:
        Parent.Log(ScriptName, str(traceback.format_exc()))
    return
        
#check if stream is live and add points after PayoutInterval
def run():
    global msgOnline
    msgOnline = False
    
    #wait until stream is live or script is stopped
    while not Parent.IsLive():
        if stopEvent.wait(settings.PollRate):
            return
    
    setupLogging()
    nextPayout = time.time() + settings.PayoutInterval - (time.time() % settings.PayoutInterval)
    while Parent.IsLive():
        if stopEvent.wait(nextPayout - time.time()):
            break
        
        nextPayout += settings.PayoutInterval
        addPoints()
    return

#write saved log info to file if the stream goes live
def setupLogging():
    global logActive
    global logData
        
    logActive = True
    logging.basicConfig(filename=getPath("currency.log"),
        filemode="w",
        level=logging.INFO,
        format="%(message)s")
    
    logging.info("Date: {}".format(strftime("%d %B %Y", localtime())))
    
    for s in logData:
        logging.info(s)
    logData[:] = []
    return

#add points for every active viewer and check session presence
def addPoints():
    #add points for viewers
    viewer = getActiveUsers()
    
    for v in viewer:
        #Todo: create one function for log and add points
        Parent.AddPoints(v, settings.PayoutAmount)
        sessionPresence[v] = sessionPresence.get(v, 0) + settings.PayoutAmount
    
    updateDecayLog(viewer)
   
    msg = ", ".join("~{}".format(Parent.GetDisplayName(v)) for v in viewer)
    if msg:
        msg = "+{} {} for: {}".format(settings.PayoutAmount, Parent.GetCurrencyName(), msg)
        if settings.AnnouncePayout:
            Parent.SendStreamMessage("/me {}".format(msg))
        Log(msg.replace('~', ''))
    else:
        Log("No viewers to give points to!")  
    return
    
def getActiveUsers():
    viewer = set()
    
    for user in Parent.GetActiveUsers():
        if Parent.GetPoints(user) > 0:
            viewer.add(user)
        else:
            #check if user is following
            link = "https://api.crunchprank.net/twitch/followed/{}/{}".format(Parent.GetChannelName(), user)
            result = Parent.GetRequest(link, {})
            if (json.loads(result)["status"] == 200 and
            json.loads(result)["response"] != "Follow not found"):
                viewer.add(user)
    return viewer

def updateDecayLog(viewer):
    if not settings.DecayActive:
        return

     #check if local top 10 is up to date
    sotv = set(Parent.GetTopCurrency(settings.DecayViewerAmount).keys())
    dlKeys = set(decayLog.data_.keys())
    difA = dlKeys.difference(sotv)
    if difA:
        difB = sotv.difference(dlKeys)
        decayLog.data_.update(dict.fromkeys(difB, 0))
        for e in difA:
            del decayLog.data_[e]
            
    #reset decay for top 10 viewers
    for k in decayLog.data_.keys():
        if k in viewer:
            decayLog.data_[k] = 0
        else:
            #Use timedelta for decaylog
            if (timedelta(minutes=decayLog.data_[user]) > settings.DecayCooldown and
            decayLog.data_[k] % 60 + settings.PayoutInterval >= 60):
                calculateDecay(k)
            
            decayLog.data_[k] += settings.PayoutInterval
    decayLog.save()
    return

def calculateDecay(user):
    decay = settings.DecayAmount
    if not settings.DecayFixed:
        percent = decayLog.data_[user]/settings.DecayInterval
        decay = int((percent/100.0) * Parent.GetPoints(user))
        
    Parent.RemovePoints(user, decay)
    sessionPresence[user] = sessionPresence.get(user, 0) - decay
    Log("{}% decay (-{} {}) for: {}".format(percent, decay, Parent.GetCurrencyName(), Parent.GetDisplayName(user)))
    Log("{}: last seen {} hours ago.".format(Parent.GetDisplayName(user), decayLog.data_[user] * (settings.PayoutInterval / 60) / 60))
    return

#sends a discord information at the end of the stream
def sendDiscordInfo():
    if not settings.AnnounceDiscord:
        return
    
    msg1 = ",  ".join(": ".join((Parent.GetDisplayName(k),"+{}".format(v) if v > 0 else str(v))) for k,v in sorted(sessionPresence.iteritems(), key=lambda (k,v): (-v,k)))
    msg = "Heutige Punkteverteilung:\n{}".format(msg1);
    Parent.SendDiscordMessage(msg)
    Log(msg)
    return
    
#write log to file after stream goes live
#else save info for later
def Log(msg):
    msg = "{} {}".format(strftime("%H:%M", localtime()), msg)
    #Parent.Log(ScriptName, msg)
    if not logActive:
        logData.append(msg)
        return

    logging.info(msg)
    return
    
def Error(msg):
    Parent.SendStreamWhisper(Parent.GetChannelName(), "{}: {}".format(ScriptName, msg))
    return