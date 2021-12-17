#   part of pYSFReflector
#
#   based on 
#
#   Copyright (C) 2009-2016 by Jonathan Naylor G4KLX
#   Copyright (C) 2018 by Andy Uribe CA6JAU
#

import ysfconvolution
import golay24128
import crc
import ysfpayload

BIT_MASK_TABLE = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01]

m_fich = []


INTERLEAVE_TABLE = [
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



def WRITE_BIT1(p, i, b):
  if b:
    p[(i)>>3] = (p[(i)>>3] | BIT_MASK_TABLE[(i)&7])
  else:
    p[(i)>>3] = (p[(i)>>3] & (~BIT_MASK_TABLE[(i)&7]))      


def READ_BIT1(p,i):
  return (p[(i)>>3] & BIT_MASK_TABLE[(i)&7])


def decode(byt):
  global m_fich

  ysfconvolution.convolution_start()
   
  for i in range(100):
    n = INTERLEAVE_TABLE[i]
    if (READ_BIT1(byt, n) > 0): 
      s0 = 1
    else:  
      s0 = 0
      
    n += 1
    if (READ_BIT1(byt, n) > 0): 
      s1 = 1
    else:
      s1 = 0

    #print(str(s0) + ';' + str(s1))  
    ysfconvolution.convolution_decode(s0, s1)
	

  output = []
  for i in range(13):
    output.append(0)
  # print(output)
  ysfconvolution.convolution_chainback(output, 96)
  # print(output)
  
  b0 = golay24128.decode24128([output[0], output[1], output[2]])
  b1 = golay24128.decode24128([output[3], output[4], output[5]])
  b2 = golay24128.decode24128([output[6], output[7], output[8]])
  b3 = golay24128.decode24128([output[9], output[10], output[11]])

  # print(b0)
  # print(b1)
  # print(b2)
  # print(b3)

  m_fich = [0,0,0,0,0,0]
  
  m_fich[0] = (b0 >> 4) & 0xFF
  m_fich[1] = ((b0 << 4) & 0xF0) | ((b1 >> 8) & 0x0F)
  m_fich[2] = (b1 >> 0) & 0xFF
  m_fich[3] = (b2 >> 4) & 0xFF
  m_fich[4] = ((b2 << 4) & 0xF0) | ((b3 >> 8) & 0x0F)
  m_fich[5] = (b3 >> 0) & 0xFF

  if crc.checkCCITT162(m_fich, 6):
    return m_fich
  else:
    return []


def encode(byt):
  global m_fich
  crc.addCCITT162(m_fich, 6)

  b0 = ((m_fich[0] << 4) & 0xFF0) | ((m_fich[1] >> 4) & 0x00F)
  b1 = ((m_fich[1] << 8) & 0xF00) | ((m_fich[2] >> 0) & 0x0FF)
  b2 = ((m_fich[3] << 4) & 0xFF0) | ((m_fich[4] >> 4) & 0x00F)
  b3 = ((m_fich[4] << 8) & 0xF00) | ((m_fich[5] >> 0) & 0x0FF)

  c0 = golay24128.encode24128(b0)
  c1 = golay24128.encode24128(b1)
  c2 = golay24128.encode24128(b2)
  c3 = golay24128.encode24128(b3)
  
  conv = [0] * 13
  
  conv[0]  = (c0 >> 16) & 0xFF
  conv[1]  = (c0 >> 8) & 0xFF
  conv[2]  = (c0 >> 0) & 0xFF
  conv[3]  = (c1 >> 16) & 0xFF
  conv[4]  = (c1 >> 8) & 0xFF
  conv[5]  = (c1 >> 0) & 0xFF
  conv[6]  = (c2 >> 16) & 0xFF
  conv[7]  = (c2 >> 8) & 0xFF
  conv[8]  = (c2 >> 0) & 0xFF
  conv[9]  = (c3 >> 16) & 0xFF
  conv[10] = (c3 >> 8) & 0xFF
  conv[11] = (c3 >> 0) & 0xFF
  conv[12] = 0x00
  
  ysfconvolution.convolution_start()
  convolved = [0] * 25
  ysfconvolution.convolution_encode(conv, convolved, 100)
  j = 0
  for i in range(100):
    n = INTERLEAVE_TABLE[i]
    if (READ_BIT1(convolved, j) != 0):
      s0 = True
    else:
      s0 = False     
    j += 1
    if (READ_BIT1(convolved, j) != 0):
      s1 = True
    else:
      s1 = False    
    j += 1

    WRITE_BIT1(byt, n + 40*8, s0)

    n += 1
    WRITE_BIT1(byt, n + 40*8, s1)
	
  
    


def getFI():
  return (m_fich[0] >> 6) & 0x03


def getCS():
  return (m_fich[0] >> 4) & 0x03


def getCM():
  return (m_fich[0] >> 2) & 0x03


def getBN():
  return m_fich[0] & 0x03


def getBT():
  return (m_fich[1] >> 6) & 0x03


def getFN():
  return (m_fich[1] >> 3) & 0x07


def getFT():
  return m_fich[1] & 0x07


def getDT():
  return m_fich[2] & 0x03


def getMR():
  return (m_fich[2] >> 3) & 0x03


def getDev():
  return (m_fich[2] & 0x40) == 0x40

def getVoIP():
  return (m_fich[2] & 0x04) == 0x04


def getSQL():
  return (m_fich[3] & 0x80) == 0x80


def getSQ():
  return m_fich[3] & 0x7F


def setFI(fi):
  m_fich[0] &= 0x3F;
  m_fich[0] |= (fi << 6) & 0xC0


def setCS(cs):
  m_fich[0] &= 0xCF
  m_fich[0] |= (cs << 4) & 0x30


def setCM(cm):
  m_fich[0] &= 0xF3
  m_fich[0] |= (cm << 2) & 0x0C


def setFN(fn):
  m_fich[1] &= 0xC7
  m_fich[1] |= (fn << 3) & 0x38


def setFT(ft):
  m_fich[1] &= 0xF8
  m_fich[1] |= ft & 0x07


def setMR(mr):
  m_fich[2] &= 0xC7
  m_fich[2] |= (mr << 3) & 0x38


def setVoIP(on):
  if (on):
    m_fich[2] |= 0x04
  else:
    m_fich[2] &= 0xFB


def setDev(on):
  if (on):
    m_fich[2] |= 0x40
  else:
    m_fich[2] &= 0xBF


def setDT(dt):
  m_fich[2] &= 0xFC
  m_fich[2] |= dt & 0x03


def setSQL(on):
  if (on):
    m_fich[3] |= 0x80
  else:
    m_fich[3] &= 0x7F


def setSQ(sq):
  m_fich[3] &= 0x80
  m_fich[3] |= sq & 0x7F


def setBN(bn):
  m_fich[0] &= 0xFC
  m_fich[0] |= bn & 0x03


def setBT(bt):
  m_fich[1] &= 0x3F
  m_fich[1] |= (bt << 6) & 0xC0



if __name__ == '__main__':
  b = b'YSFDIU5JAE    IU5JAE    ALL       >\xd4q\xc9cM m8Dh\xed\x81\xff\xe7\x98\x9b\xf2\x82\xe4T/\xf3\x03\xfb\xc8\xf9\\!8<\xf9\xc7\x0bn\x90H\xa3\x9c\xec\xd9L\xb3(j~v<w\x89\xa3V\x06\xb4Y\x90\xbd\xec\xc8\\\xb7l,\rv/U\r\x805tj{\x91\xae\xce\xc9^\x91\n\x0f?U\x0eA\x11F\xe7\xe0\x02\xe2"\x9d\xec\xc1\xc6\x808x]D\x0fA\xfc\x87\x11\xd9\x9f\xd1\x10\xbf\xdf\xf2\xf5.\xf4\xf3\xe6\xdc\x95g'
  b = b'YSFDBM_YSF_LNKIU8EKN    ALL       \x00\xd4q\xc9cM\x11m8\xdc\xec"\x01\xff0\x0e\xd0r\x82x\xec`3\x00\x86q}\\ \xa6o\xf8\x93cnNS\x11\x8e\x10\xdf#c\xc0\x17`\x7f\x1c\x88j,\xfa\x06\xe8\x92&\xff\xb1\xb9\xa8Z\xbaF\x92\x10\x14\xbe\x97y\x15t\xd5\xdd\x19\x9cuu\xa8\xf7\x7f\xb8\x11\x10\xf2\xc6?\x01\x17\xe0\xe7\x81y\x9c\x8f=\xef\x0e\x84%\x1eI\x94d\xdc@\xf1\xd9,\x0e!1\xbc\x13s\xf6\r\xfb\xd5\x89\x01\x93'
  # b = b'YSFDIU5JAE    IU5JAE    ALL       \x00\xd4q\xc9cM\x11ex\xe0\xfc"\r\xbf\xd6\xe6\xd0Ab\x04\xaa`!\xe3\x80\x87}O\xd27\xac\xcfM\xa3\xd8\x1fM }\xb0\xf4\xc3S\xd8\x1f\xa0\x1f=\xb0\xb4\xad\x1d\xb0:\x97\xc5mq\xb8,\xba\xb0:\x9d9\xe4\xb1\xad\xa4m]\xb9\xb9\x16\xd3\xd9\xad\xa4\xc8\x1f\xb9\xb9\x1b\xf4f\xda\xa3\x0cr\xe4\xc39\x99\xe3\x1a\xa3\x0b\x19\x15\x039\x99\x11\xe0\x9b\xc6?p\x0c\xe2\xe1\x8c\xd3[\xc6;[\x15\xa2\xe1\x84'
  
  a=bytearray(b)
  
  print(decode(a[40:]))

  print('FI = ' + str(getFI()))
  print('CS = ' + str(getCS()))
  print('Cm = ' + str(getCM()))
  print('DT = ' + str(getDT()))
  print('FN/FT = ' + str(getFN()) + '/' + str(getFT()))
  print('MR = ' + str(getMR()))
  print('VoIP = ' + str(getVoIP()))
  print('Dev = ' + str(getDev()))
  print('SQL = ' + str(getSQL()))
  print('SQ = ' + str(getSQ()))
  print('BN/BT = ' + str(getBN()) + '/' + str(getBT()))
  encode(a[40:])
  print(b[40:])
  print(a[40:])
