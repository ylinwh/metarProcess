import re
import numpy as np
import pandas as pd
import os

## full time
FULLTIME_RE = re.compile(r"""\s*(?P<year>\d{4})
                               (?P<month>\d{2})
                               (?P<day>\d{2})
                               (?P<hour>\d{2})
                               (?P<minute>\d{2})\s*
                        """,
                         re.VERBOSE)

def _handle_fulltime(identif, d):
    """
    Parse the full time 
    """
    if not d:
        return "", ""
    translation = f"{d['year']}-{d['month']}-{d['day']} {d['hour']}:{d['minute']}"
    return  translation, d.end()
## type
TYPE_RE = re.compile(r"""\s*(?P<type>(METAR)|(SPECI)|(TAF))\s*    
                        """,
                         re.VERBOSE)

def _handle_type(identif, d):
    """
    Parse the message type 
    """
    if not d:
        return "", ""
    translation = f"{d['type']}"
    return translation, d.end()

## icao code
ICAO_RE = re.compile(r"""\s*(COR\s)?(?P<icao>\w{4})\s*    
                        """,
                         re.VERBOSE)

def _handle_icao(identif, d):
    """
    Parse the icao identifier 
    """
    if not d:
        return "", ""
    translation = f"{d['icao']}"
    return translation, d.end()
## issuance time
ISSUANCE_TIME_RE = re.compile(r"""\s*(?P<day>\d{2})
                                    (?P<hour>\d{2})
                                    (?P<minute>\d{2})Z\s*    
                        """,
                         re.VERBOSE)

def _handle_issuance_time(identif, d):
    """
    Parse the icao identifier 
    """
    if not d:
        return "", ""
    translation = f"{d['day']}th {d['hour']}:{d['minute']}"
    return translation, d.end()

## wind (wind direction; speed; gust; unit)
WIND_RE = re.compile(r"""\s*(?P<dir>[\d]{3}|VRB)
                    (?P<speed>[\d]{2})
                    (G(?P<gust>[\d]{2})){0,1}
                    (?P<unit>KT|MPS)\s*""",        # KT/MPS have different speed unit
                    re.VERBOSE)

def _handle_wind(identif, d):
    """
    Parse the wind and variable-wind groups.

    The following attributes are set:
        dir:        wind direction 
        speed:      wind speed
        gust:       gust speed  (optional)
        unit:       (1.852 km/h) or (0.51444 m/s) per knot | "MPS" means "meter"
    """
    if not d:
        return "", ""
    direction = d['dir']
    speed = d['speed']
    gust = d['gust'] if d['gust'] else None
    unit = 'knot' if d['unit'] == 'KT' else 'm/s'
    translation = f"direction: {direction}; sustain speed: {speed}; gust: {gust}; unit: {unit}"
    return translation, d.end()

## wind variability
WIND_VARIABILITY_RE = re.compile(r"""\s*(?P<lower>[\d]{3})
                            V
                            (?P<upper>[\d]{3})\s*
                        """,
                        re.VERBOSE)

def _handle_wind_variability(identif, d):
    """
    Parse the wind variability groups.

    The following attributes are set:
        lower direction:        wind direction 
        upper direction:      wind speed
    """
    if not d:
        return "", ""
    lower = d['lower']
    upper = d['upper']
    translation = f"direction varying between: {lower} and {upper} degree"
    return translation, d.end()

## visibility
VISIBILITY_RE = re.compile(r"""\s*((?P<const>[\d]\s)?  (?P<num>[\d]+)  (/(?P<den>[\d]+))? SM)   # statute miles
                            |
                            (?P<meter>([\d][\d][05][0])|([9]{4}))\s*                              # meters
                            """,
                            re.VERBOSE)

def _handle_visibility(identif, d):
    """
    Parse the visibility. (Two standards:  1. with "SM" on the end;   2. 4 decimal numbers.
    The following attributes are set:
            1. constant + numerator / denominator,
            2. 4 decimal numbers.
    """
    if not d:
        return "", ""
    constant = int(d['const']) if d['const'] else 0
    numerator = int(d['num']) if d['num'] else 0
    denominator = int(d['den']) if d['den'] else 1
    meter = d['meter']
    translate = f"{meter} meter" if meter else f"{constant+numerator/denominator} statute mile"
    return translate, d.end()

## runway
RUNWAY_RE = re.compile(r"""\s*(?P<runway>R[\d]+[L|R|C]?)
                        /
                        (   (?P<prefix_low>[M|P]?)(?P<low>[\d]{4})
                                (   (?P<vary>V)
                                    (?P<prefix_high>[M|P]?)(?P<high>[\d]{4})
                                )?
                            (?P<unit>FT)?
                            /?
                            (?P<trend>[NDU]?)       # static, decrease, increase              
                        )\s*
                        """,
                        re.VERBOSE)

def _handle_runway(identif, d):
    """
    Parse the Runway related information. 
    The following attributes are set:
        runway:     runway number
        vary:       flag of "***V***" case
        prefix:     M/P -- less than / greater than
        unit:       "FT" -- ft  / None
    """
    if not d:
        return "", ""
    translate = {'M': 'less than', 'P': 'greater than', 'N': 'static trend', 'D': 'decreasing trend', \
                     'U': 'increasing trend', '': '', None: ''}
    runway = d['runway']
    vary = True if d['vary'] else False
    unit = 'ft' if d['unit'] else 'meter'
    trend = translate[d['trend']]
    prefix_low, prefix_high = translate[d['prefix_low']], translate[d['prefix_high']]
    low, high = d['low'], d['high']
    if vary:
        translate =  f"runway: {runway}; visibility: from {prefix_low} {low}  to {prefix_high} {high}; unit: {unit}; with {trend}"
    else:
        translate =  f"runway: {runway}; visibility: {prefix_low} {low}; unit: {unit}; with {trend}"
    return translate, d.end()
                              
## weather
WEATHER_RE = re.compile(r"""\s*(?P<int>(-|\+)?)
                            (?P<desc>(BC|BL|DR|FZ|MI|PR|SH|TS)?)
                            (?P<prec>(DZ|GR|GS|IC|PL|RA|SG|SN|UP)*)
                            (?P<obsc>BR|DU|FG|FU|HZ|PY|SA|VA)?
                            (?P<other>DS|FC|PO|SQ|SS)?\s*
                        """,
                        re.VERBOSE)

WEATHER_INT = {'-': 'light', '+': 'heavy', '-VC': 'nearby light', '+VC': 'nearby heavy', 'VC': 'nearby', '': '', None: ''}
WEATHER_DESC = { 'BC': 'patches of','BL': 'blowing','DR': 'low drifting','FZ': 'freezing', 'MI': 'shallow', \
                'PR': 'partial', 'SH': 'showers', 'TS': 'thunderstorm', '': '', None: ''}
WEATHER_PREC = {'DZ': 'drizzle', 'GR': 'hail', 'GS': 'snow pellets', 'IC': 'ice crystals','PL': 'ice pellets', \
                'RA': 'rain', 'SG': 'snow grains', 'SN': 'snow',  'UP': 'unknown precipitation', '': '', None: ''}
WEATHER_OBSC = {'BR': 'mist', 'FG': 'fog', 'FU': 'smoke', 'VA': 'volcanic ash', 'DU': 'dust', 'SA': 'sand', \
                'HZ': 'haze', 'PY': 'spray', '': '', None: ''}
WEATHER_OTHER = {'PO': 'san whirls', 'SQ': 'squalls', 'FC': 'funnel cloud', 'SS': 'sandstorm', 'DS': 'dust storm', '': '', None: ''}
# WEATHER_SPECIAL = {'+FC': 'tornado', None: ''}

def _handle_weather(identif, d):
    """
    Parse the weather. 
    The following attributes are set:
            1. intensity
            2. description
            3. precipitation
            4. obscuration
            5. other
    """
    if not d or d.start() == d.end():
        return "", ""
    intensity = WEATHER_INT[d['int']]
    descriptor = WEATHER_DESC[d['desc']]
    # 
    if d['prec']:
        chunks, chunkSize = len(d['prec']), 2
        prec = [ d['prec'][i:i+chunkSize] for i in range(0, chunks, chunkSize)]
    else:
        prec = ""
    precitation = ""
    for p in prec:
        precitation += WEATHER_PREC[p] + ";"
    # precitation = WEATHER_PREC[d['prec']]           # bug, maybe more one precitation.

    obscuration = WEATHER_OBSC[d['obsc']]
    other = WEATHER_OTHER[d['other']]

    translation = f"{intensity} {descriptor} {precitation} {obscuration} {other}"
    return translation.strip(), d.end()

## clouds
CLOUDS_RE = re.compile(r"""\s*(?P<cover>SKC|FEW|SCT|BKN|OVC|VV)
                            (?P<height>[\d]{2,4})\s*
                        """,
                        re.VERBOSE)

CLOUDS_INDI = {'SKC': 'sky clear', 'FEW': 'few', 'SCT': 'scattered', 'BKN': 'broken', 'OVC': 'overcast', 'VV': 'vertical visibility'}

def _handle_clouds(identif, d):
    """
    Parse the clouds. 
    The following attributes are set:
            1. cover:       degree of the clouds
            2. height:      heights
    """
    if not d:
        return "", ""
    prefix = CLOUDS_INDI[d['cover']]
    height = d['height']
    translation = f"{prefix} {height}"
    return translation, d.end()

## temperature
TEMP_RE = re.compile(r"""\s*(?P<minus_f1>M?)(?P<temp>\d{2})
                        /
                        (?P<minus_f2>M?)(?P<dewpoint>\d{2})\s*
                    """,
                    re.VERBOSE)

def _handle_temp(identif, d):
    """
    Parse the temp. It has form like (01/M01)
    The following attributes are set:
            1. minus_f1:      flag for minus sign ("-")
            2. temp:            tempeture
            3. minus_f2:      flag for minus sign ("-")
            3. dewpoint:      dewpoint
    """
    if not d:
        return "", ""
    minus_f1 = -1 if d['minus_f1'] else 1
    minus_f2 = -1 if d['minus_f2'] else 1
    temp = minus_f1 * int(d['temp'])
    dewpoint = minus_f2 * int(d['dewpoint'])

    translation = f"temperature: {temp}; dewpoint: {dewpoint}" 
    return translation, d.end()
## altimeter
ALTIMETER_RE = re.compile(r"""\s*(?P<unit>A|Q)?
                            (?P<press>\d{3,4})\s*
                        """,
                        re.VERBOSE)
def _handle_altimeter(identif, d):
    """
    Parse the temp. It has form like (A2984 / Q1011)
    The following attributes are set:
            1. unit:    A-- inches /  Q-- hPa
            2. press:   pressure number
    """
    if not d:
        return "", ""
    unit = 'inches' if d['unit'] == 'A' else 'hPa'
    press = int(d['press'])

    translation = f"sea level pressure: {press}; unit: {unit}"
    return  translation, d.end()


class metarProcessing(object):

    def __init__(self, fileDir):
        # be careful with the empty fileDir !!!!
        self.fileDir=fileDir
        self.f = None
        self.curRecord = ""

        self.startProg = re.compile(r"\s*\d{12}")
        self.endProg = re.compile(r".*=\s*$")
        self.typeProg = re.compile(r"\sTAF\s")
        
        self.handlers = [ (FULLTIME_RE, _handle_fulltime, 'fulltime', False),
                    (TYPE_RE, _handle_type, 'type', False),
                    (ICAO_RE, _handle_icao, 'icao', False),
                    (ISSUANCE_TIME_RE, _handle_issuance_time, 'issuancetime', False),
                    (WIND_RE, _handle_wind, 'wind', False),
                    (WIND_VARIABILITY_RE, _handle_wind_variability, 'variability', False),
                    (VISIBILITY_RE, _handle_visibility, 'visibility', True),
                    (RUNWAY_RE, _handle_runway, 'runway', True),
                    (WEATHER_RE, _handle_weather, 'weather', True),
                    (CLOUDS_RE, _handle_clouds, 'clouds', True),
                    (TEMP_RE, _handle_temp, 'temp', False),
                    (ALTIMETER_RE, _handle_altimeter, 'altimeter', True)
                    ]
        self.metarReport = {}

    def open(self):
        self.f = open(self.fileDir, 'r')

    def close(self):
        if self.f:
            self.f.close()

    def isRecordStart(self, line):
        """ record start: continuous 12 number
        """
        return True if self.startProg.match(line) else False

    def isRecordEnd(self, line):
        """ assume record ALWAYS ends with "=": 
        """
        return True if self.endProg.match(line) else False

    def isTAFRecord(self, line):
        """ detect TAF record
        """
        return True if self.typeProg.search(line) else False

    def getNextRecord(self):
        """ assume that every metar record starts with "fulltime" and ends with "="
            maybe we should make it more robust.
        """
        self.curRecord = ""
        
        while True:
            line = self.f.readline()
            if self.isRecordStart(line):
                break
            elif line == "" or self.isTAFRecord(line):      # end of the file
                return ""
      
        while True:
            self.curRecord += line
            if self.isRecordEnd(line) or line == "":
                break
            line = self.f.readline()

        return self.curRecord.rstrip('=\n ')

   
    def decodeMetar(self, metarStr):
        """ follow the standar process, indicated by "handler".
        """

        ngroup = len(self.handlers)
        igroup = 0
        message = {}
        pos = 0
        errorMsg = ""
        while igroup < ngroup:
            pattern, handler, identif, repeat = self.handlers[igroup]
            # if repeat, then do multiple times (we also need to consider the exception)
            # if not repeat, then just do one time
            message.setdefault(identif, "")
            while True:
                d = pattern.match(metarStr, pos=pos)
                text, p = handler(identif, d)         # if there is no match..
                if not text:
                    if not message[identif]:
                        # print(f"identif: {identif}| message:  no text matched")
                        errorMsg += f"{identif}:  no text matched;"
                    break
                pos = p
                # print(f'identif : {identif} | message: {text}')
                message[identif] += f'{identif}: {text};'
                if not repeat:
                    break                               # not repeat, only do once.
            # message[identif] = message[identif].rstrip('\n ')
            igroup += 1
        return message, errorMsg
    
    def vmcMinima(self, metarStr):
        """
        VMC minima
        a) when the ceiling is less than 450m (1500 ft); or
        b) when the ground visibility is less than 5 km  (1SM = 1.60934)
        c) False for IMC; True for VMC
        ----------------------------------------------------------------
        "CAVOK" - horizontal visibility of 10000 meters or more and no clouds below 5000 feet.
        """
        # the regex used...
        # _handle_visibility     _handle_clouds
        CAVOK_RE = re.compile(r"""\sCAVOK\s""")
        CEILING_RE = re.compile(r"""\s*(BKN|OVC)
                                (\d{2,4})\s*
                                """,
                                re.VERBOSE)
        VISIBILITY_RE = re.compile(r"""\s((?P<const>[\d]\s)?  (?P<num>[\d]+)  (/(?P<den>[\d]+))? SM)\s   # statute miles
                                |
                                \s(?P<meter>([\d][\d][05][0])|([9]{4}))\s                              # meters
                                """,
                                re.VERBOSE)
        # "CAVOK" code
        if CAVOK_RE.search(metarStr):
            # return True, 9999, "15sm"
            return True
        # ceiling
        ceilingRes = CEILING_RE.findall(metarStr)
        if not ceilingRes:
            ceiling = True
            # ceilingNum = 9999
        else:
            ceilingList = [int(height) for prefix, height in ceilingRes]
            ceiling = True if min(ceilingList) >= 15 else False
            # ceilingNum = min(ceilingList)
        # visibility
        d = VISIBILITY_RE.search(metarStr)
        if d:
            constant = int(d['const']) if d['const'] else 0
            numerator = int(d['num']) if d['num'] else 0
            denominator = int(d['den']) if d['den'] else 1
            meter = int(d['meter']) if d['meter'] else 0
            
            if meter:
                visibility = True if meter >= 5000 else False       # visibility >= 5km
                # visibilityNum = meter
            else:
                visibility = True if (constant + numerator / denominator) >= 3 else False   # visibility >= 3SM
                # visibilityNum = f'{constant + numerator / denominator} sm'
        else:
            visibility = False
        
        return ceiling and visibility

    def decodeVMC(self, metar):
        def handle_time(metar):
            prog = re.compile(r"^\s*(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})(?P<hour>\d{2})(?P<minute>\d{2})\s")
            res = prog.search(metar)
            if not res:
                return None
            return f"{res.group('year')}-{res.group('month')}-{res.group('day')} {res.group('hour')}:{res.group('month')}"
        
        def handle_city(metar):
            prog = re.compile(r"\s(COR\s)?(?P<icao>\w{4})\s")
            res = prog.search(metar)
            if not res:
                return None
            return f"{res.group('icao')}"
        
        def handle_type(metar):
            prog = re.compile(r"\s(?P<type>(METAR)|(SPECI)|(TAF))\s")
            res = prog.search(metar)
            if not res:
                return None
            return f"{res.group('type')}"
        # current time/city/type
        handlers = [handle_time, handle_city, handle_type, self.vmcMinima]
        resList = [None] * 4
        for ind, h in enumerate(handlers):
            resList[ind] = (h(metar))
        return resList

    def decodeFileMetar(self, filename, storeDir='VMC_decoded'):
        self.fileDir = filename
        self.open()
        time, city, repType, VMC = [], [], [], []
        
        while True:
            metar = self.getNextRecord()
            if not metar:
                break
            t, c, r, v = self.decodeVMC(metar)
            time.append(t)
            city.append(c)
            repType.append(r)
            VMC.append(v)

        self.close()
        resDic = {'time': time, 'city': city, 'repType': repType, 'VMC': VMC}
        resDic = pd.DataFrame(resDic)
        # make dir
        try:
            os.mkdir(storeDir)
        except:
            pass
        resDic.to_csv(os.path.join(storeDir, os.path.splitext(filename)[0] + '_VMC.csv'), index=False)


if __name__ == '__main__':
    filedir = '.'
    rawFileList = os.listdir(filedir)
    for rfl in rawFileList:
        if rfl.endswith('.txt'):
            filename = os.path.join(filedir, rfl)
            mp = metarProcessing(filename)
            mp.decodeFileMetar(filename)
