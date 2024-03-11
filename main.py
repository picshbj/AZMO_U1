import json
import websockets
import asyncio
import os
import datetime
import random
import time 
import shutil
import requests
import subprocess
        
RELAY1_PIN = 17
RELAY2_PIN = 27
RELAY3_PIN = 22
RELAY4_PIN = 18
RELAY5_PIN = 25
RELAY6_PIN = 8
RELAY7_PIN = 12
RELAY8_PIN = 13
DIP1_PIN_2 = 19
DIP2_PIN_1 = 16
DIP3_PIN_4 = 26
DIP4_PIN_3 = 20
COMM_EN_PIN = 23

global Channel, CO2, TVOC, PM25, TEMP, HUMID, LIGHT, WATER1, WATER2, WATER3, RELAYS_PARAM, SERVER_STATUS, SENSOR_STATUS, SERIAL_WATCHDOG, Manual_Relay_Info, Relay_Pins, isReadyToSend, ERRORCOUNT, TGBOT, msgToSend, RECIEVE_WATCHDOG, comm
Channel = CO2 = TVOC = PM25 = TEMP = HUMID = LIGHT = WATER1 = WATER2 = WATER3 = ERRORCOUNT = TGBOT = RECIEVE_WATCHDOG = 0
SERVER_STATUS = True
SENSOR_STATUS = False
isReadyToSend = False
SERIAL_WATCHDOG = 0
Manual_Relay_Info = [[False, 0],[False, 0],[False, 0],[False, 0],[False, 0],[False, 0],[False, 0],[False, 0]]
Relay_Pins = []
msgToSend = ''
comm = 'S00000000\n'

VERSION = '4.0U'

IS_PI = True

if IS_PI:
    import RPi.GPIO as GPIO

    while True:
        try:
            import serial_asyncio
            print('serial_asyncio import succeed!')
            break
        except Exception as e:
            print('This system has no serial_asyncio module..')
            print('Installing serial_asyncio module..')
            os.system('pip3 install pyserial-asyncio')
            time.sleep(5)
            
    while True:
        try:
            import pyautogui
            print('pyautogui import succeed!')
            break
        except Exception as e:
            print('This system has no pyautogui module..')
            print('Installing pyautogui module..')
            os.system('pip3 install pyautogui')
            time.sleep(5)
            
    while True:
        try:
            import telegram
            print('telegram import succeed!')
            TGBOT = telegram.Bot(token='6725689755:AAFecGY3ty3wheg44lR8d-6hO7LIuhAfiao')
            chat_id = 5391813621
            break
        except Exception as e:
            print('This system has no telegram module..')
            print('Installing telegram module..')
            os.system('pip3 install python-telegram-bot')
            time.sleep(5)

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RELAY1_PIN, GPIO.OUT)
    GPIO.setup(RELAY2_PIN, GPIO.OUT)
    GPIO.setup(RELAY3_PIN, GPIO.OUT)
    GPIO.setup(RELAY4_PIN, GPIO.OUT)
    GPIO.setup(RELAY5_PIN, GPIO.OUT)
    GPIO.setup(RELAY6_PIN, GPIO.OUT)
    GPIO.setup(RELAY7_PIN, GPIO.OUT)
    GPIO.setup(RELAY8_PIN, GPIO.OUT)
    GPIO.setup(COMM_EN_PIN, GPIO.OUT)
    GPIO.setup(DIP1_PIN_2, GPIO.IN)
    GPIO.setup(DIP2_PIN_1, GPIO.IN)
    GPIO.setup(DIP3_PIN_4, GPIO.IN)
    GPIO.setup(DIP4_PIN_3, GPIO.IN)
    
    GPIO.output(COMM_EN_PIN, True)

    Relay_Pins = [RELAY1_PIN, RELAY2_PIN, RELAY3_PIN, RELAY4_PIN, RELAY5_PIN, RELAY6_PIN, RELAY7_PIN, RELAY8_PIN]

    f = open('/home/pi/Desktop/settings.txt', 'r')
    setting_id = ''
    for line in f:
        d = line.split(':')
        if d[0] == 'DEVICE_ID':
            setting_id = d[1]
            setting_id = setting_id.replace(' ', '')
            setting_id = setting_id.replace('\n', '')
    f.close()

    uri = 'wss://admin.azmo.kr/azmo_ws?%s' % (setting_id)

    f = open('/etc/xdg/lxsession/LXDE-pi/autostart','r')
    data = ''
    isChanged = False
    for line in f:
        if 'atmo' in line:
            line = line.replace('atmo', 'azmo')
            isChanged = True
        if 'v3' in line:
            line = line.replace('v3', 'v1')
            isChanged = True

        if 'azmo' in line:
            id = line.split('/')[1].replace('\n','')
            if setting_id != id:
                isChanged = True
            
            data += line.split('/')[0] + '/' + setting_id + '\n'
        else:
            data += line

    f.close()

    if isChanged:
        f = open('/etc/xdg/lxsession/LXDE-pi/autostart','w')
        f.write(data)
        f.close()
        os.system('shutdown -r now')
    
    class InputChunkProtocol(asyncio.Protocol):
        def __init__(self):
            self.line = ''
            
        def connection_made(self, transport):
            self.transport = transport
        
        def data_received(self, data):
            global Channel, CO2, TVOC, PM25, TEMP, HUMID, LIGHT, WATER1, WATER2, WATER3, SERVER_STATUS, SENSOR_STATUS, SERIAL_WATCHDOG, comm
            
            if len(data) > 0:
                self.line += str(data, 'utf-8')
            #print('\n[Sensor sData]', self.line)

            SERIAL_WATCHDOG = time.time()
            SENSOR_STATUS = False
            
                            
#             if ('{' in self.line and '}' in self.line) and (self.line.find('{') < self.line.find('}')):
#                 line = self.line[self.line.find('{'):self.line.find('}')+1]
#                 self.line = ''
#                 print('[Sensor Data]', line)
#                 try:
#                     if len(line) > 0:
#                         d = json.loads(line)
#                         Channel = d['CH']
#                         
#                         if int(Channel) == readDipSW():
#                             CO2 = int(d['CO2'])
#                             TVOC = int(d['TVOC'])
#                             PM25 = int(d['PM25'])
#                             TEMP = float(d['TEMP'])
#                             HUMID = float(d['HUMID'])
#                             LIGHT = int(d['LIGHT'])
#                         
#                 except Exception as e:
#                     # SERVER_STATUS = False
#                     print('Serial Error:', e)
#             elif ('{' in self.line and '}' in self.line) and (self.line.find('{') > self.line.find('}')):
#                 self.line = self.line[self.line.find('{'):]
                
            self.transport.write(bytes(comm, 'utf-8'))
            self.pause_reading()
            
        def pause_reading(self):
            self.transport.pause_reading()
            
        def resume_reading(self):
            self.transport.resume_reading()

    async def reader():
        global SERVER_STATUS
        transport, protocol = await serial_asyncio.create_serial_connection(loop, InputChunkProtocol, '/dev/serial0', baudrate=9600)
        
        while True:
            if not SERVER_STATUS: break
            await asyncio.sleep(1)
            try:
                protocol.resume_reading()
                
            except Exception as e:
                # SERVER_STATUS = False
                print('Serial Reader Error:', e)
                
        # raise RuntimeError('Serial Read Error')    

else:
    class GPIO():
        def output(pin, value):
            if pin == 17:
                print('RELAY1 set', value)
            elif pin == 27:
                print('RELAY2 set', value)
            elif pin == 22:
                print('RELAY3 set', value)
            elif pin == 18:
                print('RELAY4 set', value)
            elif pin == 25:
                print('RELAY5 set', value)
            elif pin == 8:
                print('RELAY6 set', value)
            elif pin == 12:
                print('RELAY7 set', value)
            elif pin == 13:
                print('RELAY8 set', value)
            else:
                print('Wrong pin number')
        
        def input(pin):
            return 1
    
    setting_id = '8d3cd'
    uri = 'ws://127.0.0.1/atmo_ws?%s' % (setting_id)

    async def reader():
        global Channel, CO2, TVOC, PM25, TEMP, HUMID, LIGHT, WATER1, WATER2, WATER3, SERVER_STATUS, SENSOR_STATUS
        
        while True:
            if not SERVER_STATUS: break
            await asyncio.sleep(1)
            try:
                CO2 = random.randint(20,25)
                TVOC = random.randint(100,110)
                PM25 = random.randint(10,20)
                TEMP = 26.6
                HUMID = 54.2
                LIGHT = random.randint(550,560)
                SENSOR_STATUS = True

            except Exception as e:
                # SERVER_STATUS = False
                print('Serial Reader Error:', e)
                
        # raise RuntimeError('Serial Read Error')



def saveParams(RELAYS_PARAM):
    params = {
        "CONTROL": [json.loads(RELAYS_PARAM[0]),
                    json.loads(RELAYS_PARAM[1]),
                    json.loads(RELAYS_PARAM[2]),
                    json.loads(RELAYS_PARAM[3]),
                    json.loads(RELAYS_PARAM[4]),
                    json.loads(RELAYS_PARAM[5]),
                    json.loads(RELAYS_PARAM[6]),
                    json.loads(RELAYS_PARAM[7])
                    ]
        }
    with open('./saved3.json', 'w', encoding='utf-8') as make_file:
        json.dump(params, make_file, indent='\t')
        

def readParams():
    global RELAYS_PARAM
    RELAYS_PARAM = []
    relay_list = [1,2,3,4,5,6,7,8]
    if os.path.exists('./saved3.json'):
        with open('./saved3.json', 'r', encoding='utf-8') as read_file:
            d = json.load(read_file)
            for relay in d['CONTROL']:
                j = json.dumps(relay)
                jj = int(json.loads(j)["RELAY"])
                relay_list.remove(jj)
                RELAYS_PARAM.append(j)
            
            for relay in relay_list:
                j = '''{"RELAY": "%d", "NAME": "", "MODE": "onoff", "ONOFFINFO": "off"}''' % (relay)
                RELAYS_PARAM.append(j)
                
    else:
        pData = '''
{
	"CONTROL": [
		{
			"RELAY": "1",
			"NAME": "RELAY1",
			"MODE": "onoff",
			"ONOFFINFO": "off"
		},
		{
			"RELAY": "2",
			"NAME": "RELAY2",
			"MODE": "onoff",
			"ONOFFINFO": "off"
		},
		{
			"RELAY": "3",
			"NAME": "RELAY3",
			"MODE": "onoff",
			"ONOFFINFO": "off"
		},
		{
			"RELAY": "4",
			"NAME": "RELAY4",
			"MODE": "onoff",
			"ONOFFINFO": "off"
		},
		{
			"RELAY": "5",
			"NAME": "RELAY5",
			"MODE": "onoff",
			"ONOFFINFO": "off"
		},
		{
			"RELAY": "6",
			"NAME": "RELAY6",
			"MODE": "onoff",
			"ONOFFINFO": "off"
		},
		{
			"RELAY": "7",
			"NAME": "RELAY7",
			"MODE": "onoff",
			"ONOFFINFO": "off"
		},
		{
			"RELAY": "8",
			"NAME": "RELAY8",
			"MODE": "onoff",
			"ONOFFINFO": "off"
		}
	]
}
'''
        with open('./saved3.json', 'w', encoding='utf-8') as save_file:
            save_file.write(pData)
        
        with open('./saved3.json', 'r', encoding='utf-8') as read_file:
            d = json.load(read_file)
            for relay in d['CONTROL']:
                RELAYS_PARAM.append(json.dumps(relay))

        # RELAYS_PARAM = ['{"RELAY":"1", "MODE":"onoff", "ONOFFINFO":"off"}', '{"RELAY":"2", "MODE":"onoff", "ONOFFINFO":"off"}', '{"RELAY":"3", "MODE":"onoff", "ONOFFINFO":"off"}', '{"RELAY":"4", "MODE":"onoff", "ONOFFINFO":"off"}', '{"RELAY":"5", "MODE":"onoff", "ONOFFINFO":"off"}', '{"RELAY":"6", "MODE":"onoff", "ONOFFINFO":"off"}', '{"RELAY":"7", "MODE":"onoff", "ONOFFINFO":"off"}', '{"RELAY":"8", "MODE":"onoff", "ONOFFINFO":"off"}']


def runManualMode(ONOFFINFO):
    if ONOFFINFO == 'on': return True
    else: return False
                
def runPeriodictMode(WEEKINFO):
    try:
        # "WEEKINFO": {"START_DT": "20220909", "REPEAT_DAY": "15", "START_TIME": "0030", "END_TIME": "0100"}}
        scheduled_date = datetime.datetime.strptime(WEEKINFO['START_DT'], '%Y-%m-%d').replace(tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
        now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9)))
        diff = now - scheduled_date
        
        #print('WEEK', WEEKINFO)

        if diff.days % int(WEEKINFO['REPEAT_DAY']) == 0:
            if int(WEEKINFO['START_TIME']) <= now.hour*100 + now.minute < int(WEEKINFO['END_TIME']):
                return True
        return False

    except Exception as e:
        print('WEEK INFO ERROR:', e)
        return False

def runWeeklyRepeatMode(REPEATINFO):
    try:
        # "REPEATINFO": [{"WEEK_INFO": "1", "START_TIME": "0100", "END_TIME": "0200"}, {"WEEK_INFO": "2", "START_TIME": "0100", "END_TIME": "0200"}]
        # Mon(1), Tue(2), Wed(3), Thu(4), Fri(5), Sat(6), Sun(7)
        now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9)))
        
        for element in REPEATINFO:
            #print('REPEAT',element)
            if element['WEEK_INFO'] == '':
                return False
            if int(element['WEEK_INFO']) == now.weekday()+1:
                if int(element['START_TIME']) <= now.hour*100 + now.minute < int(element['END_TIME']):
                    return True
        return False
                
    except Exception as e:
        print('WEEK INFO ERROR:', e)
        return False

def readDipSW():
    num = 0
    if GPIO.input(DIP2_PIN_1) == 0:
        num += 8
    if GPIO.input(DIP1_PIN_2) == 0:
        num += 4
    if GPIO.input(DIP4_PIN_3) == 0:
        num += 2
    if GPIO.input(DIP3_PIN_4) == 0:
        num += 1
    
    return num

def updateRelay():
    global RELAYS_PARAM, Manual_Relay_Info, Relay_Pins, comm
    
    try:
        print('\n--------------- checking relay params ---------------')
        for idx, relay in enumerate(RELAYS_PARAM):
            result = False
            
            relay = json.loads(relay)
            print(relay)
            
            if relay['MODE'] == 'onoff':   # manual mode
                result = runManualMode(relay['ONOFFINFO'])
                if relay['ONOFFINFO'] == 'on' and Manual_Relay_Info[idx][0] == False:
                    Manual_Relay_Info[idx][0] = True
                    Manual_Relay_Info[idx][1] = time.time()
                elif relay['ONOFFINFO'] == 'off': Manual_Relay_Info[idx][0] = False
                
            
            elif relay['MODE'] == 'repeat':   # weekly repeat mode
                result = runWeeklyRepeatMode(relay['REPEATINFO'])
                Manual_Relay_Info[idx][0] = False

            elif relay['MODE'] == 'week': # periodic mode
                result = runPeriodictMode(relay['WEEKINFO'])
                Manual_Relay_Info[idx][0] = False
                
            
            if Manual_Relay_Info[idx][0] and (time.time() - Manual_Relay_Info[idx][1]) > 60*20:
                result = False
                RELAYS_PARAM[idx] = '''{"RELAY": "%d", "NAME": "%s", "MODE": "onoff", "ONOFFINFO": "off"}''' % (idx+1, relay['NAME'])
                Manual_Relay_Info[idx][0] = False
                saveParams(RELAYS_PARAM)


            if result:
                #GPIO.output(Relay_Pins[idx], True)
                comm = list(comm)
                comm[idx+1] = '1'
                comm = ''.join(comm)
            else:
                #GPIO.output(Relay_Pins[idx], False)
                comm = list(comm)
                comm[idx+1] = '0'
                comm = ''.join(comm)

        print('-----------------------------------------------------\n')
    except Exception as e:
        print('Update Realy Error:', e)

async def TGMSG(message):
    try:
        print(message)
        msg = '[%s][%s]\n%s' % (setting_id, datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'), message)
        await TGBOT.sendMessage(chat_id=chat_id, text=msg)
    except Exception as e:
        print('TGMSG ERROR', e)
    
async def send_sensor_data(ws):
    global Channel, CO2, TVOC, PM25, TEMP, HUMID, LIGHT, WATER1, WATER2, WATER3, SERVER_STATUS, SENSOR_STATUS, SERIAL_WATCHDOG, msgToSend, isReadyToSend, RECIEVE_WATCHDOG

    DB_time_check = 0
    WEB_time_check = 0
    relay_time_check = 0
    ping_pong_time_check = 0
    connection_check = 0
    RECIEVE_WATCHDOG = time.time()
    
    while True:
        await asyncio.sleep(0)
        if time.time() - RECIEVE_WATCHDOG > 120.0:
            await TGMSG('RECEIVE_WATCHDOG is over')
            SERVER_STATUS = False

        if not SERVER_STATUS: break
        
        try:
            if isReadyToSend:
                print('[Send Message to server]', msgToSend)
                await ws.send(msgToSend)
                isReadyToSend = False
                msgToSend = ''


            if time.time() - SERIAL_WATCHDOG > 10.0:
                SENSOR_STATUS = False
            
            if int(time.time()) - connection_check >= 60 * 5:   # connection check every 5 mins
                pyautogui.press('f5')
                connection_check = int(time.time())
                URL = 'https://v1.azmo.kr/api/fr/frMachineConnect.json?MACHINE_ID=%s' % (setting_id)
                res = requests.get(URL)
                #print('connection check status code:', res.status_code)

            if SENSOR_STATUS:
                if int(time.time()) - DB_time_check >= 60 * 30:   # DB update per every 30 mins
                    DB_time_check = int(time.time())
                    URL = 'https://v1.azmo.kr/api/fr/frMachineApiSave.json?MACHINE_ID=%s&CO2=%d&TVOC=%d&PM25=%d&TEMP=%.1f&HUMID=%.1f&LIGHT=%d' % (setting_id, CO2, TVOC, PM25, TEMP, HUMID, LIGHT)
                    res = requests.get(URL)
                    #print('data db push status code:', res.status_code)
#                     params = {
#                         "METHOD": "DBINIT",
#                         "CO2": CO2,
#                         "TVOC": TVOC,
#                         "PM25": PM25,
#                         "TEMP": TEMP,
#                         "HUMID": HUMID,
#                         "LIGHT": LIGHT
#                     }
#                     pData = json.dumps(params)
#                     print('[DB PUSH]', pData)
#                     await ws.send(pData)
                    
                if int(time.time()) - WEB_time_check >= 60:   # web update per every 60 sec
                    WEB_time_check = int(time.time())
                    params = {
                        "METHOD": "SEND_F",
                        "CO2": CO2,
                        "TVOC": TVOC,
                        "PM25": PM25,
                        "TEMP": TEMP,
                        "HUMID": HUMID,
                        "LIGHT": LIGHT,
                        "WATER1": 0,
                        "WATER2": 0,
                        "WATER3": 0
                    }

                    pData = json.dumps(params)
                    print('[WEB PUSH]', pData)
                    await ws.send(pData)
            else:
                if int(time.time()) - WEB_time_check >= 5:   # DO NOT CHANGE THE VALUE
                    WEB_time_check = int(time.time())
                    print('Sensor Status False')
                
            
            if int(time.time()) - relay_time_check >= 5: # check relay every 5 sec
                relay_time_check = int(time.time())
                updateRelay()
            
            if int(time.time()) - ping_pong_time_check >= 10:
                ping_pong_time_check = int(time.time())
                params = {
                    "METHOD": "PING"
                }

                pData = json.dumps(params)
                print('[SEND PING]', pData)
                await ws.send(pData)
                
        except Exception as e:
            SERVER_STATUS = False
            await TGMSG('Sender Error: %s' % (e))
            ws.close()
            await TGMSG('Websocket Closed!')

async def recv_handler(ws):
    global RELAYS_PARAM, SERVER_STATUS, SENSOR_STATUS, ERRORCOUNT, msgToSend, isReadyToSend, RECIEVE_WATCHDOG
    
    while True:
        if not SERVER_STATUS: break
        try:
            try:
                await asyncio.sleep(0)
                data = await ws.recv()
            except Exception as e:
                print('Websocket recv() Error:', e)
                continue

            d = json.loads(data)
            print('recieved:', d)
            
            if 'TIMESTAMP' in d:
                # time_cmd = "sudo date -s '%s'" % d['TIMESTAMP']
                # os.system(time_cmd)
                TIMESTAMP = '%s' % (d['TIMESTAMP'])
                subprocess.call(['sudo', 'date', '-s', TIMESTAMP])
            
            if d['METHOD'] == 'CALL_A':
                params = {
                "METHOD": "CALL_R",
                "CONTROL": [json.loads(RELAYS_PARAM[0]),
                            json.loads(RELAYS_PARAM[1]),
                            json.loads(RELAYS_PARAM[2]),
                            json.loads(RELAYS_PARAM[3]),
                            json.loads(RELAYS_PARAM[4]),
                            json.loads(RELAYS_PARAM[5]),
                            json.loads(RELAYS_PARAM[6]),
                            json.loads(RELAYS_PARAM[7])
                        ]
                }
                pData = json.dumps(params)
                ERRORCOUNT = 0
                # await ws.send(pData)
                msgToSend = pData
                isReadyToSend = True
                
            
            elif d['METHOD'] == 'UPT_R':
                for relay in d['CONTROL']:
                    # print(relay)
                    if relay['RELAY'] == "1":
                        RELAYS_PARAM[0] = json.dumps(relay)
                    elif relay['RELAY'] == "2":
                        RELAYS_PARAM[1] = json.dumps(relay)
                    elif relay['RELAY'] == "3":
                        RELAYS_PARAM[2] = json.dumps(relay)
                    elif relay['RELAY'] == "4":
                        RELAYS_PARAM[3] = json.dumps(relay)
                    elif relay['RELAY'] == "5":
                        RELAYS_PARAM[4] = json.dumps(relay)
                    elif relay['RELAY'] == "6":
                        RELAYS_PARAM[5] = json.dumps(relay)
                    elif relay['RELAY'] == "7":
                        RELAYS_PARAM[6] = json.dumps(relay)
                    elif relay['RELAY'] == "8":
                        RELAYS_PARAM[7] = json.dumps(relay)
                saveParams(RELAYS_PARAM)

            elif d['METHOD'] == 'TOTAL_STATUS':
                RECIEVE_WATCHDOG = int(time.time())
                params = {
                    "METHOD": "TOTAL_STATUS",
                    "DEVICE_ID": setting_id,
                    "SENSOR_STATUS": SENSOR_STATUS,
                    "VERSION": VERSION
                }
                pData = json.dumps(params)
                # await ws.send(pData)
                msgToSend = pData
                isReadyToSend = True

            elif d['METHOD'] == 'R_START':
                params = {
                    "METHOD": "R_START",
                    "RESULT": True
                }
                pData = json.dumps(params)
                await TGMSG('Reboot')

                # await ws.send(pData)
                msgToSend = pData
                isReadyToSend = True
                await asyncio.sleep(5)
                os.system('shutdown -r now')
            
            elif d['METHOD'] == 'OTA':
                await TGMSG('Updating..')
                os.system('wget -P /home/pi/ https://raw.githubusercontent.com/picshbj/ATMOV3/main/main.py')
                
                path_src = '/home/pi/main.py'
                path_dest = '/home/pi/Documents/main.py'

                if os.path.isfile(path_src):
                    shutil.move(path_src, path_dest)
                
                await asyncio.sleep(10)

                params = {
                    "METHOD": "OTA",
                    "RESULT": True
                }
                pData = json.dumps(params)
                
                # await ws.send(pData)
                msgToSend = pData
                isReadyToSend = True

                await TGMSG('Update done and reboot..')

                subprocess.call(['reboot'])
            
            elif d['METHOD'] == 'PONG':
                RECIEVE_WATCHDOG = int(time.time())
                    

        except Exception as e:
            SERVER_STATUS = False
            await TGMSG('Recieve Error: %s' % e)
            await TGMSG('Recieved: %s' % (data))
            ws.close()
            await TGMSG('Websocket Closed!')
            

async def main():
    global SERVER_STATUS, ERRORCOUNT
    readParams()
    await TGMSG('Booting..')
    
    while True:  
        await TGMSG('Updating Relays..')
        updateRelay()
        
        SERVER_STATUS = True
        if ERRORCOUNT > 25:
            await TGMSG('Error occurred. Reboot: %d' % ERRORCOUNT)
            subprocess.call(['reboot'])
        else:
            print('ERROR COUNT: %d' % (ERRORCOUNT))
        

        await TGMSG('Creating a new websockets..')
        try:
            async with websockets.connect(uri) as ws:
                await asyncio.gather(
                    send_sensor_data(ws),
                    recv_handler(ws),
                    reader()
                )
        except Exception as e:
            await TGMSG('Main Error: %s' % (e))

            await asyncio.sleep(1)
            ERRORCOUNT += 1

while True:
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()
    except Exception as e:
        pass

