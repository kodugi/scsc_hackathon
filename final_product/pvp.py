import datetime

class PvpMatch:
    def __init__(self, host, problemId):
        self.host = host
        self.opponent = None
        self.hostStartTime = datetime.now()
        self.problemId = problemId
        self.opponentStartTime = None
        self.hostTime = None
        self.opponentTime = None
    def setOpponent(self, opponent):
        self.opponent = opponent
        self.opponentStartTime = datetime.now()
    def endHost(self):
        self.hostTime = datetime.now() - self.hostStartTime
        self.getMatchResult()
    def endOpponent(self):
        self.opponentTime = datetime.now() - self.opponentStartTime
        self.getMatchResult()
    def getMatchResult(self):
        if(self.hostTime != None and self.opponentTime != None):
            return self.hostTime < self.opponentTime
        else:
            return None

class PvpManager:
    def __init__(self):
        self.pvps = []
    def findPvp(self, user):
        pvpList = []
        for pvp in self.pvps:
            if(pvp.host == user or pvp.opponent == user):
                pvpList.append(pvp)
        return pvpList
    def newPvp(self, user, problemId):
        for pvp in self.pvps:
            if(pvp.problemId == problemId and pvp.opponent == None):
                pvp.setOpponent(user)
    def endPvp(self, user, problemId):
        for pvp in self.pvps:
            if(pvp.problemId == problemId):
                if(pvp.host == user):
                    pvp.endHost()
                elif(pvp.opponent == user):
                    pvp.endOpponent()