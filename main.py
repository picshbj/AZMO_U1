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
import serial_asyncio
import telegram


global RELAYS_PARAM, SERVER_STATUS, RELAY_STATUS, SERIAL_WATCHDOG, Manual_Relay_Info, isReadyToSend, ERRORCOUNT, RECIEVE_WATCHDOG, comm, TGBOT, SOIL_HUMID, SOIL_TEMP
ERRORCOUNT = TGBOT = RECIEVE_WATCHDOG = SOIL_HUMID = SOIL_TEMP = 0

SERVER_STATUS = True
RELAY_STATUS = True
isReadyToSend = False
SERIAL_WATCHDOG = 0
Manual_Relay_Info = [[False, 0],[False, 0],[False, 0],[False, 0],[False, 0],[False, 0],[False, 0],[False, 0]]
comm = 'S00000000\n'
setting_id = ''

VERSION = '4.1U'


# telegram bot setup
while True:
    try:
        TGBOT = telegram.Bot(token='6725689755:AAFecGY3ty3wheg44lR8d-6hO7LIuhAfiao')
        chat_id = 5391813621
        break
    except Exception as e:
        print('telegram setup failed..')
        time.sleep(5)


# load device id
f = open('/boot/uEnv.txt', 'r')
for line in f:
    if 'device_id' in line:
        d = line.split('=')
        if d[0] == 'device_id':
            setting_id = d[1]
            setting_id = setting_id.replace(' ', '')
            setting_id = setting_id.replace('\n', '')
f.close()

# set websocket uri
uri = 'wss://admin.azmo.kr/azmo_ws?%s' % (setting_id)


# serial input asyncio class
class InputChunkProtocol_Relay(asyncio.Protocol):
    def __init__(self):
        self.line = ''
        
    def connection_made(self, transport):
        self.transport = transport
    
    def data_received(self, data):
        global SERVER_STATUS, RELAY_STATUS, SERIAL_WATCHDOG, comm
        
        if len(data) > 0:
            self.line += str(data, 'utf-8')
        print('[Relay sData]', self.line)
        self.line = ''
        RELAY_STATUS = True

        SERIAL_WATCHDOG = time.time()
            
        self.transport.write(bytes(comm, 'utf-8'))
        self.pause_reading()
        
    def pause_reading(self):
        self.transport.pause_reading()
        
    def resume_reading(self):
        self.transport.resume_reading()

async def reader_relay():
    global SERVER_STATUS
    transport, protocol = await serial_asyncio.create_serial_connection(loop, InputChunkProtocol_Relay, '/dev/ttyS1', baudrate=9600)
    
    while True:
        if not SERVER_STATUS: break
        await asyncio.sleep(1)
        try:
            protocol.resume_reading()
            
        except Exception as e:
            # SERVER_STATUS = False
            print('Serial Reader Error:', e)
            
    # raise RuntimeError('Serial Read Error')    


# serial input asyncio class
class InputChunkProtocol_SoilSensor(asyncio.Protocol):
    def __init__(self):
        self.line = ''
        self.data = bytearray([0x01, 0x03, 0x00, 0x00, 0x00, 0x02, 0xc4, 0x0b])
        
    def connection_made(self, transport):
        self.transport = transport
    
    def data_received(self, data):
        global SERVER_STATUS, RELAY_STATUS, SERIAL_WATCHDOG, comm, SOIL_HUMID, SOIL_TEMP
        if len(data) == 9:
            SOIL_HUMID = (int(data[3])*256 + int(data[4])) / 10
            SOIL_TEMP = (int(data[5])*256 + int(data[6])) / 10

            print('temp: %.1fC, humid: %.1f%%' % (SOIL_TEMP, SOIL_HUMID))
        self.pause_reading()
        
    def pause_reading(self):
        self.transport.pause_reading()
        
    def resume_reading(self):
        self.transport.write(self.data)
        self.transport.resume_reading()

async def reader_soilsensor():
    global SERVER_STATUS
    transport, protocol = await serial_asyncio.create_serial_connection(loop, InputChunkProtocol_SoilSensor, '/dev/ttyS2', baudrate=9600)
    
    while True:
        if not SERVER_STATUS: break
        await asyncio.sleep(1)
        try:
            protocol.resume_reading()
            
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
    with open('./RelayInfo.json', 'w', encoding='utf-8') as make_file:
        json.dump(params, make_file, indent='\t')
        

def readParams():
    global RELAYS_PARAM
    RELAYS_PARAM = []
    relay_list = [1,2,3,4,5,6,7,8]
    if os.path.exists('./RelayInfo.json'):
        with open('./RelayInfo.json', 'r', encoding='utf-8') as read_file:
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
        with open('./RelayInfo.json', 'w', encoding='utf-8') as save_file:
            save_file.write(pData)
        
        with open('./RelayInfo.json', 'r', encoding='utf-8') as read_file:
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


def updateRelay():
    global RELAYS_PARAM, Manual_Relay_Info, comm
    
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
                comm = list(comm)
                comm[idx+1] = '1'
                comm = ''.join(comm)
            else:
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
    global SERVER_STATUS, RELAY_STATUS, SERIAL_WATCHDOG, msgToSend, isReadyToSend, RECIEVE_WATCHDOG

    DB_time_check = 0
    WEB_time_check = 0
    relay_time_check = 0
    ping_pong_time_check = 0
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
                RELAY_STATUS = False
            

            if RELAY_STATUS:
                if int(time.time()) - DB_time_check >= 60 * 30:   # DB update per every 30 mins
                    DB_time_check = int(time.time())
                    # URL = 'https://v1.azmo.kr/api/fr/frMachineApiSave.json?MACHINE_ID=%s&CO2=%d&TVOC=%d&PM25=%d&TEMP=%.1f&HUMID=%.1f&LIGHT=%d' % (setting_id, CO2, TVOC, PM25, TEMP, HUMID, LIGHT)
                    # res = requests.get(URL)
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
    global RELAYS_PARAM, SERVER_STATUS, RELAY_STATUS, ERRORCOUNT, msgToSend, isReadyToSend, RECIEVE_WATCHDOG
    
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
                    "SENSOR_STATUS": True,
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
                os.system('wget -P /home/pi/ https://raw.githubusercontent.com/picshbj/AZMO_U1/main/main.py')
                
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
        if ERRORCOUNT > 50:
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
                    reader_relay(),
                    reader_soilsensor()
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

