#   part of pYSFReflector
#

import crc

latitude = 999.0
longitude = 999.0
radio_code = 0x0

def gps_reset():
  global latitude
  global longitude
  global radio_code
  latitude = 999.0
  longitude = 999.0
  radio_code = 0x0

def GPS_dec(data, ft):
  global latitude
  global longitude
  global radio_code
  
  latitude = 999.0
  longitude = 999.0
  radio_code = 0x0
  
  i = (ft - 5) * 10 - 2
  valid = False
  while (i >= 0):
    if (data[i] == 0x03):
      crcd = crc.addCRC(data, i+1)
      if (crcd == data[i + 1]):
        valid = True
        break
    i = i-1
    
  if valid:
    radio_code = data[4]
    if ((data[1] == 0x22) and (data[2] == 0x62)):
      #print('short')
      GPS_string(data)        
      
    if ((data[1] == 0x47) and (data[2] == 0x64)):
      #print('long')
      GPS_string(data)

  return valid


def GPS_string(data):
  global latitude
  global longitude
  global radio_code
  
  
  for i in range(6):
    b = data[i+5] & 0xF0
    if ((b != 0x50) and (b != 0x30)):
      return False                               

    
  tens = data[5] & 0x0F
  units = data[6] & 0x0F
  lat_deg = tens * 10 + units
  if ((tens > 9) or (units > 9) or (lat_deg > 89)):
    return False

 
  tens = data[7] & 0x0F
  units = data[8] & 0x0F
  lat_min = tens * 10 + units
  if ((tens > 9) or (units > 9) or (lat_min > 59)):
    return False

 
  tens = data[9] & 0x0F
  units = data[10] & 0x0F
  lat_min_frac = tens * 10 + units
  if ((tens > 9) or (units > 10) or (lat_min_frac > 99)):
    return False

  b = data[8] & 0xF0

  if (b == 0x50):
    lat_dir = 1
  else:
    if (b == 0x30):
      lat_dir = -1  
    else:
      return False

  b = data[9] & 0xF0
  if (b == 0x50):
    b = data[11]
    if ((b >= 0x76) and (b <= 0x7F)):
      lon_deg = b - 0x76
    else:
      if ((b >= 0x6C) and (b <= 0x75)):
        lon_deg = 100 + (b - 0x6C)
      else:
        if ((b >= 0x26) and (b <= 0x6B)):
          lon_deg = 110 + (b - 0x26)
        else:
          return False
        
  else:
    if (b == 0x30):
      b = data[11]
      if ((b >= 0x26) and (b <= 0x7F)):
        lon_deg = 10 + (b - 0x26)
      else:
        return False
    else: 
      return False

  b = data[12]
  if ((b >= 0x58) and (b <= 0x61)):
    lon_min = b - 0x58
  else:
    if ((b >= 0x26) and (b <= 0x57)):
      lon_min = 10 + (b - 0x26)
    else:
      return False

	
  b = data[13]
  if ((b >= 0x1C) and (b <= 0x7F)):
    lon_min_frac = b - 0x1C
  else:
    return False

	
  b = data[10] & 0xF0
  if (b == 0x30):
    lon_dir = 1
  else:
    if (b == 0x50):
      lon_dir = -1
    else:
      return False     


  latitude = lat_deg + ((lat_min + (lat_min_frac * 0.01)) * (1.0 / 60.0))
  latitude *= lat_dir

  longitude = lon_deg + ((lon_min + (lon_min_frac * 0.01)) * (1.0 / 60.0));
  longitude *= lon_dir;

  return True



if __name__ == '__main__':

    d70  = [7, 34, 97, 95, 43, 3, 23, 0, 0, 0]
    d300 = [69, 34, 98, 95, 49, 84, 51, 85, 89, 50, 48, 38, 58, 83, 108, 32, 28, 32, 3, 110]

    GPS_dec(d300, 7)
    print(latitude)
    print(longitude)
