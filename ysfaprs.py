#   part of pYSFReflector
#

import aprslib
import time
import math
from datetime import datetime, date
import sys

# aprs last heard
APRS_LH = []     # 0 -> call 1 -> lat 2 -> long 3 -> time 


def aprs_string(call, latitude, longitude, radio_code, ysf_code, ssid):
  global APRS_LH
  radio_str = ''
  table = '/'
  symb = '['
#symbols 
# [ -> Jogger
# > -> Car
# - -> Home

  if ((len(call) < 3) or ((latitude == 999.0) and (longitude == 999.0))):
    return ''
  # used for unknown models 
  radio_str = '<' + str(hex(radio_code)) + '>' 
  
  if (radio_code == 0x20):
    radio_str = 'DR-2X'
    symb = '-'

  if (radio_code == 0x24):
    radio_str = 'FT-1D'
    symb = '['

  if (radio_code == 0x25):
    radio_str = 'FTM-400D'
    symb = '>'

  if (radio_code == 0x26):
    radio_str = 'DR-1X'
    symb = '-'
    
  if (radio_code == 0x27):
    radio_str = 'FT-991A'
    symb = '-'  

  if (radio_code == 0x28):
    radio_str = 'FT-2D'
    symb = '['

  if (radio_code == 0x29):
    radio_str = 'FTM-100D'
    symb = '>'

  if (radio_code == 0x31):
    radio_str = 'FTM-300D'
    symb = '>'

  if (radio_code == 0x30):
    radio_str = 'FT-3D'
    symb = '['
    
  if (radio_code == 0x33):
    radio_str = 'FT-5D'
    symb = '['  

  if (radio_code == 0x34):
    radio_str = 'FTM-500D'
    symb = '>'  
  
  if (radio_code == 0x35):
    radio_str = 'FTM-510D'
    symb = '>'  
  
  if (radio_code == 0x2A):
    radio_str = 'FTM-3200D'
    symb = '>'  
  
  if (radio_code == 0x32):
    radio_str = 'FTM-200D'
    symb = '>'
    
  if (radio_code == 0x2B):
    radio_str = 'FT-70D'
    symb = '['  
  
  if (radio_code == 0x2E):
    radio_str = 'FTM-7250D'
    symb = '>'
    
  if (radio_code == 0x2D):
    radio_str = 'FTM-3207D'
    symb = '>'  
  
  # ssid = '-10'

  ora = datetime.utcnow()
  oraz = ora.strftime("%d%H%M")
  lat = aprslib.util.latitude_to_ddm(latitude)
  long = aprslib.util.longitude_to_ddm(longitude)

  now = time.time()
  found = False
  skip = False
  for c in APRS_LH:
    if (c[0] == call):
      found = True
      if (((now - c[3]) < 1800.0) and (c[1] == lat) and (c[2] == long)):
        skip = True
      else:
        c[1] = lat
        c[2] = long
        c[3] = now  
    else:
      if ((now - c[3]) > 1800.0):   # clean list 
        APRS_LH.remove(c)
        
  if (not found):
    APRS_LH.append([call, lat, long, now])

# 2021-05-29 16:56:40 CEST: IT9FRN>API510,DSTAR*,qAR,IR5UBO-B:!4340.94N/01126.94E>326/059/A=000424Peppe Mobile

  if (not skip):
    desc = 'YSF#' + ysf_code + ' via pYSFReflector'
    aprs_str = call + ssid + '>APRS,TCPIP*:@' + oraz + 'z' + lat + table + long + symb +  desc

    if (len(radio_str) > 0):
      aprs_str += ' ' + radio_str
  else:
    aprs_str = ''  

  return aprs_str




def send_aprs(aprs_string, aprs_server, aprs_user, aprs_port):  

  passw = str(aprslib.passcode(aprs_user))

  try:
    # OK FUNZIONA !!!
    # SI PUO' USARE IL NOME DEL REFLECTOR COME USERNAME
    AIS = aprslib.IS(aprs_user, host=aprs_server, passwd=passw, port=aprs_port)
    AIS.connect()
    AIS.sendall(aprs_string)
    AIS.close() 
  except Exception as e:
    print('Impossibile collegarsi al server APRS ' + str(e))
   


if __name__ == '__main__':
  print(aprs_string('IU5JAE', 44.0, 10.5, 0x31, '90123'))      
  send_aprs(aprs_string('IU5JAE', 44.0, 10.5, 0x31, '90123'), 'aprs.grupporadiofirenze.net', 'YSF90123')
  send_aprs(aprs_string('IU5JAE', 44.0, 10.5, 0x31, '90123'), 'aprs.grupporadiofirenze.net', 'YSF90123')
