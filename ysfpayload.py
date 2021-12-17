#   part of pYSFReflector
#
#   based on 
#
#    Copyright (C) 2016,2017 Jonathan Naylor, G4KLX
#    Copyright (C) 2016 Mathias Weyland, HB9FRV
#


import ysfconvolution
import golay24128
import crc
import ysfutils

YSF_SYNC_LENGTH_BYTES = 5
YSF_FICH_LENGTH_BYTES = 25
YSF_CALLSIGN_LENGTH   = 10

BIT_MASK_TABLE = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01]

WHITENING_DATA = [0x93, 0xD7, 0x51, 0x21, 0x9C, 0x2F, 0x6C, 0xD0, 0xEF, 0x0F,
		  0xF8, 0x3D, 0xF1, 0x73, 0x20, 0x94, 0xED, 0x1E, 0x7C, 0xD8]

INTERLEAVE_TABLE_5_20 = [
   0, 40,  80, 120, 160,
   2, 42,  82, 122, 162,
   4, 44,  84, 124, 164,
   6, 46,  86, 126, 166,
   8, 48,  88, 128, 168,
  10, 50,  90, 130, 170,
  12, 52,  92, 132, 172,
  14, 54,  94, 134, 174,
  16, 56,  96, 136, 176,
  18, 58,  98, 138, 178,
  20, 60, 100, 140, 180,
  22, 62, 102, 142, 182,
  24, 64, 104, 144, 184,
  26, 66, 106, 146, 186,
  28, 68, 108, 148, 188,
  30, 70, 110, 150, 190,
  32, 72, 112, 152, 192,
  34, 74, 114, 154, 194,
  36, 76, 116, 156, 196,
  38, 78, 118, 158, 198]



INTERLEAVE_TABLE_9_20 = [
        0, 40,  80, 120, 160, 200, 240, 280, 320, 
        2, 42,  82, 122, 162, 202, 242, 282, 322,
        4, 44,  84, 124, 164, 204, 244, 284, 324,
        6, 46,  86, 126, 166, 206, 246, 286, 326,
        8, 48,  88, 128, 168, 208, 248, 288, 328,
       10, 50,  90, 130, 170, 210, 250, 290, 330,
       12, 52,  92, 132, 172, 212, 252, 292, 332,
       14, 54,  94, 134, 174, 214, 254, 294, 334,
       16, 56,  96, 136, 176, 216, 256, 296, 336,
       18, 58,  98, 138, 178, 218, 258, 298, 338,
       20, 60, 100, 140, 180, 220, 260, 300, 340,
       22, 62, 102, 142, 182, 222, 262, 302, 342,
       24, 64, 104, 144, 184, 224, 264, 304, 344,
       26, 66, 106, 146, 186, 226, 266, 306, 346,
       28, 68, 108, 148, 188, 228, 268, 308, 348,
       30, 70, 110, 150, 190, 230, 270, 310, 350,
       32, 72, 112, 152, 192, 232, 272, 312, 352,
       34, 74, 114, 154, 194, 234, 274, 314, 354,
       36, 76, 116, 156, 196, 236, 276, 316, 356,
       38, 78, 118, 158, 198, 238, 278, 318, 358]


m_uplink = ''
m_downlink = ''
m_source = ''
m_dest = ''


def WRITE_BIT1(p, i, b):
  if b:
    p[(i)>>3] = (p[(i)>>3] | BIT_MASK_TABLE[(i)&7])
  else:
    p[(i)>>3] = (p[(i)>>3] & (~BIT_MASK_TABLE[(i)&7]))      


def READ_BIT1(p,i):
  return (p[(i)>>3] & BIT_MASK_TABLE[(i)&7])


def processheaderdata(data):
  global m_source
  global m_dest
  global m_uplink
  global m_downlink
 

  m_uplink = ''
  m_downlink = ''
  m_source = ''
  m_dest = ''

  dch = [0] * 45
  data_i = YSF_SYNC_LENGTH_BYTES + YSF_FICH_LENGTH_BYTES
  dch_i = 0
  
  for i in range(5):
    for j in range(9):
      dch[dch_i+j] = data[data_i+j]

    data_i = data_i + 18
    dch_i = dch_i + 9  

  ysfconvolution.convolution_start()
   
  for i in range(180):
    n = INTERLEAVE_TABLE_9_20[i]
    if (READ_BIT1(dch, n) != 0): 
      s0 = 1
    else:  
      s0 = 0
      
    n += 1
    if (READ_BIT1(dch, n) != 0): 
      s1 = 1
    else:
      s1 = 0

    ysfconvolution.convolution_decode(s0, s1)
	
  output = [0] * 23

  ysfconvolution.convolution_chainback(output, 176)

  valid1 = crc.checkCCITT162(output, 22)
  
  if valid1:
    for i in range(20):
      output[i] ^= WHITENING_DATA[i]  
 
    if (len(m_dest) == 0):
      m_dest = ysfutils.list_to_string(output[0:YSF_CALLSIGN_LENGTH])
   
    if (len(m_source) == 0):
      m_source = ysfutils.list_to_string(output[YSF_CALLSIGN_LENGTH:2*YSF_CALLSIGN_LENGTH])
   
    for i in range(20):
      output[i] ^= WHITENING_DATA[i]
      
    crc.addCCITT162(output, 22)    
    output[22] = 0
    
    convolved = [0] * 45
    ysfconvolution.convolution_encode(output, convolved, 180)
    
    byt = [0] * 45
    j = 0
    for i in range(180):
      n = INTERLEAVE_TABLE_9_20[i]
      if (READ_BIT1(convolved, j) != 0):
        s0 = 1
      else:
        s0 = 0
      j += 1
      if (READ_BIT1(convolved, j) != 0):
        s1 = 1
      else:
        s1 = 0    
    
      WRITE_BIT1(byt, n, s0)
      n += 1
      WRITE_BIT1(byt, n, s1)
  
    data_i = 0
    byt_i = 0
    for i in range(5):
      for j in range(9):
        byt[byt_i+j] = data[data_i+j]

      data_i = data_i + 18
      byt_i = byt_i + 9  
      
  data_i = YSF_SYNC_LENGTH_BYTES + YSF_FICH_LENGTH_BYTES + 9
  dch_i = 0
  
  for i in range(5):
    for j in range(9):
      dch[dch_i+j] = data[data_i+j]

    data_i = data_i + 18
    dch_i = dch_i + 9  

  ysfconvolution.convolution_start()
   
  for i in range(180):
    n = INTERLEAVE_TABLE_9_20[i]
    if (READ_BIT1(dch, n) != 0): 
      s0 = 1
    else:  
      s0 = 0
      
    n += 1
    if (READ_BIT1(dch, n) != 0): 
      s1 = 1
    else:
      s1 = 0

    #print(str(s0) + ';' + str(s1))  
    ysfconvolution.convolution_decode(s0, s1)
    
  ysfconvolution.convolution_chainback(output, 176)
#  print(output)

  valid2 = crc.checkCCITT162(output, 22)
  
  if valid2:
    for i in range(20):
      output[i] ^= WHITENING_DATA[i]  
    if (len(m_downlink) == 0):
      m_downlink = ysfutils.list_to_string(output[0:YSF_CALLSIGN_LENGTH])
    if (len(m_uplink) == 0):
      m_uplink = ysfutils.list_to_string(output[YSF_CALLSIGN_LENGTH:2*YSF_CALLSIGN_LENGTH])  
	
    for i in range(20):
      output[i] ^= WHITENING_DATA[i]
      
    crc.addCCITT162(output, 22)    
    output[22] = 0
    
    convolved = [0] * 45
    ysfconvolution.convolution_encode(output, convolved, 180)
    
    byt = [0] * 45
    j = 0
    for i in range(180):
      n = INTERLEAVE_TABLE_9_20[i]
      if (READ_BIT1(convolved, j) != 0):
        s0 = 1
      else:
        s0 = 0
      j += 1
      if (READ_BIT1(convolved, j) != 0):
        s1 = 1
      else:
        s1 = 0    
    
      WRITE_BIT1(byt, n, s0)
      n += 1
      WRITE_BIT1(byt, n, s1)
  
    data_i = 0
    byt_i = 0
    for i in range(5):
      for j in range(9):
        byt[byt_i+j] = data[data_i+j]

      data_i = data_i + 18
      byt_i = byt_i + 9  
  
  return valid1



def readDataVDModeData2(data, dt):
  dch = [0] * 25
  data_i = YSF_SYNC_LENGTH_BYTES + YSF_FICH_LENGTH_BYTES
  dch_i = 0
  
  for i in range(5):
    for j in range(5):
      dch[dch_i+j] = data[data_i+j]

    data_i = data_i + 18
    dch_i = dch_i + 5  

  ysfconvolution.convolution_start()
   
  for i in range(100):
    n = INTERLEAVE_TABLE_5_20[i]
    if (READ_BIT1(dch, n) != 0): 
      s0 = 1
    else:  
      s0 = 0
      
    n += 1
    if (READ_BIT1(dch, n) != 0): 
      s1 = 1
    else:
      s1 = 0

    ysfconvolution.convolution_decode(s0, s1)
	
  output = [0] * 13

  ysfconvolution.convolution_chainback(output, 96)

  valid1 = crc.checkCCITT162(output, 12)
  
  if valid1:
    for i in range(10):
      output[i] ^= WHITENING_DATA[i]  
 
    for i in range(YSF_CALLSIGN_LENGTH):
      dt[i] = output[i]

  return valid1


def readDataFRModeData1(data, dt):
  dch = [0] * 45
  data_i = YSF_SYNC_LENGTH_BYTES + YSF_FICH_LENGTH_BYTES
  dch_i = 0
  
  
  for i in range(5):
    for j in range(9):
      dch[dch_i+j] = data[data_i+j]

    data_i = data_i + 18
    dch_i = dch_i + 9  

  ysfconvolution.convolution_start()
   
  for i in range(180):
    n = INTERLEAVE_TABLE_9_20[i]
    if (READ_BIT1(dch, n) != 0): 
      s0 = 1
    else:  
      s0 = 0
      
    n += 1
    if (READ_BIT1(dch, n) != 0): 
      s1 = 1
    else:
      s1 = 0

    ysfconvolution.convolution_decode(s0, s1)
	
  output = [0] * 23

  ysfconvolution.convolution_chainback(output, 176)

  valid1 = crc.checkCCITT162(output, 22)
  
  if valid1:
    for i in range(20):
      output[i] ^= WHITENING_DATA[i]  
 
    for i in range(20):
      #dt[i] = output[i]
      dt.append(output[i])
      
  return valid1


def readDataFRModeData2(data, dt):
  dch = [0] * 45
  data_i = YSF_SYNC_LENGTH_BYTES + YSF_FICH_LENGTH_BYTES + 9
  dch_i = 0
  
  
  for i in range(5):
    for j in range(9):
      dch[dch_i+j] = data[data_i+j]

    data_i = data_i + 18
    dch_i = dch_i + 9  

  ysfconvolution.convolution_start()
   
  for i in range(180):
    n = INTERLEAVE_TABLE_9_20[i]
    if (READ_BIT1(dch, n) != 0): 
      s0 = 1
    else:  
      s0 = 0
      
    n += 1
    if (READ_BIT1(dch, n) != 0): 
      s1 = 1
    else:
      s1 = 0

    ysfconvolution.convolution_decode(s0, s1)
	
  output = [0] * 23

  ysfconvolution.convolution_chainback(output, 176)

  valid1 = crc.checkCCITT162(output, 22)
  
  if valid1:
    for i in range(20):
      output[i] ^= WHITENING_DATA[i]  
 
    for i in range(20):
      # dt[i] = output[i]
      dt.append(output[i])

  return valid1




def writeVDMmode2Data(data, dt):
  data_i = YSF_SYNC_LENGTH_BYTES + YSF_FICH_LENGTH_BYTES
  dt_tmp = [0] * 13
  
  for i in range(YSF_CALLSIGN_LENGTH):
    dt_tmp[i] = dt[i]
  
  for i in range(10):
    dt_tmp[i] ^= WHITENING_DATA[i]
  
  crc.addCCITT162(dt_tmp, 12)
  dt_tmp[12] = 0
  ysfconvolution.convolution_start()
  convolved = [0] * 25
  ysfconvolution.convolution_encode(dt_tmp, convolved, 100)  
  
  byt = [0] * 25
  j = 0
  for i in range(100):
    n = INTERLEAVE_TABLE_5_20[i]
    if (READ_BIT1(convolved, j) != 0): 
      s0 = 1
    else:  
      s0 = 0
      
    j += 1
    if (READ_BIT1(convolved, j) != 0): 
      s1 = 1
    else:
      s1 = 0
    j += 1
    
    WRITE_BIT1(byt, n, s0)

    n += 1
    WRITE_BIT1(byt, n, s1)
  byt_i = 0
    
  for i in range(5):
    for j in range(5):
      data[data_i + j] = byt[byt_i + j]
    data_i += 18
    byt_i += 5      

def writeDataFRModeData1(dt, data):
  data_i = YSF_SYNC_LENGTH_BYTES + YSF_FICH_LENGTH_BYTES
  output = [0] * 25
  for i in range(20):
    output[i] = dt[i] ^ WHITENING_DATA[i]
  crc.addCCITT162(output, 22)
  output[22] = 0
  ysfconvolution.convolution_start()
  convolved = [0] * 45
  ysfconvolution.convolution_encode(output, convolved, 180)  
  
  byt = [0] * 45
  j = 0
  for i in range(180):
    n = INTERLEAVE_TABLE_9_20[i]
    if (READ_BIT1(convolved, j) != 0): 
      s0 = 1
    else:  
      s0 = 0
      
    j += 1
    if (READ_BIT1(convolved, j) != 0): 
      s1 = 1
    else:
      s1 = 0
    j += 1
    
    WRITE_BIT1(byt, n, s0)

    n += 1
    WRITE_BIT1(byt, n, s1)
  byt_i = 0
    
  for i in range(5):
    for j in range(9):
      data[data_i + j] = byt[byt_i + j]
    data_i += 18
    byt_i += 9        
    

def writeDataFRModeData2(dt, data):
  data_i = YSF_SYNC_LENGTH_BYTES + YSF_FICH_LENGTH_BYTES
  output = [0] * 25
  for i in range(20):
    output[i] = dt[i] ^ WHITENING_DATA[i]
  crc.addCCITT162(output, 22)
  output[22] = 0
  ysfconvolution.convolution_start()
  convolved = [0] * 45
  ysfconvolution.convolution_encode(output, convolved, 180)  
  
  byt = [0] * 45
  j = 0
  for i in range(180):
    n = INTERLEAVE_TABLE_9_20[i]
    if (READ_BIT1(convolved, j) != 0): 
      s0 = 1
    else:  
      s0 = 0
      
    j += 1
    if (READ_BIT1(convolved, j) != 0): 
      s1 = 1
    else:
      s1 = 0
    j += 1
    
    WRITE_BIT1(byt, n, s0)

    n += 1
    WRITE_BIT1(byt, n, s1)
  byt_i = 0
  data_i += 9
    
  for i in range(5):
    for j in range(9):
      data[data_i + j] = byt[byt_i + j]
    data_i += 18
    byt_i += 9        


def writeHeader(data, csd1, csd2):
  writeDataFRModeData1(csd1, data)
  writeDataFRModeData2(csd2, data)  




if __name__ == '__main__':
  #b = b'YSFDIU5JAE    IU5JAE    ALL       >\xd4q\xc9cM m8Dh\xed\x81\xff\xe7\x98\x9b\xf2\x82\xe4T/\xf3\x03\xfb\xc8\xf9\\!8<\xf9\xc7\x0bn\x90H\xa3\x9c\xec\xd9L\xb3(j~v<w\x89\xa3V\x06\xb4Y\x90\xbd\xec\xc8\\\xb7l,\rv/U\r\x805tj{\x91\xae\xce\xc9^\x91\n\x0f?U\x0eA\x11F\xe7\xe0\x02\xe2"\x9d\xec\xc1\xc6\x808x]D\x0fA\xfc\x87\x11\xd9\x9f\xd1\x10\xbf\xdf\xf2\xf5.\xf4\xf3\xe6\xdc\x95g'
  #b = b'YSFDBM_YSF_LNKIU8EKN    ALL       \x00\xd4q\xc9cM\x11m8\xdc\xec"\x01\xff0\x0e\xd0r\x82x\xec`3\x00\x86q}\\ \xa6o\xf8\x93cnNS\x11\x8e\x10\xdf#c\xc0\x17`\x7f\x1c\x88j,\xfa\x06\xe8\x92&\xff\xb1\xb9\xa8Z\xbaF\x92\x10\x14\xbe\x97y\x15t\xd5\xdd\x19\x9cuu\xa8\xf7\x7f\xb8\x11\x10\xf2\xc6?\x01\x17\xe0\xe7\x81y\x9c\x8f=\xef\x0e\x84%\x1eI\x94d\xdc@\xf1\xd9,\x0e!1\xbc\x13s\xf6\r\xfb\xd5\x89\x01\x93'
  b = b'YSFDIU5JAE    IU5JAE    ALL       \x00\xd4q\xc9cM\x11ex\xe0\xfc"\r\xbf\xd6\xe6\xd0Ab\x04\xaa`!\xe3\x80\x87}O\xd27\xac\xcfM\xa3\xd8\x1fM }\xb0\xf4\xc3S\xd8\x1f\xa0\x1f=\xb0\xb4\xad\x1d\xb0:\x97\xc5mq\xb8,\xba\xb0:\x9d9\xe4\xb1\xad\xa4m]\xb9\xb9\x16\xd3\xd9\xad\xa4\xc8\x1f\xb9\xb9\x1b\xf4f\xda\xa3\x0cr\xe4\xc39\x99\xe3\x1a\xa3\x0b\x19\x15\x039\x99\x11\xe0\x9b\xc6?p\x0c\xe2\xe1\x8c\xd3[\xc6;[\x15\xa2\xe1\x84'
  # print(b[35:])
  print(processheaderdata(b[35:]))
  print(m_source)
  print(m_dest)
  print(m_downlink)
  print(m_uplink)


  dt = [0] * 20
  readDataVDModeData2(b[35:], dt)

  #print(dt)
  for c in dt:
    print(chr(c))
  bb = bytearray(b)
 
  data = [0] * 120
  csd1 = [0] * 20
  csd2 = [0] * 20
  csd1 = ('90123FAHuL' + '41/IU5JAE ').encode()
  csd2 = ('IU5JAE    ' + 'IU5JAE    ').encode()
  writeHeader(data, csd1, csd2)
  # si modifica solo il payload
  bb[35 + YSF_SYNC_LENGTH_BYTES + YSF_FICH_LENGTH_BYTES:] = data[YSF_SYNC_LENGTH_BYTES + YSF_FICH_LENGTH_BYTES:]
  print(b)
  print(bb)
  print(processheaderdata(bb[35:]))
  print(m_source)
  print(m_dest)
  print(m_downlink)
  print(m_uplink)      
