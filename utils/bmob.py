# coding=utf-8

import json
import time

try:
    from urllib import quote
    import urllib2 as import_urllib
except ImportError:
    from urllib.parse import quote
    import urllib.request as import_urllib


class BmobObject:
    def __init__(self, type):
        self.__dict__["__type"] = type


class BmobPointer(BmobObject):
    def __init__(self, className, objectId):
        BmobObject.__init__(self, "Pointer")
        self.__dict__["className"] = className
        self.__dict__["objectId"] = objectId


class BmobFile(BmobObject):
    def __init__(self, url, filename=""):
        BmobObject.__init__(self, "File")
        self.__dict__["url"] = url
        self.__dict__["filename"] = filename


class BmobDate(BmobObject):
    def __init__(self, timestamp):
        BmobObject.__init__(self, "Date")
        if type(timestamp) == float or type(timestamp) == int:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp / 1000))
        self.__dict__["iso"] = timestamp


class BmobGeoPoint(BmobObject):
    def __init__(self, latitude, longitude):
        BmobObject.__init__(self, "GeoPoint")
        self.__dict__["latitude"] = latitude
        self.__dict__["longitude"] = longitude


def def_marshal(obj):
    return obj.__dict__


class BmobUpdater:
    @staticmethod
    def add(key, value, data=None):
        if data == None:
            data = {}
        data[key] = value
        return data

    @staticmethod
    def ensuerArray(self, value):
        if isinstance(value, BmobObject):
            value = [value.__dict__]
        elif isinstance(value, dict):
            value = [value]
        elif isinstance(value, list) or isinstance(value, tuple):
            objs = []
            for i in range(0, len(value)):
                obj = value[i]
                if isinstance(obj, BmobObject):
                    obj = obj.__dict__
                objs.append(obj)
            value = objs
        else:
            value = [value]
        return value

    @staticmethod
    def increment(key, number, data=None):
        return BmobUpdater.add(key, {"__op": "Increment", "amount": number}, data)

    @staticmethod
    def arrayAdd(key, value, data=None):
        return BmobUpdater.add(key, {"__op": "Add", "objects": BmobUpdater.ensuerArray(value)}, data)

    @staticmethod
    def arrayAddUnique(key, value, data=None):
        return BmobUpdater.add(key, {"__op": "AddUnique", "objects": BmobUpdater.ensuerArray(value)}, data)

    @staticmethod
    def arrayRemove(key, value, data=None):
        return BmobUpdater.add(key, {"__op": "Remove", "objects": BmobUpdater.ensuerArray(value)}, data)

    @staticmethod
    def addRelations(key, value, data=None):
        return BmobUpdater.add(key, {"__op": "AddRelation", "objects": BmobUpdater.ensuerArray(value)}, data)

    @staticmethod
    def removeRelations(key, value, data=None):
        return BmobUpdater.add(key, {"__op": "RemoveRelation", "objects": BmobUpdater.ensuerArray(value)}, data)


class BmobQuerier:
    def __init__(self):
        self.filter = {}

    # 基础
    def putWhereFilter(self, key, value=None, oper=None):
        if key == None or len(key) == 0 or value == None:
            return self
        if isinstance(value, BmobObject):
            value = value.__dict__
        if oper == None:
            self.filter[key] = value
        else:
            self.filter[key] = {oper: value}
        return self

    def addWhereEqualTo(self, key, value=None):
        if value == None:
            return self.addWhereNotExists(key)
        else:
            return self.putWhereFilter(key, value)

    def addWhereNotEqualTo(self, key, value=None):
        if value == None:
            return self.addWhereExists(key)
        else:
            return self.putWhereFilter(key, value, "$ne")

    # 比较
    def addWhereGreaterThan(self, key, value):
        return self.putWhereFilter(key, value, "$gt")

    def addWhereGreaterThanOrEqualTo(self, key, value):
        return self.putWhereFilter(key, value, "$gte")

    def addWhereLessThan(self, key, value):
        return self.putWhereFilter(key, value, "$lt")

    def addWhereLessThanOrEqualTo(self, key, value):
        return self.putWhereFilter(key, value, "$lte")

    # 关联
    def addWhereRelatedTo(self, table, objectId, key):
        return self.putWhereFilter(key, {"key": key,
                                         "object": {"__type": "Pointer", "className": table, "objectId": objectId}},
                                   "$relatedTo")

    # 存在
    def addWhereExists(self, key, exists=True):
        return self.putWhereFilter(key, exists, "$exists")

    def addWhereNotExists(self, key):
        return self.addWhereExists(key, False)

    # 地理位置
    def addWhereNear(self, key, bmobGeoPointer, maxMiles=None, maxKM=None, maxRadians=None):
        near = {"$nearSphere": bmobGeoPointer.__dict__}
        if maxMiles != None:
            near["$maxDistanceInMiles"] = maxMiles
        if maxKM != None:
            near["$maxDistanceInKilometers"] = maxKM
        if maxRadians != None:
            near["$maxDistanceInRadians"] = maxRadians
        return self.putWhereFilter(key, near)

    def addWhereWithinGeoBox(self, southwest, northeast):
        return self.putWhereFilter(key, {"$box": [southwest.__dict__, northeast.__dict__]}, "$within")

    # 列表
    def addWhereContainedIn(self, key, value, isIn=True):
        if isIn:
            isIn = "$in"
        else:
            isIn = "$nin"
        return self.putWhereFilter(key, value, isIn)

    def addWhereNotContainedIn(self, key, value):
        return self.addWhereContainedIn(key, value, False)

    def addWhereContainsAll(self, key, value):
        return self.putWhereFilter(key, value, "$all")

    # 模糊查询
    def addWhereStrContains(self, key, value):
        return self.putWhereFilter(key, value, "$regex")

    # 子查询
    def addWhereMatchesSelect(self, key, innerQuery, innerKey, innerTable=None, isMatch=True):
        if isMatch:
            isMatch = "$select"
        else:
            isMatch = "$dontSelect"
        if isinstance(innerQuery, BmobQuerier):
            innerQuery = {"className": innerTable, "where": innerQuery.filter}
        return self.putWhereFilter(key, {"key": innerKey, "query": innerQuery}, isMatch)

    def addWhereInQuery(self, key, value, className=None, isIn=True):
        if isIn:
            isIn = "$inQuery"
        else:
            isIn = "$notInQuery"
        if isinstance(value, BmobQuerier):
            innerQuery = {"className": className, "where": value.filter}
        return self.putWhereFilter(key, value, isIn)


class HttpResponse:
    def __init__(self, code, status, headers, data, error=None):
        if code == None:
            code = -100
        if status == None:
            status = 'Unknown Error'
        if headers == None:
            headers = {}
        if data == None:
            data = ''
        self.code = code
        self.status = status
        self.headers = headers
        self.stringData = data
        self.err = error
        try:
            self.jsonData = json.loads(data)
            if 'results' in self.jsonData:
                self.queryResults = self.jsonData["results"]
            else:
                self.queryResults = None
            if 'count' in self.jsonData:
                self.statCount = self.jsonData["count"]
            else:
                self.statCount = 0
        except:
            self.jsonData = {}
            self.queryResults = None
            self.statCount = 0

    def updatedAt(self):
        if "updatedAt" in self.jsonData:
            return self.jsonData["updatedAt"]
        else:
            return None

    def createdAt(self):
        if "createdAt" in self.jsonData:
            return self.jsonData["createdAt"]
        else:
            return None

    def objectId(self):
        if "objectId" in self.jsonData:
            return self.jsonData["objectId"]
        else:
            return None

    def msg(self):
        if "msg" in self.jsonData:
            return self.jsonData["msg"]
        else:
            return None


def httpRequest(url, method='GET', headers=None, body=None, timeout=10):
    if headers == None:
        headers = {}
    if body != None:
        body = body.encode("utf-8")
    req = import_urllib.Request(url=url, data=body, headers=headers)
    if method != None:
        req.get_method = lambda: method
    try:
        res = import_urllib.urlopen(req, timeout=timeout)
        return HttpResponse(res.code, res.msg, res.headers, res.read())
    except import_urllib.URLError as e:
        try:
            if hasattr(e, "reason"):
                reason = e.reason
            else:
                reason = None
            return HttpResponse(e.code, e.msg, e.headers, e.read(), reason)
        except Exception as e:
            print("Req failed wih response.init:", e)
            errMsg = "Unknown Error"
            return HttpResponse(-3, errMsg, {}, errMsg, repr(e))
    else:
        errMsg = "Unknown Error"
        return HttpResponse(-4, errMsg, {}, errMsg, errMsg)


class Bmob:
    def __init__(self, appid, restkey):
        self.domain = 'https://api2.bmob.cn'
        self.headers = {"X-Bmob-Application-Id": appid, "X-Bmob-REST-API-Key": restkey,
                        "Content-Type": "application/json"}
        self.appid = appid
        self.restkey = restkey

    def setUserSession(self, sessionToken):
        self.headers["X-Bmob-Session-Token"] = sessionToken
        return self

    def setMasterKey(self, masterKey):
        self.headers["X-Bmob-Master-Key"] = masterKey
        return self

    # About user start
    def userSignUp(self, userInfo):
        return httpRequest(url=self.domain + '/1/users', method='POST', headers=self.headers,
                           body=json.dumps(userInfo, default=def_marshal))

    def userLogin(self, username, password):
        return httpRequest(url=self.domain + '/1/login?username=' + quote(username) + '&password=' + quote(password),
                           method='GET', headers=self.headers)

    def userLoginBySMS(self, mobile, smsCode, userInfo):
        userInfo["mobilePhoneNumber"] = mobile
        userInfo["smsCode"] = smsCode
        return self.userSignUp(userInfo)

    def userResetPasswordByEmail(self, email):
        return httpRequest(url=self.domain + '/1/requestPasswordReset', method='POST', headers=self.headers,
                           body=json.dumps({"email": email}))

    def userResetPasswordBySMS(self, smsCode, password):
        return httpRequest(url=self.domain + '/1/resetPasswordBySmsCode/' + smsCode, method='PUT', headers=self.headers,
                           body=json.dumps({"password": password}))

    def userResetPasswordByPWD(self, userId, session, oldPassword, newPassword):
        return httpRequest(url=self.domain + '/1/updateUserPassword/' + userId, method='PUT', headers=self.headers,
                           body=json.dumps({"oldPassword": oldPassword, "newPassword": newPassword}))

    # About user over

    def sendCustomSMS(self, mobile, content):
        return httpRequest(url=self.domain + '/1/requestSms', method='POST', headers=self.headers,
                           body=json.dumps({'mobilePhoneNumber': mobile, 'content': content}))

    def sendSMSCode(self, mobile, template):
        return httpRequest(url=self.domain + '/1/requestSmsCode', method='POST', headers=self.headers,
                           body=json.dumps({'mobilePhoneNumber': mobile, 'template': template}))

    def verifySMSCode(self, mobile, smsCode):
        return httpRequest(url=self.domain + '/1/verifySmsCode/' + smsCode, method='POST', headers=self.headers,
                           body=json.dumps({'mobilePhoneNumber': mobile}))

    def payQuery(self, orderId):
        return httpRequest(url=self.domain + '/1/pay/' + orderId, method='GET', headers=self.headers)

    def cloudCode(self, funcName, body=None):
        if body == None:
            body = {}
        return httpRequest(url=self.domain + '/1/functions/' + funcName, method='POST', headers=self.headers,
                           body=json.dumps(body, default=def_marshal))

    def getDBTime(self):
        return httpRequest(url=self.domain + '/1/timestamp/', method='GET', headers=self.headers)

    def batch(self, requests, isTransaction=None):
        if isTransaction == None or isTransaction == False or isTransaction == 0:
            isTransaction = ''
        else:
            isTransaction = '?isTransaction=1'
        return httpRequest(url=self.domain + '/1/batch' + isTransaction, method='POST', headers=self.headers,
                           body=json.dumps(requests, default=def_marshal))

    def insert(self, className, data):
        if isinstance(data, dict):
            for k, v in data.items():
                if (isinstance(v, BmobObject)):
                    data[k] = v.__dict__
        return httpRequest(url=self.domain + '/1/classes/' + className, method='POST', headers=self.headers,
                           body=json.dumps(data, default=def_marshal))

    def update(self, className, objectId, data):
        if isinstance(data, dict):
            for k, v in data.items():
                if (isinstance(v, BmobObject)):
                    data[k] = v.__dict__
        return httpRequest(url=self.domain + '/1/classes/' + className + '/' + objectId, method='PUT',
                           headers=self.headers, body=json.dumps(data, default=def_marshal))

    def remove(self, className, objectId):
        return httpRequest(url=self.domain + '/1/classes/' + className + '/' + objectId, method='DELETE',
                           headers=self.headers)

    def find(self, table, where=None, limit=None, skip=None, order=None, include=None, keys=None, count=None,
             groupby=None, groupcount=None, min=None, max=None, sum=None, average=None, having=None, objectId=None):
        try:
            url = self.domain + '/1/classes/' + table
            if objectId != None:
                url += '/' + objectId
            else:
                params = ''
                if limit != None:
                    params += '&limit=' + str(limit)
                if skip != None:
                    params += '&skip=' + str(skip)
                if count != None:
                    params += '&count=' + str(count)
                if groupby != None:
                    params += '&groupby=' + quote(groupby)
                if groupcount != None and (groupcount == True or groupcount == 1):
                    params += '&groupcount=true'
                if sum != None:
                    params += '&sum=' + quote(sum)
                if average != None:
                    params += '&average=' + str(average)
                if max != None:
                    params += '&max=' + str(max)
                if min != None:
                    params += '&min=' + str(min)
                if having != None:
                    params += '&having=' + str(having)
                if order != None:
                    params += '&order=' + str(order)
                if keys != None:
                    params += '&keys=' + str(keys)
                if include != None:
                    params += '&include=' + str(include)
                if where != None:
                    if isinstance(where, BmobQuerier):
                        where = where.filter
                    params += '&where=' + quote(json.dumps(where, default=def_marshal))
                if len(params) != 0:
                    url += '?' + params[1:]
            return httpRequest(url=url, method='GET', headers=self.headers)
        except Exception as e:
            print(repr(e))
            msg = 'Bad Query'
            return HttpResponse(-1, msg, None, msg, msg)

    def findOne(self, className, objectId):
        return httpRequest(url=self.domain + '/1/classes/' + className + '/' + objectId, method='GET',
                           headers=self.headers)
