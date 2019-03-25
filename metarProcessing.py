import re

######################################################################################
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
    translation = f"year: {d['year']}| month: {d['month']}| day: {d['day']}| hour:{d['hour']}| minute: {d['minute']}"
    return  translation, d.end()
######################################################################################
TYPE_RE = re.compile(r"""\s*(?P<type>(METAR)|(TAF))\s*    
                        """,
                         re.VERBOSE)

def _handle_type(identif, d):
    """
    Parse the message type 
    """
    if not d:
        return "", ""
    translation = f"type: {d['type']}"
    return translation, d.end()

######################################################################################
ICAO_RE = re.compile(r"""\s*(COR\s)?(?P<icao>\w{4})\s*    
                        """,
                         re.VERBOSE)

def _handle_icao(identif, d):
    """
    Parse the icao identifier 
    """
    if not d:
        return "", ""
    translation = f"icao: {d['icao']}"
    return translation, d.end()
######################################################################################
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
    translation = f"day: {d['day']} | hour: {d['hour']} | minute: {d['minute']}"
    return translation, d.end()
######################################################################################
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
    translation = f"direction: {direction}| sustain speed: {speed}| gust: {gust}| unit: {unit}"
    return translation, d.end()
#########################################################################################
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
    translation = f"direction varying between: {lower}| and: {upper} degree"
    return translation, d.end()
#########################################################################################
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
    translate = f"meter: {meter}" if meter else f"statute mile: {constant+numerator/denominator}"
    return translate, d.end()
#########################################################################################
RUNWAY_RE = re.compile(r"""\s*(?P<runway>R[\d]+[L|R]?)
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
        translate =  f"runway: {runway} | visibility: from {prefix_low} {low}  to {prefix_high} {high}| unit: {unit} | trend: {trend}"
    else:
        translate =  f"runway: {runway} | visibility: {prefix_low} {low} | unit: {unit} | trend: {trend}"
    return translate, d.end()
                              
#########################################################################################
WEATHER_RE = re.compile(r"""\s*(?P<int>(-|\+)?)
                            (?P<desc>(BC|BL|DR|FZ|MI|PR|SH|TS)?)
                            (?P<prec>(DZ|GR|GS|IC|PL|RA|SG|SN|UP)*)
                            (?P<obsc>BR|DU|FG|FU|HZ|PY|SA|VA)?
                            (?P<other>DS|FC|PO|SQ|SS)?\s*
                        """,
                        re.VERBOSE)

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
    ########################################################
    # TODO: there may be more than one weather description.#
    ########################################################
    if not d or d.start() == d.end():
        return "", ""
    WEATHER_INT = {'-': 'light', '+': 'heavy', '-VC': 'nearby light', '+VC': 'nearby heavy', 'VC': 'nearby', '': '', None: ''}
    WEATHER_DESC = { 'BC': 'patches of','BL': 'blowing','DR': 'low drifting','FZ': 'freezing', 'MI': 'shallow', \
                    'PR': 'partial', 'SH': 'showers', 'TS': 'thunderstorm', '': '', None: ''}
    WEATHER_PREC = {'DZ': 'drizzle', 'GR': 'hail', 'GS': 'snow pellets', 'IC': 'ice crystals','PL': 'ice pellets', \
                    'RA': 'rain', 'SG': 'snow grains', 'SN': 'snow',  'UP': 'unknown precipitation', '': '', None: ''}
    WEATHER_OBSC = {'BR': 'mist', 'FG': 'fog', 'FU': 'smoke', 'VA': 'volcanic ash', 'DU': 'dust', 'SA': 'sand', \
                    'HZ': 'haze', 'PY': 'spray', '': '', None: ''}
    WEATHER_OTHER = {'PO': 'san whirls', 'SQ': 'squalls', 'FC': 'funnel cloud', 'SS': 'sandstorm', 'DS': 'dust storm', '': '', None: ''}
    # WEATHER_SPECIAL = {'+FC': 'tornado', None: ''}
    intensity = WEATHER_INT[d['int']]
    descriptor = WEATHER_DESC[d['desc']]
    precitation = WEATHER_PREC[d['prec']]
    obscuration = WEATHER_OBSC[d['obsc']]
    other = WEATHER_OTHER[d['other']]

    translation = f"{intensity} {descriptor} {precitation} {obscuration} {other}"
    return translation, d.end()
#########################################################################################
CLOUDS_RE = re.compile(r"""\s*(?P<cover>SKC|FEW|SCT|BKN|OVC|VV)
                            (?P<height>[\d]{2,4})\s*
                        """,
                        re.VERBOSE)

def _handle_clouds(identif, d):
    """
    Parse the clouds. 
    The following attributes are set:
            1. cover:       degree of the clouds
            2. height:      heights
    """
    ########################################################
    # TODO: there may be more than one clouds description. #
    ########################################################
    if not d:
        return "", ""
    CLOUDS_INDI = {'SKC': 'sky clear', 'FEW': 'few', 'SCT': 'scattered', 'BKN': 'broken', 'OVC': 'overcast'}
    prefix = CLOUDS_INDI[d['cover']]
    height = d['height']
    translation = f"{prefix} {height}"
    return translation, d.end()

#########################################################################################
TEMP_RE = re.compile(r"""\s*(?P<minus_f1>M?)(?P<temp>\d{2})
                        /
                        (?P<dew_temp>M?)(?P<dewpoint>\d{2})\s*
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

    translation = f"temperature: {temp} | dewpoint: {dewpoint}" 
    return translation, d.end()
#########################################################################################
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

    translation = f"sea level pressure: {press} | unit: {unit}"
    return  translation, d.end()
#########################################################################################

# a list of handler function to use (in order to process a METAR report)
# handlers = [ (FULLTIME_RE, _handle_fulltime, 'fulltime', False),
#              (TYPE_RE, _handle_type, 'type', False),
#              (ICAO_RE, _handle_icao, 'icao', False),
#              (ISSUANCE_TIME_RE, _handle_issuance_time, 'issuancetime', False),
#              (WIND_RE, _handle_wind, 'wind', False),
#              (WIND_VARIABILITY_RE, _handle_wind_variability, 'variability', False),
#              (VISIBILITY_RE, _handle_visibility, 'visibility', True),
#              (RUNWAY_RE, _handle_runway, 'runway', True),
#              (WEATHER_RE, _handle_weather, 'weather', True),
#              (CLOUDS_RE, _handle_clouds, 'clouds', True),
#              (TEMP_RE, _handle_temp, 'temp', False),
#              (ALTIMETER_RE, _handle_altimeter, 'altimeter', True)
#             ]


def decode_mini(metarStr):
    handlers = [ (FULLTIME_RE, _handle_fulltime, 'fulltime', False),
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
    ngroup = len(handlers)
    igroup = 0
    message = {}
    pos = 0
    errorMsg = ""
    while igroup < ngroup:
        pattern, handler, identif, repeat = handlers[igroup]
        # if repeat, then do multiple times (we also need to consider the exception)
        # if not repeat, then just do one time
        while True:
            d = pattern.match(metarStr, pos=pos)
            text, p = handler(identif, d)         # if there is no match..
            if not text:
                print(f"identif: {identif};  no text matched")
                break
            pos = p
            print(f'identif : {identif} | text: {text}')
            if not repeat:
                break                               # not repeat, only do once.
        igroup += 1
        

if __name__ == '__main__':
    metarStr = "201707310300 METAR ZPPP 310300Z 26002MPS 200V300 5000 BR SCT023 Q1010"
    decode_mini(metarStr)

def decodeMetar(metarStr):
    """ Aviation Routine Weather Report (METAR)
        1. time (YYYYMMDDHHMM) 
        2. message type
        3. ICAO identifier (4-letter)
        4. Issuance Time (DDHHMMz  (UTC))
        5. Wind
        6. Horizontal Visibility
        7. Present weather
        8. Sky Cover
        9. Altimeter setting 
    """
    # ngroup = len(handlers)
    # igroup = 0
    # content = ['time', 'type', 'icao', 'issuance time', 'wind', 'visibility', 'weather', 'sky', 'altimeter']
    # message = {}
    # for c in content:
    #     message[c] = ''
    # while igroup < ngroup:
    #     pattern, handler, identif, repeat = handlers[igroup]
    #     res = handler('test', pattern, 0)
    return ""




class metarData(object):
    def __init__(self):
        self.reportType = 'METAR'
        self.location = None
        self.dateTime = None
        self.wind = None
        self.windVariability = None
        self.visibility = None
        self.runwayVisualRange = None
        self.typeWeather = None
        self.clouds = None
        self.temperature = None
        self.altimeter = None
        self.remarks = None



class metarProcessing(object):

    def __init__(self, fileDir):
        self.f = open(fileDir, 'r')
        self.curRecord = ""
        self.nexRecord = ""

        self.startProg = re.compile(r"^\s*\d{12}")
        self.endProg = re.compile(r".*=\s*$")

    def close(self):
        self.f.close()

    def isRecordStart(self, line):
        """ record start: continuous 12 number
        """
        return True if self.startProg.match(line) else False

    def isRecordEnd(self, line):
        """ record ends: 
            1. end with a "="
        """
        return True if self.endProg.match(line) else False


    def getNextRecord(self):
        #########################################################
        #  TODO:                                                #
        #   1. currently, I assume record must end with "=".    #
        #      maybe I should consider more situations...       #
        #   2. Do I have to use curRecord & nexRecord ??        #
        #      it seems very complicated..                      #
        #                                                       #
        #########################################################

        self.curRecord = self.nexRecord

        line = self.f.readline()
        while not self.isRecordStart(line):
            line = self.f.readline()
            # the end of the file
            if line == "":
                self.f.close()
                return None
        
        # start of the record
        self.curRecord = self.curRecord + line
        if self.isRecordEnd(line):
            self.nexRecord = ""
            return self.curRecord
        
        # need to find the end of record
        line = self.f.readline()
        while not self.isRecordEnd(line):        
            self.curRecord += line
            line = self.f.readline()
        self.curRecord += line
        self.nexRecord = ""
        return self.curRecord

    
    def getMetarList(self, metarStr):
        return re.split(r'\s+', metarStr.strip().rstrip('='))

    
    def decode(self, metarList):
        #########################################################
        #  TODO:                                                #
        #   1. design a decode table,                           #
        #       translate codes in metarList                    #
        #   2. maybe it shoudl return a dict like               #
        #       {'weather': ****, 'wind': ****, }               #
        #                                                       #
        #########################################################
        metar = metarData()
        time = metarList[0]
        reportType = metarList[1]

        # regrex for wind  (data group followed by KT(knots))
        # 25015G30KT
        wind = None
