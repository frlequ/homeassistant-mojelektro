import requests
import logging
from datetime import datetime, timedelta
import os
import re

_LOGGER = logging.getLogger(__name__)
DIR = os.path.dirname(os.path.realpath(__file__))

class MojElektroApi:

    username = None
    password = None
    meter_id = None

    session = requests.Session()
    csrf = None
    token = None

    cache = None
    cacheDate = None

    def __init__(self, username, password, meter_id): 
        self.username = username
        self.password = password
        self.meter_id = meter_id

    def updateOauthToken(self):
        if self.isTokenValid():
            _LOGGER.debug("Token is valid")
            return

        try:
            self.initRekonoSession()
            self.rekonoLogin()
            self.confirmWithCert()
        except Exception as err_msg:
            _LOGGER.error("Error! %s", err_msg)
            raise

    def initRekonoSession(self):
        response = self.session.get("https://idp.rekono.si/openid-connect-server-webapp/authorize?response_type=code&client_id=SEDMPWEB&state=&redirect_uri=https%3A%2F%2Fmojelektro.si&scope=address%20phone%20openid%20profile%20email%20http%3A%2F%2Fidp.rekono.si%2Fopenid%2Ftaxnumber")

        assert response.status_code == 200

        _LOGGER.debug("JSession: " + self.session.cookies.get('JSESSIONID', path='/IdP-RM-Front'))
        _LOGGER.debug("Init redirect url: " + response.url)

        csrfSearch = re.search(r'_csrf.*value=\"([a-z0-9\-]*)\"', response.text)

        self.csrf = csrfSearch.group(1)
    
    def rekonoLogin(self):        
        payload = {"_csrf": self.csrf, "doaction": "doaction", "username": self.username, "password": self.password}

        response = self.session.post('https://idp.rekono.si/IdP-RM-Front/chooselogin/rekono.htm', data=payload)

        assert response.status_code == 200

    def confirmWithCert(self):
        payload = {"_csrf": self.csrf, "mode": "certlogin"}
        response = self.session.post('https://idp.rekono.si/IdP-RM-Front/chooselogin/options.htm', 
            allow_redirects=False,
            data=payload
        )
        assert response.status_code == 302


        certRes = requests.Session().get('https://idp.rekono.si/IdP-RM-Front/certlogin.htm', 
            cert=(DIR + '/crt.pem', DIR + '/key.pem'), 
            cookies = {'JSESSIONID': self.session.cookies.get('JSESSIONID', path='/IdP-RM-Front')}
        )

        assert certRes.status_code == 200
        token = re.search(r'token.*value=\"([a-z0-9\-]*)\"', certRes.text).group(1)
        
        
        response = self.session.get('https://idp.rekono.si/openid-connect-server-webapp/callback?token=' + token)
        
        assert response.status_code == 200

        #https://mojelektro.si?code=PKaKA6uPOpEU7Xryrx8255sGP83Hv3fG&state=
        code = re.search(r'code\=(.*?)&', response.url).group(1)


        payload = {
            "grant_type":"authorization_code",
            "code": code, 
            "redirect_uri": "https://mojelektro.si",
            "client_id": "SEDMPWEB",
            "client_secret": "deacJn54-nQsjmfTvQ5As5odBs51docg8NUc6KxL4iSDhoOMIqv25BhP3xM8vlLidjfKr6bsTj9j12M3dJ2wuw"
        }

        response = self.session.post('https://idp.rekono.si/openid-connect-server-webapp/token', data=payload)
        assert response.status_code == 200
        
        self.token = response.json()['access_token']
        _LOGGER.debug("Generted token: " + self.token)


    def get15MinIntervalData(self):
        self.updateOauthToken()

        dateFrom = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%dT23:59:00")
        dateTo = datetime.now().strftime("%Y-%m-%dT00:00:00")

        _LOGGER.debug("15min interval request range: " + dateFrom + " - " + dateTo)
        
        r=requests.get(f'https://api.mojelektro.si/NmcApiStoritve/nmc/v1/merilnamesta/{self.meter_id}/odbirki/15min', 
            headers={"authorization": ("Bearer " + self.token)},
            params={"datumCasOd": dateFrom, "datumCasDo": dateTo, "flat": "true"}
        )
        assert r.json()['success'] == True

        # [{'datum': '2021-02-24T09:30:00+01:00', 'A+': 0, 'A-': 0.825},... ]

        return r.json()['data']

    def getMeterData(self):
        self.updateOauthToken()

        dateFrom = (datetime.now()).strftime("%Y-%m-%dT00:00:00")
        dateTo = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00")

        _LOGGER.debug("Meter state request range: " + dateFrom + " - " + dateTo)
        
        r=requests.get(f'https://api.mojelektro.si/NmcApiStoritve/nmc/v1/merilnamesta/{self.meter_id}/odbirki/dnevnaStanja', 
            headers={"authorization": ("Bearer " + self.token)},
            params={"datumCasOd": dateFrom, "datumCasDo": dateTo, "flat": "true"}
        )
        assert r.json()['success'] == True

        # [{ "datum": "2021-02-28T00:00:00+01:00", 
        # "PREJETA DELOVNA ENERGIJA ET": 2562, "PREJETA DELOVNA ENERGIJA VT": 1072, "PREJETA DELOVNA ENERGIJA MT": 1490, 
        # "ODDANA DELOVNA ENERGIJA ET": 588, "ODDANA DELOVNA ENERGIJA VT": 410, "ODDANA DELOVNA ENERGIJA MT": 178 },... ]

        return r.json()['data']


    def getDailyData(self):
        self.updateOauthToken()

        dateFrom = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00")
        dateTo = datetime.now().strftime("%Y-%m-%dT00:00:00")

        _LOGGER.debug("Daily state request range: " + dateFrom + " - " + dateTo)

        r=requests.get(f'https://api.mojelektro.si/NmcApiStoritve/nmc/v1/merilnamesta/{self.meter_id}/odbirki/dnevnaPoraba', 
            headers={"authorization": ("Bearer " + self.token)},
            params={"datumCasOd": dateFrom, "datumCasDo": dateTo, "flat": "true"}
        )

        assert r.json()['success'] == True

        # [{"datum":"2021-02-26T00:00:00+01:00",
        # "PREJETA DELOVNA ENERGIJA ET":14.94,"PREJETA DELOVNA ENERGIJA VT":8.47,"PREJETA DELOVNA ENERGIJA MT":6.47,
        # "ODDANA DELOVNA ENERGIJA ET":28.56,"ODDANA DELOVNA ENERGIJA VT":28.56,"ODDANA DELOVNA ENERGIJA MT":0.00}, ...]

        return r.json()['data']
    

    def getData(self):
        cache = self.getCache()

        dMeter = cache.get("meter")[0]
        dDaily = cache.get("daily")[0]
        d15 = cache.get("15")[self.get15MinOffset()]

        return {
            "15min_input": d15['A+'], 
            "15min_output": d15['A-'],

            "meter_input": dMeter['PREJETA DELOVNA ENERGIJA ET'],
            "meter_input_peak": dMeter['PREJETA DELOVNA ENERGIJA VT'],
            "meter_input_offpeak": dMeter['PREJETA DELOVNA ENERGIJA MT'],
            "meter_output": dMeter['ODDANA DELOVNA ENERGIJA ET'],
            "meter_output_peak": dMeter['ODDANA DELOVNA ENERGIJA VT'],
            "meter_output_offpeak": dMeter['ODDANA DELOVNA ENERGIJA MT'],

            "daily_input": dDaily['PREJETA DELOVNA ENERGIJA ET'],
            "daily_input_peak": dDaily['PREJETA DELOVNA ENERGIJA VT'],
            "daily_input_offpeak": dDaily['PREJETA DELOVNA ENERGIJA MT'],
            "daily_output": dDaily['ODDANA DELOVNA ENERGIJA ET'],
            "daily_output_peak": dDaily['ODDANA DELOVNA ENERGIJA VT'],
            "daily_output_offpeak": dDaily['ODDANA DELOVNA ENERGIJA MT']
        }

    def getCache(self):
        _LOGGER.debug("Rerfresing cache")
        
        if self.cache is None or self.cacheDate != datetime.today().date():
            self.cache = {
                "meter": self.getMeterData(), 
                "daily": self.getDailyData(),
                "15" : self.get15MinIntervalData()
            }
            self.cacheDate = datetime.today().date()

        return self.cache

    def get15MinOffset(self):
        now = datetime.now()

        return int((now.hour * 60 + now.minute)/15) 


    def isTokenValid(self):
        if self.token is None:
            return False

        #TODO: validate JWT token
        r = requests.get("https://api.mojelektro.si/NmcApiStoritve/nmc/v1/user/info", 
            headers={"authorization":"Bearer " + self.token})
        
        _LOGGER.debug(f'Validation response {r.status_code}')

        return r.status_code != 401
        