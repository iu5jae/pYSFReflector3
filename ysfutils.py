#   part of pYSFReflector
#

import math


def list_to_string(l):
	return ''.join(chr(i) for i in l)


def calculateLocator(latitude, longitude):

  locator = '' 
  if ((latitude < -90.0) or (latitude > 90.0)):
    return "AA00AA"

  if ((longitude < -360.0) or (longitude > 360.0)):
    return "AA00AA";

  latitude += 90.0

  if (longitude > 180.0):
    longitude -= 360.0

  if (longitude < -180.0):
    longitude += 360.0

  longitude += 180.0

  lon = math.floor(longitude / 20.0)
  lat = math.floor(latitude  / 10.0)

  locator += chr(ord('A') + lon)
  locator += chr(ord('A') + lat)

  longitude -= lon * 20.0
  latitude  -= lat * 10.0

  lon = math.floor(longitude / 2.0)
  lat = math.floor(latitude  / 1.0)

  locator += chr(ord('0') + lon)
  locator += chr(ord('0') + lat)

  longitude -= lon * 2.0
  latitude  -= lat * 1.0

  lon = math.floor(longitude / (2.0 / 24.0))
  lat = math.floor(latitude  / (1.0 / 24.0))

  locator += chr(ord('a') + lon)
  locator += chr(ord('a') + lat)

  return locator

    