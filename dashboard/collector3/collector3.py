#!/usr/bin/python3

#    Collector3  - this is a software for store data from pYSFReflector3 (by IU5JAE) in a sqlite3 db
#
#    Created by David Bencini (IK5XMK) on 01/11/2021.
#    Copyright 2021 David Bencini (IK5XMK). All rights reserved.

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket
import threading
import time
import json
import sys
from   threading import Lock
import datetime as dt
from   datetime import datetime
import re
import sqlite3
import os
import random

# *** CONFIG SECTION ***
# set your pYSF3 (Json section in pysfreflector.ini) address and port
srv_addr_port = ('127.0.0.1', 42223)

# set database name anche path (r = raw string)
db = r'/opt/pysfreflector/collector3.db'

# show TB (blocked by rules) streams on dashboard? True/False
show_TB = True

# do you have special links ? set the descr/serial
ser_lnks = {"BM_2222":"E0C4W", "XLX-Link":"G0gBJ","BlueDV":"F5ZFW"}

# do you need DGID/Descriptions ?
gid_desc = { "9":"Local_reflector",
	    "22":"MP_Italia",
            "30":"MP_Lazio",
            "31":"MP_Sardegna",
            "32":"MP_Umbria",
            "33":"MP_Liguria",
            "34":"MP_Piemonte",
            "35":"MP_V.Aosta",
            "36":"MP_Lombardia",
            "37":"MP_Friuli VG",
            "38":"MP_Trentino AA",
            "39":"MP_Veneto",
            "40":"MP_Emilia R.",
            "41":"MP_Toscana",
            "42":"MP_Abruzzo",
            "43":"MP_Marche",
            "44":"MP_Puglia",
            "45":"MP_Basilicata",
            "46":"MP_Calabria",
            "47":"MP_Campania",
            "48":"MP_Molise",
            "49":"MP_Sicilia"}
# *** END CONFIG SECTION ***

# common
VERSION  = "testing15" # new Yaesu FTM-200 code
conn_msg = "CONNREQ"
bye_msg  = "BYE"
buffer   = 1024
t_out    = 0
t_start  = ""
t_end    = ""

# reflector
aprs_active = ""
aprs_ssid = None

# streams
strm_rec = {}

# linked systems
lnkd_rec = {}
cl_lst = False

# blocked callsigns
blck_rec = {}
cl_lst_blk = False
strm_blk = {}

lock = Lock()

def create_connection(db_file):
    if os.path.exists(db_file):
        os.remove(db_file)
        print("old db removed")
    else:
        print("db doesn't exist, make new one and connect it")    
    conn = None
    conn = sqlite3.connect(db_file, check_same_thread=False)
    return conn

def get_start_time_from_db(_st_id):
    lock.acquire()
    sql = "SELECT time FROM streams WHERE stream_id = '" + _st_id + "';"
    c = conn.cursor()
    c.execute(sql)
    record = c.fetchone()
    lock.release()
    try:
        t_start = record[0]
    except:
        t_start = ''
    return(t_start)
    
def obscure_IP(IP): # privacy rule
    global obs_IP
    tmp = IP.split(".")
    tmp[3] = "***" # hide only last byte
    my_ip = tmp[0] + "." + tmp[1] + "." + tmp[2] + "." + tmp[3]
    return(my_ip)

def calc_qso_time(t2, t1):
    d = "999"
    try:
        start_dt = dt.datetime.strptime(t1, '%H:%M:%S')
        end_dt = dt.datetime.strptime(t2, '%H:%M:%S')
        diff = (end_dt - start_dt) 
        diff.seconds/60
        d = str(diff)
    except:
        pass
    return(d)

def purge_call(call): 
    pattern = r'[/-]' 
    re_call = re.sub(pattern,"+",call) 
    res = re_call.find("+")
    if ( res > 0 ):
        my_call = re_call[:res]
    else:
        my_call = call
    return(my_call)

def add_time():
    return (time.strftime("%Y:%m:%d %H:%M:%S", time.localtime()))

def pingpong(s):
    global srv_addr_port
    while True:
        s.sendto(b'PING',  srv_addr_port)
        time.sleep(10)

def timeout(s):
    while True:
        global bye_msg
        global srv_addr_port
        global t_out
        lock.acquire()
        t_out = t_out + 1
        lock.release()
        if ( t_out == 60 ):
            print(add_time() + " timeout, no PONG answer from server")
            s.sendto(str.encode(bye_msg), srv_addr_port)
            time.sleep(3)
            print(add_time() + " sent BYE, and call the server again (waiting for 60 secs)")
            s.sendto(str.encode(conn_msg), srv_addr_port)
            lock.acquire()
            t_out = 0
            lock.release()
        time.sleep(1)

# *** STREAMS TABLE        
def insert_new_stream_in_table(rec):
    lock.acquire()
    now = datetime.now() # current date and time
    date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    sql_insert_values = "INSERT INTO streams VALUES ('" + rec["status"] + "', \
                                                     '" + rec["stream_id"] + "', \
                                                     '" + rec["call"] + "', \
                                                     '" + rec["target"] + "', \
                                                     '" + rec["gw"] + "', \
                                                     '" + rec["dgid"] + "', \
                                                     '" + rec["gid_desc"] + "', \
                                                     '" + rec["time"] + "', \
                                                     '" + rec["CS"] + "', \
                                                     '" + rec["CM"] + "', \
                                                     '" + rec["FT"] + "', \
                                                     '" + rec["Dev"] + "', \
                                                     '" + rec["MR"] + "', \
                                                     '" + rec["VoIP"] + "', \
                                                     '" + rec["DT"] + "', \
                                                     '" + rec["SQL"] + "', \
                                                     '" + rec["SQC"] + "', \
                                                     '" + rec["latitude"] + "', \
                                                     '" + rec["longitude"] + "', \
                                                     '" + rec["aprs"] + "', \
                                                     '" + rec["radio_code"] + "', \
                                                     '" + rec["station_id"] + "', \
                                                     '" + rec["radio_id"] + "', \
                                                     '" + rec["dst"] + "', \
                                                     '" + rec["src"] + "', \
                                                     '" + rec["uplink"] + "', \
                                                     '" + rec["downlink"] + "', \
                                                     '" + rec["downlink_id"] + "', \
                                                     '" + rec["uplink_id"] + "', \
                                                     '" + date_time + "');"
    c = conn.cursor()
    c.execute(sql_insert_values)
    conn.commit()
    lock.release()
    print(f"({rec['status']}) {rec['call']} [stream: {rec['stream_id']} dgid: {rec['dgid']}/{rec['gid_desc']} at: {rec['time']}]")

def close_stream_in_table(st_id, _status, _time):
    lock.acquire()
    sql_update_values = "UPDATE streams SET status = '" + _status + "', time = '" + _time + "' WHERE stream_id = '" + st_id + "';"
    c = conn.cursor()
    c.execute(sql_update_values)
    conn.commit()
    lock.release()
    print(f"(TX closing) [stream: {st_id} status: {_status} at: {_time}]")   

def update01_stream_in_table(_st_id, _downlink_id, _uplink_id):
    lock.acquire()
    sql_update_values = "UPDATE streams SET downlink_id = '" + _downlink_id + "', uplink_id = '" + _uplink_id + "'  WHERE stream_id = '" + _st_id + "';"
    c = conn.cursor()
    c.execute(sql_update_values)
    conn.commit()
    lock.release()

def update02_stream_in_table(_st_id, _station_id, _radio_id):
    lock.acquire()
    if ( _radio_id == "" ):
        # check in db if DT = 3 then radio_id = target[5:]
        sql = "SELECT DT, target  FROM streams WHERE stream_id ='"+ _st_id +"';"
        c = conn.cursor()
        c.execute(sql)
        record = c.fetchone()
        DT = record[0]
        target = record[1]
        if ( DT == "3"):
            _radio_id = target[5:]
    sql_update_values = "UPDATE streams SET station_id = '" + _station_id + "', radio_id = '" + _radio_id + "'  WHERE stream_id = '" + _st_id + "';"
    c = conn.cursor()
    c.execute(sql_update_values)
    conn.commit()
    lock.release()   

def update03_stream_in_table(_st_id, _radio_code):
    lock.acquire()
    # yaesu rtx models 
    if ( _radio_code =="43" ):
        _radio_code = "FT-70D"
    elif ( _radio_code =="48" ):
        _radio_code = "FT- 3D"
    elif ( _radio_code =="39" ):
        _radio_code = "FT-991"
    elif ( _radio_code =="52" ):
        _radio_code = "FTM500" # update 17.05.2023
    elif ( _radio_code =="37" ):
        _radio_code = "FTM400"
    elif ( _radio_code =="49" ):
        _radio_code = "FTM300"
    elif ( _radio_code =="55" ):
        _radio_code = "FTM310" # update 25.11.2025
    elif ( _radio_code =="36" ):
        _radio_code = "FT-1XD"
    elif ( _radio_code =="46" ):
        _radio_code = "FT7250"
    elif ( _radio_code =="40" ):
        _radio_code = "FT- 2D"
    elif ( _radio_code =="41" ):
        _radio_code = "FTM100"
    elif ( _radio_code =="51" ):
        _radio_code = "FT- 5D"
    elif ( _radio_code =="45" ):
        _radio_code = "FT3207"	
    elif ( _radio_code =="50" ): # update 02.10.2022
        _radio_code = "FTM200"
    elif ( _radio_code =="53" ): # update 28.03.2025
        _radio_code = "FTM510"
    elif ( _radio_code =="42" ): # update 28.03.2025
        _radio_code = "FTM3200"        
    # check in db if radio_id match a serial, so it is a link/bridge 
    sql = "SELECT radio_id FROM streams WHERE stream_id ='"+ _st_id +"';"
    c = conn.cursor()
    c.execute(sql)
    record = c.fetchone()
    try:
        radio_id = record[0]
    except:
        radio_id = 'unknown'
    radio_id = record[0]
    for key in ser_lnks:
        if ( ser_lnks[key] == radio_id ):
            _radio_code = key
            break
    sql_update_values = "UPDATE streams SET radio_code = '" + _radio_code + "' WHERE stream_id = '" + _st_id + "';"
    c = conn.cursor()
    c.execute(sql_update_values)
    conn.commit()
    lock.release()

def update04_stream_in_table(_st_id, _latitude, _longitude):
    lock.acquire()
    sql_update_values = "UPDATE streams SET latitude = '" + _latitude + "', longitude = '" + _longitude + "'  WHERE stream_id = '" + _st_id + "';"
    c = conn.cursor()
    c.execute(sql_update_values)
    conn.commit()
    lock.release()

def update05_stream_in_table(_st_id, _dst, _src, _uplink, _downlink):
    lock.acquire()
    sql_update_values = "UPDATE streams SET dst = '" + _dst + "', src = '" + _src + "', uplink = '" + _uplink + "', downlink = '" + _downlink + "' WHERE stream_id = '" + _st_id + "';"
    c = conn.cursor()
    c.execute(sql_update_values)
    conn.commit()
    lock.release()

# *** REFLECTOR INFO TABLE
def update_reflector_table(rec):
    global aprs_active
    global aprs_ssid
    now = datetime.now() # add starting connection date and time
    date_time = now.strftime("%Y-%m-%d %H:%M:%S")    
    lock.acquire()
    sql_insert_values = "INSERT INTO reflector (system,ver,REF_ID,REF_NAME,REF_DESC,date_time,APRS_EN,APRS_SSID,contact,web,dgid_loc,dgid_def,dgid_list) \
                         VALUES ('" + rec["system"] + "', \
                                 '" + rec["ver"] + "', \
                                 '" + rec["REF_ID"] + "', \
                                 '" + rec["REF_NAME"] + "', \
                                 '" + rec["REF_DESC"] + "', \
                                 '" + date_time + "', \
                                 '" + rec["APRS_EN"] + "', \
                                 '" + rec["APRS_SSID"] + "', \
                                 '" + rec["contact"] + "', \
                                 '" + rec["web"] + "', \
                                 '" + rec["dgid_loc"] + "', \
                                 '" + rec["dgid_def"] + "', \
                                 '" + rec["dgid_list"] + "');"
    c = conn.cursor()
    c.execute(sql_insert_values)
    conn.commit()
    lock.release()
    aprs_active = rec["APRS_EN"]
    aprs_ssid = rec["APRS_SSID"]
    print(f"reflector: {rec['REF_ID']} aprs: {rec['APRS_EN']} ready at: " + add_time())

# *** CONNCTED TABLE
def update_connected_table(rec):
    print(f"==>linked GW:{rec['call']}:{rec['DGID']}:{rec['T_HOLD']}:{rec['BTH_DGID']}")
    lock.acquire()
    sql_insert_values = "INSERT INTO connected (linked,call,IP,port,TC,CF,LO,LK,DGID,T_HOLD,BTH_DGID,BTH_TOUT,BTH_TCORR) \
                         VALUES ('" + rec["linked"] + "', \
                                 '" + rec["call"] + "', \
                                 '" + rec["IP"] + "', \
                                 '" + rec["port"] + "', \
                                 '" + rec["TC"] + "', \
                                 '" + rec["CF"] + "', \
                                 '" + rec["LO"] + "', \
                                 '" + rec["LK"] + "', \
                                 '" + rec["DGID"] + "', \
                                 '" + rec["T_HOLD"] + "', \
                                 '" + rec["BTH_DGID"] + "', \
                                 '" + rec["BTH_TOUT"] + "', \
                                 '" + rec["BTH_TCORR"] + "');"
    c = conn.cursor()
    c.execute(sql_insert_values)
    conn.commit()
    lock.release()
    print("gw inserted in table at " + add_time())

# *** BLOCKED TABLE
def update_blocked_table(rec):
    lock.acquire()
    sql = "SELECT call FROM blocked WHERE call ='" + rec['call'] + "';"
    c = conn.cursor()
    c.execute(sql)
    if ( len(c.fetchall()) > 0 ): 
        print(f"{rec['call']} is blocked and already in db")
    else:
        sql_insert_values = "INSERT INTO blocked (time,call,BR,TR) \
                             VALUES ('" + rec["time"] + "', \
                                     '" + rec["call"] + "', \
                                     '" + rec["BR"] + "', \
                                     '" + rec["TR"] + "');"
        c = conn.cursor()
        c.execute(sql_insert_values)
        conn.commit()
        print(f"{rec['call']} inserted in blocked table at {rec['time']}")
    lock.release()

def rcv(s):
    global cl_lst
    global cl_lst_blk
    global aprs_active
    global aprs_ssid
    global gid_desc
    global show_TB
    while True:
        try:
            msg,adr = s.recvfrom(buffer)
            if ( msg == b"PONG" ):
                global t_out
                lock.acquire()
                t_out = 0
                lock.release()
                continue
            if ( msg[0:6] == b"CONNOK" ):
                answer = msg.decode("utf-8")
                p = answer.split(":")
                print(f"\nserver answered, established with my IP:{p[1]} PORT:{p[2]}\n")
                print(f"show TB status:{show_TB}\n")
                try:
                    sql = "DELETE FROM reflector;"
                    c = conn.cursor()
                    c.execute(sql)
                    conn.commit()
                except:
                    pass
            else: 
                # load the json data to a string
                resp = json.loads(msg)
                
                for item in resp:
                    # reflector info                    
                    if ( item == "system" ):
                        time.sleep(1)
                        update_reflector_table(resp)
                        continue
                    
                    # starting stream
                    if ( item == "stream_start" ):
                        strm_rec["status"]    = "TX"
                        strm_rec["stream_id"] = resp["stream_start"]
                        strm_rec["call"]      = resp["call"]
                        strm_rec["target"]    = resp["target"]  
                        strm_rec["gw"]        = resp["gw"]
                        strm_rec["dgid"]      = resp["dgid"]
                        strm_rec["gid_desc"]  = gid_desc.get(resp["dgid"], "not assigned") # returns the value for the specified ID
                        temp = str.split(resp["time"])
                        strm_rec["time"]      = temp[1][:8] # begin TX time
                        strm_rec["CS"]        = resp["CS"]
                        if ( resp["CM"] == "0" ):
                            strm_rec["CM"] = "Group/CQ"
                        elif ( resp["CM"] == "1" ):
                            strm_rec["CM"] = "Radio ID"
                        elif ( resp["CM"] == "2" ):
                            strm_rec["CM"] = "Reserve"
                        else:
                            strm_rec["CM"] = "Individual"
                        strm_rec["FT"]  = resp["FT"]
                        if ( resp["Dev"] == "False" ):
                            strm_rec["Dev"] = "Wide"
                        else:
                            strm_rec["Dev"] = "Narrow"
                        strm_rec["MR"]   = resp["MR"]
                        strm_rec["VoIP"] = resp["VoIP"]
                        if ( resp["DT"] == "0" ):
                            strm_rec["DT"] = "V/D mode 1"
                        elif ( resp["DT"] == "1" ):
                            strm_rec["DT"] = "Data FR"
                        elif ( resp["DT"] == "2" ):
                            strm_rec["DT"] = "V/D mode 2"
                        else:
                            strm_rec["DT"]  = "Voice FR"
                        strm_rec["SQL"]         = resp["SQL"]
                        strm_rec["SQC"]         = resp["SQC"]
                        strm_rec["latitude"]    = ""
                        strm_rec["longitude"]   = ""
                        if ( aprs_active == "1" ):
                            strm_rec["aprs"]        = "https://aprs.fi/" + purge_call(resp["call"]) + aprs_ssid
                        else:
                            strm_rec["aprs"] = ""
                        strm_rec["radio_code"]  = ""
                        strm_rec["station_id"]  = ""
                        strm_rec["radio_id"]    = resp["target"][-5:]
                        strm_rec["dst"]         = ""
                        strm_rec["src"]         = ""
                        strm_rec["uplink"]      = ""
                        strm_rec["downlink"]    = ""
                        strm_rec["downlink_id"] = ""
                        strm_rec["uplink_id"]   = ""                    
                        insert_new_stream_in_table(strm_rec)
                        continue

                    if ( item == "stream_id01" ):
                        _st_id       = resp["stream_id01"]
                        _downlink_id = resp["Rem1+2"][:5]
                        _uplink_id   = resp["Rem1+2"][5:]
                        update01_stream_in_table(_st_id, _downlink_id, _uplink_id)
                        continue
                      
                    if ( item == "stream_id02" ):
                        _st_id      = resp["stream_id02"]
                        _station_id = resp["Rem3+4"][:5]
                        _radio_id   = resp["Rem3+4"][5:]
                        update02_stream_in_table(_st_id, _station_id, _radio_id)
                        continue

                    if ( item == "stream_id03" ):
                        _st_id      = resp["stream_id03"]
                        _radio_code = resp["radio_code"]
                        update03_stream_in_table(_st_id, _radio_code)
                        continue

                    if ( item == "stream_id04" ):
                        _st_id     = resp["stream_id04"]
                        _latitude  = resp["latitude"][:9].ljust(9, "0") 
                        _longitude = resp["longitude"][:9].ljust(9, "0")
                        update04_stream_in_table(_st_id, _latitude, _longitude)
                        continue

                    if ( item == "stream_id05" ):
                        _st_id    = resp["stream_id05"]
                        _dst      = resp["dst"]
                        _src      = resp["src"]
                        _uplink   = resp["uplink"]
                        _downlink = resp["downlink"]
                        update05_stream_in_table(_st_id, _dst, _src, _uplink, _downlink)
                        continue

                    # closing stream / status can be TC (regular) WD (watchdog) and TD (changing dgid)
                    if ( item == "stream_end" ):
                        _st_id = resp["stream_end"]
                        _status = resp["type"]
                        t_end = resp["time"]
                        temp = str.split(resp["time"])
                        _time = temp[1][:8] # stop TX time
                        t_end = _time
                        t_start = get_start_time_from_db(_st_id)    
                        d = calc_qso_time(t_end, t_start)
                        # _time = datetime.today().strftime('%A')[:3] + " " + _time + "(" + str(d[2:])+ ")"
                        _time = _time + "(" + str(d[2:])+ ")"
                        close_stream_in_table(_st_id, _status, _time) 
                        continue

                    # qso too long!!
                    if ( item == "stream_timeout" ):
                        _st_id     = resp["stream_timeout"]
                        _status = "TO" # timeout
                        t_end = resp["time"]
                        temp = str.split(resp["time"])
                        _time = temp[1][:8] # stop TX time
                        t_end = _time
                        t_start = get_start_time_from_db(_st_id) 
                        d = calc_qso_time(t_end, t_start)
                        #_time = datetime.today().strftime('%A')[:3] + " " + _time + "(" + str(d[2:])+ ")"
                        _time = _time + "(" + str(d[2:])+ ")"
                        close_stream_in_table(_st_id, _status, _time) # as normal ending qso for me
                        continue

                    # blocked (by rules) as invalid callsign, invalid suffix, etc. THEY ARE IN STREAMS TABLE
                    if ( item == "blocked" and show_TB == True ):
                        print(f"==> blocked (by rules) callsign:{resp['CS']} at: {resp['time']} reason: {resp['BR']}")
                        if ( resp['BR'] == "CS" ): # no Wires-X query (DT), only callsign problems
                            strm_blk["status"]    = "TB"
                            strm_blk["stream_id"] = str(random.randint(0, 9999999)) # i need a new stream (not given by pYSF3)
                            strm_blk["call"]      = resp["CS"]
                            strm_blk["gw"]        = resp["GW"]
                            temp = str.split(resp["time"])
                            strm_blk["time"]      = temp[1][:8] # begin TX time
                            strm_blk["gid_desc"]  = "Blocked: " + resp["BR"]
                            # fields not used in this situation
                            strm_blk["target"]      = ""
                            strm_blk["dgid"]        = ""
                            strm_blk["CS"]          = ""
                            strm_blk["CM"]          = ""
                            strm_blk["FT"]          = ""
                            strm_blk["Dev"]         = ""
                            strm_blk["MR"]          = ""
                            strm_blk["VoIP"]        = ""
                            strm_blk["DT"]          = ""
                            strm_blk["SQL"]         = ""
                            strm_blk["SQC"]         = ""
                            strm_blk["latitude"]    = ""
                            strm_blk["longitude"]   = ""
                            strm_blk["aprs"]        = ""
                            strm_blk["radio_code"]  = ""
                            strm_blk["station_id"]  = ""
                            strm_blk["radio_id"]    = ""
                            strm_blk["dst"]         = ""
                            strm_blk["src"]         = ""
                            strm_blk["uplink"]      = ""
                            strm_blk["downlink"]    = ""
                            strm_blk["downlink_id"] = ""
                            strm_blk["uplink_id"]   = ""
                            now = datetime.now() # current date and time
                            strm_blk["date_time"]  = now.strftime("%Y-%m-%d %H:%M:%S")
                            insert_new_stream_in_table(strm_blk)
                        continue

                    # linked gateways
                    if ( item == "linked" ):
                        if ( cl_lst == True ): # we can start with an empty list
                            lock.acquire()
                            try:
                                sql = "DELETE FROM connected;"
                                c = conn.cursor()
                                c.execute(sql)
                                conn.commit()
                                print("gw list erased")
                                cl_lst = False
                            except:
                                pass
                            lock.release()
                        lnkd_rec["linked"] = resp["linked"]
                        lnkd_rec["call"]   = resp["call"]
                        lnkd_rec["IP"]     = obscure_IP(resp["IP"]) # privacy rule
                        lnkd_rec["port"]   = resp["port"]
                        lnkd_rec["TC"]     = resp["TC"]
                        lnkd_rec["CF"]     = resp["CF"]
                        if ( resp["LO"] == "0" ):
                            lnkd_rec["LO"] = "No"
                        else:
                            lnkd_rec["LO"] = "Yes"
                        if ( resp["LK"] == "0" ):
                            lnkd_rec["LK"] = "No"
                        else:
                            lnkd_rec["LK"] = "Yes"
                        lnkd_rec["DGID"]   = resp["DGID"] + " (" +  gid_desc.get(resp["DGID"], "not assigned") + ")" # returns the value for the specified ID
                        if ( resp["T_HOLD"] == "0" ):
                            lnkd_rec["T_HOLD"] = "Movable"
                        elif ( resp["T_HOLD"] == "-1" ):
                            lnkd_rec["T_HOLD"] = "Fixed"
                        elif ( resp["T_HOLD"] == "-2" ):
                            lnkd_rec["T_HOLD"] = "Fixed/BTH"
                        else:
                            lnkd_rec["T_HOLD"] = resp["T_HOLD"]
                        if ( resp["BTH_DGID"] == "0" ): # back to home function
                            lnkd_rec["BTH_DGID"] = "Unset"
                        else:
                            lnkd_rec["BTH_DGID"] = resp["BTH_DGID"]
                        lnkd_rec["BTH_TOUT"]  = resp["BTH_TOUT"]
                        lnkd_rec["BTH_TCORR"] = resp["BTH_TCORR"]
                        update_connected_table(lnkd_rec)
                        continue

                    if ( item == "total_linked" ):
                        print(f"received {resp['total_linked']} gws")
                        cl_lst = True # linked gw list can be cleared next time
                        # but...
                        # use this procedure to purge streams (older than 1 hour)
                        lock.acquire()
                        c = conn.cursor()
                        c.execute("SELECT date_time FROM streams;")
                        if ( len(c.fetchall()) > 100 ): # check to delete records if only > 100
                            sql_purge_streams = "DELETE FROM streams WHERE date_time < datetime('now', '-1 hour');"
                            c = conn.cursor()
                            c.execute(sql_purge_streams)
                            rd = c.rowcount
                            conn.commit()
                            print(f"* purged ({rd})old streams (older than 1 hour)")
                        else:
                            pass 
                        lock.release()
                        #
                        if ( resp["total_linked"] == "0" ):
                            # clear now!
                            lock.acquire()
                            try:
                                sql = "DELETE FROM connected;"
                                c = conn.cursor()
                                c.execute(sql)
                                conn.commit()
                                print("no gws in reflector")
                            except:
                                pass
                            lock.release()
                        continue

                    # blocked callisgns (in time only)
                    if ( item == "blk_time" ):
                        # blck_rec["blk_time"] = resp["blk_time"]
                        blck_rec["time"] = add_time()
                        blck_rec["call"] = resp["call"]
                        if ( resp["BR"] == "RCT" ):
                            blck_rec["BR"] = "TX Timeout"
                        else:
                            blck_rec["BR"] = "Wild PTT"
                        blck_rec["TR"] = resp["TR"]
                        cl_lst_blk = False # set switch for data in blocked table
                        update_blocked_table(blck_rec)
                        continue

                    if ( item == "total_blk_time" ):
                        if ( resp["total_blk_time"] == "0" ):
                            # is table blocked cleared ?
                            if ( cl_lst_blk == True ):
                                print("no blocked callsigns in reflector (in time)")
                            else:    
                                lock.acquire()
                                try:
                                    sql = "DELETE FROM blocked;"
                                    c = conn.cursor()
                                    c.execute(sql)
                                    conn.commit()
                                    print("blocked list erased before new data")
                                    cl_lst_blk = True
                                except:
                                    pass
                                lock.release()                            
                            
        except Exception as e:
            print(str(e))

print(f"starting... version: {VERSION}")

# init and start socket/conn pYSF server
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.sendto(str.encode(conn_msg), srv_addr_port)
print("done - socket connection with pYSF3 server")

# init threads
threading.Thread(target=pingpong,args=(UDPClientSocket,)).start()      
threading.Thread(target=rcv,args=(UDPClientSocket,)).start()
threading.Thread(target=timeout,args=(UDPClientSocket,)).start()
print("done - threads initialized")

# init database
conn = create_connection(db)
# define fields in tables
sql_create_reflector_table = """
                             CREATE TABLE reflector (
                             ID INTEGER PRIMARY KEY AUTOINCREMENT,
                             system TEXT,
                             ver TEXT,
                             REF_ID TEXT NOT NULL,
                             REF_NAME TEXT,
                             REF_DESC TEXT,
                             date_time TEXT,
                             APRS_EN TEXT,
                             APRS_SSID TEXT,
                             contact TEXT,
                             web TEXT,
                             dgid_loc TEXT,
                             dgid_def TEXT,
                             dgid_list TEXT); 
                             """
sql_create_streams_table = """
                           CREATE TABLE streams (
                           status TEXT, 
                           stream_id INTEGER NOT NULL, 
                           call TEXT NOT NULL, 
                           target TEXT, 
                           gw TEXT, 
                           dgid TEXT,
                           gid_desc TEXT,
                           time TEXT, 
                           CS TEXT, 
                           CM TEXT, 
                           FT TEXT, 
                           Dev TEXT, 
                           MR TEXT, 
                           VoIP TEXT, 
                           DT TEXT, 
                           SQL TEXT, 
                           SQC TEXT, 
                           latitude TEXT, 
                           longitude TEXT, 
                           aprs TEXT, 
                           radio_code TEXT, 
                           station_id TEXT, 
                           radio_id TEXT, 
                           dst TEXT, 
                           src TEXT, 
                           uplink TEXT, 
                           downlink TEXT, 
                           downlink_id TEXT, 
                           uplink_id TEXT,
                           date_time TEXT);
                           """ # aprs field is NOT sent by pYSF3, also date_time is used for purge and gid_desc is for easiest on dashboard
sql_create_connected_table = """
                             CREATE TABLE connected (
                             ID INTEGER PRIMARY KEY AUTOINCREMENT,
                             linked TEXT, 
                             call TEXT NOT NULL, 
                             IP TEXT, 
                             port TEXT, 
                             TC TEXT, 
                             CF TEXT, 
                             LO TEXT, 
                             LK TEXT, 
                             DGID TEXT,
                             T_HOLD TEXT,
                             BTH_DGID TEXT,
                             BTH_TOUT TEXT,
                             BTH_TCORR TEXT);
                             """
sql_create_blocked_table = """
                           CREATE TABLE blocked (
                           ID INTEGER PRIMARY KEY AUTOINCREMENT,
                           time TEXT, 
                           call TEXT NOT NULL, 
                           BR TEXT,  
                           TR TEXT);
                           """
# create tables
if conn is not None:
    # create reflector table
    lock.acquire()
    c = conn.cursor()
    c.execute(sql_create_reflector_table)
    lock.release()

    # create streams table
    lock.acquire()
    c = conn.cursor()
    c.execute(sql_create_streams_table)
    c.execute("CREATE INDEX i_date_time on streams(date_time);")
    lock.release()

    # create connected table
    lock.acquire()
    c = conn.cursor()
    c.execute(sql_create_connected_table)
    c.execute("CREATE INDEX i_CF on connected(CF);")
    lock.release()

    # create blocked table
    lock.acquire()
    c = conn.cursor()
    c.execute(sql_create_blocked_table)
    c.execute("CREATE INDEX i_time on blocked(time);")
    lock.release()

    print("done - new db created with empty tables")
else:
    print("can't work with the database, exiting...")
    sys.exit()

# idle status, waiting server input...
while True:
    time.sleep(2)
