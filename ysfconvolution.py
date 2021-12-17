#   part of pYSFReflector
#
#   based on 
#
#   Copyright (C) 2009-2016 by Jonathan Naylor G4KLX
#

BIT_MASK_TABLE = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01]

BRANCH_TABLE1 = [0, 0, 0, 0, 1, 1, 1, 1]

BRANCH_TABLE2 = [0, 1, 1, 0, 0, 1, 1, 0]

NUM_OF_STATES_D2 = 8
NUM_OF_STATES = 16
M = 2
K = 5

m_metrics1 = []
m_metrics2 = []
m_oldMetrics = []
m_newMetrics = []
m_dp = []
m_dp_i = 0


def WRITE_BIT1(p, i, b):
  if b:
    p[(i)>>3] = (p[(i)>>3] | BIT_MASK_TABLE[(i)&7])
  else:
    p[(i)>>3] = (p[(i)>>3] & (~BIT_MASK_TABLE[(i)&7]))      


def READ_BIT1(p,i):
  return (p[(i)>>3] & BIT_MASK_TABLE[(i)&7])


def convolution_start():
  global m_metrics1
  global m_metrics2
  global m_metrics1
  global m_oldMetrics
  global m_newMetrics
  global m_dp
  global m_dp_i
  
  m_metrics1 = [0] * NUM_OF_STATES
  m_metrics2 = [0] * NUM_OF_STATES   
  m_dp = [0] * 180

  m_dp_i = 0
  m_oldMetrics = m_metrics1.copy()
  m_newMetrics = m_metrics2.copy()


def convolution_decode(s0, s1):
  global m_dp
  global m_dp_i
  global m_oldMetrics
  global m_newMetrics

  for i in range(NUM_OF_STATES_D2):
    j = i * 2
    metric = ((BRANCH_TABLE1[i] ^ s0) + (BRANCH_TABLE2[i] ^ s1)) & 0xFFFF
    m0 = (m_oldMetrics[i] + metric) & 0xFFFF
    m1 = (m_oldMetrics[i + NUM_OF_STATES_D2] + (M - metric)) & 0xFFFF

    if (m0 >= m1):
      decision0 = 1
    else:
      decision0 = 0  

    if (m0 >= m1):
      m_newMetrics[j + 0] = m1
    else:
      m_newMetrics[j + 0] = m0

    m0 = (m_oldMetrics[i] + (M - metric)) & 0xFFFF
    m1 = (m_oldMetrics[i + NUM_OF_STATES_D2] + metric) & 0xFFFF
    if (m0 >= m1):
      decision1 = 1
    else:
      decision1 = 0  
    if (decision1 != 0):
      m_newMetrics[j + 1] = m1
    else:  
      m_newMetrics[j + 1] = m0
      
    m_dp[m_dp_i] |= ((decision1) << (j + 1)) & 0xFFFFFFFFFFFFFFFF | ((decision0) << (j + 0)) & 0xFFFFFFFFFFFFFFFF

  m_dp_i += 1

  tmp = m_oldMetrics.copy()
  m_oldMetrics = m_newMetrics.copy()
  m_newMetrics = tmp.copy()


def convolution_chainback(out, nBits):
  state = 0
  global m_dp
  global m_dp_i
  #for cf in m_dp:
  #  print(cf)
  while (nBits > 0):
    m_dp_i = m_dp_i - 1
    nBits = nBits - 1
    i = state >> (9 - K)
    bit = ((m_dp[m_dp_i] >> i) & 1) & 0xFF
    state = (bit << 7) | (state >> 1)
    # print(str(nBits) + ';' + str(bit))
    WRITE_BIT1(out, nBits, bit != 0)


def convolution_encode(inp, o, nBits):
  d1 = 0
  d2 = 0
  d3 = 0
  d4 = 0
  k = 0  
  for i in range(nBits):
    if (READ_BIT1(inp, i) > 0):
      d = 1
    else:
      d = 0
    g1 = (d + d3 + d4) & 1
    g2 = (d + d1 + d2 + d4) & 1    
    d4 = d3
    d3 = d2
    d2 = d1
    d1 = d

    WRITE_BIT1(o, k, g1 != 0)
    #print(k)
    k = k + 1

    WRITE_BIT1(o, k, g2 != 0)
   # print(k)
    k = k + 1   
