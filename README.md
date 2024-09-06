# pYSFReflector3
pYSF3 is a YSF C4FM Multi-stream reflector with DG ID management, open source, written in python3. It needs some libraries that you can install with "pip". It is important that you have sufficient knowledge of linux to install python3 and what is necessary on your server. Manually run the reflector before setting it in the service so that you can view the libraries not present and add them. At the end when everything starts regularly, and you have configured the .ini file you can create and manage the service for the start / stop / restart. please ask to network sysop before starting bridges or similar, if you are planning to manage.

for pYSF3 you need (debian distro):

python3 latest version and libs, so:<br>
sudo apt update<br>
sudo apt install python3 python3-pip<br>
sudo pip install aprslib --break-system-packages<br>
sudo pip install tinydb --break-system-packages<br>
sudo pip install threaded --break-system-packages<br>

than chmod +x YSFReflector<br>
and setup the service

we recommend installing the reflector under the /opt/pysfreflector directory as well as the accessory software (the .ini file).

the configuration file is documented internally, ultimately it is necessary to carefully configure the various sections such as the description and name of the reflector and the path for the log. The network section concerns the listening port (as configured in the ysf world database register) of the reflector, and the json port for communication towards the collector / dashboard. A complete and functional block list (in time reload) to limit disturbances is managed in the /opt/pysfreflector/deny.db file: CS:call (block callsign), AL:call (allowed)...
See first pYSF version on https://github.com/iu5jae/pYSFReflector#muting-matrix and the file ACL_rules.txt for infos
The protections section sets the communication timeout and the limitation to continuous PTT strokes only to test the presence of the repeater. Finally, the aprs section (if enabled) manages the communication towards an aprs server, sending the callsigns complete with ssid if specified.

if used in a "classic" way (mono stream), pYSF3 allows you to receive a connection from an external server (for example BrandMeister) with its associated TG DMR. These settings are configured in the DGID section. Let's see an example:

list = 1,31<BR>
default = 31<BR>
local = 1<BR>

so, the local DG ID (transit only on the repeater in use) is 1, all the rest is managed by the 31 (BM will arrive on this flow). If I connect my hotspot, by default I will be assigned the 31 stream and I will be able to leave the 00 setting on the radio, however everything will be operated on the 31.
Only DG ID 1 and 31 will be able to work on the reflector and will allow me a QSO.

let's see this second example:

list = 1, 9, 31<BR>
default = 31<BR>
local = 1<BR>


At DG ID 9 there are no external connections, BM is configured to arrive on 31 (default), 1 is always the local. In this way, using 9, I will be able to talk to all systems that use the same setting (like a private QSO reserved for the reflector only), but I will not go out to BM

third example, a more advanced configuration:

list = 1, 9, 31, 22<BR>
default = 31<BR>
local = 1<BR>

With this configuration I have 4 DG IDs manageable on the reflector, 1 and 9 for "local and private" configurations, the BM server will arrive on 31 and I will have DG ID 22 for a further external link, using, for example, the ysf_bridge software (to another ysf / xlx / ycs) or ysf2dmr. As TGs are used in the DMR world to switch from one stream to another, in this case I will use DG ID 31 and 22 on the C4FM radio. The change is immediate (the first PTT does not go to the network in order not to disturb).
The last DG ID used is "stored" in /opt/pysreflector/dgid.json so that, in case of disconnection of my hotspot, the next time it is activated it resumes the last DG ID used.

Remember: to set a static flow with a specific DG ID you must rename your gateway link with a -nn (example: IK5XMK-22 or TG22-30 …) at the end of the callsign, as static DG ID (10 total chars! do not exceed this number). This allows you to use external software for linking with specific flow. Of course, the DG ID (-nn) of the gateway must be in the list among those "allowed" in the reflector (list option).

pYSF3 is a multiport connections system. As in the .ini:
aux ports linked statically at DG-ID (empty string if not used)
format:

aux_port =  41:42397, 88:42398

It can be very useful for the diversified management of flows in combination with specific DG IDs. It was tested on BM, requesting the connection on the same pYSF reflector of two TGs and defining the DG ID to a specific port / connection. So, on the BM side, we have two distinct YSF connections to specific ports (FIXED, in dashboard), and on the YSF side, two flows to specific DG IDs.

sysop side of the reflector, the last section of the configuration file adds a useful feature to reduce and combine the presence of multiple YSF reflectors in a single system. In fact, it is possible to combine a flow not only with a port as we have seen previously, but also with a YSF reflector ID (identifier). By doing this, the new pYSF3 will respond to the registry like a normal YSF and it will be possible to manage (and therefore remove the old installation) a single "virtual YSF" on each DG ID. Let's see a practical example:

DG-ID:port <BR>
aux_port =  41:42397, 88:42398

[REFL_ALIAS]<BR>
refl_01 = 88, 0, IT PYSF3-TEST, PYSF3 TEST REF

an alias is created (refl_01, refl_02 and so on) which will contain the following information:
Management DGID, YSF ID of the original reflector, name, description

Note: By entering 0 (zero) instead of the YSF ID, the software will calculate it automatically. This informations are contained in the worldwide register of YSF reflectors (https://register.ysfreflector.de/). At this point, on the register, I can change the destination IP / dns of my old reflector and insert the new IP / port (as in the .ini the port is 42398) for listening to the stream (DG ID 88) configured on pYSF3. That's all, pYSF3 will then manage its normal functions and will also be seen from the outside as the old YSF reflector, without the need to manually intervene on repeater and hotspot configurations. They will be FIXED connections.

finally user side, a convenient function to understand, directly on the radio, on which flow (DG ID) I am operating: the reflector sends (not on the network side) the number of the DG ID before the callsign, for example: 41 / IK5XMK. This funcition is not operative on FIXED connections. See prefix=1 on pysfreflector.ini (DGID section) to manage this feature.

pYSF3 can manage the "return home"; after a TOT of time, bring the repeater / hotspot back to the preset flow. This functionality is managed in the home.db file, by inserting the callsign, dgid "home" and the time after when to return (after a period of inactivity of the repeater). This management is delegated by the reflector sysop. In exceptional cases, a time set to -1 "forces" the remote system to a predetermined dgid.

pYSF3 can manage the "Default DGID" when connecting your hotspot or repeater. You must insert in the Network section of ysfgateway.ini of your system, after the connection reflector indication, the line Options=nn where nn indicates the DGID on which you will be positioned when entering the reflector. It can also be used for BTH (return home), managed independently without the need for server-side intervention.

*****

the collector software is used to receive data from the reflector, manage them (e.g., add description to values) and save them in a database (sqlite3). Also, in this case the possible lack of python libraries must be compensated manually. There is no external configuration file, you need to edit the collector3.py code and work on the configuration section:

- reflector address and port (see json port section in pysfreflector.ini)<BR>
srv_addr_port = ('127.0.0.1', 42223)<BR>

- path and name of the database (check access permissions)<BR>
db = r'/opt/pysfreflector/collector3.db'<BR>

- to show the "blocked streams" by rules<BR>
show_TB = True<BR>

- possible associations to the serial used (BM uses a specific serial for its connection), only for better visualization in dashboard<BR>
ser_lnks = {"BM_2222":"E0C4W", "Cluster GRF":"G0gBJ"}<BR>

- any associations between DG ID and the name of the flow / connection, always for the dashboard view<BR>
gid_desc = {"22":"MP_IT BM-DMR+", "30":"MP_Lazio", … and so on<BR>

For information, the collector, and the dashboard (php pages) can also reside on an external server for maximum operational flexibility (see pysfreflector.ini, network section).
The collector cleans the database every minute of data older than one hour, and in any case always reserves a minimum of records for the presence in the dashboard. To ensure full functionality, run the collector by hand and check on the screen if the radio passages are correctly displayed on the shell, as well as the arrival of the gateways connected to the reflector. Then place it as a service (and with ExecStart=/usr/bin/screen -DmS collector /opt/pysfreflector/collector3.py if you like screen management).

*****

the html / php pages must be inserted in the directory provided within the webserver path, for example /var/www/html/ysf and be accessible as paths. The only configuration required, for each page, is to enter the path and name of the database generated by the collector. See the section and adapt it:

// set path/db name<BR>
$db = new SQLite3('/opt/pysfreflector/collector3.db');<BR>

the webserver must be active with the management of the php language and with the extensions (modules) related to the connection to the sqlite3 database. Check in (for example) /etc/php/7.3/apache2/php.ini if there is no such line:<BR>
extension = sqlite3<BR>
Check on the internet and on the documentation the right configuration for your server regarding the functioning of php and sqlite3. Install / configure as needed and reboot. Try to run manually (php main.php) to see that all works good!

the main.php page displays the QSOs, with useful information such as the status (TC = call terminated, TO = timeout, TX = transmission in progress, WD = reflector watchdog, TB = blocked callsigns - if option selected - ), the gateway from which the flow came, the type of radio and serial, coordinates, and position on openstreet map if transmitted, and more (FICH pachet info). Also, in the footer there are information about the reflector and the active flows. Everything displayed comes from the configuration of the reflector.

the connections page displays the repeaters and hotspots connected, in addition to the bridges present, the IP addresses / ports in use and the DG ID currently active on the system (with description) and which will be used if the radio has DG ID 00. This page also displays the "return home" function if managed, ie after how long a system (repeater or hotspot) must return to the default flow (dgid), in case of inactivity.

blocked in time page reports callsigns in timeout or given wild-PTT. They will be resumed automatically in time.

No form of warranty and support is due from the authors, the software is for amateur and experimental radio use without assurance of proper functioning. The management and maintenance of these software requires a good knowledge of computer science, the linux operating system and networks. The software is open source, manage it as such by recognizing what has been done and following the principles set out. Help your amateur radio friends and spread your knowledge. What is written can change at any time. Good fun

Antonio Matraia IU5JAE<BR>
David Bencini IK5XMK<BR>

Gruppo Radio Firenze<BR>
www.grupporadiofirenze.net<BR>
 
To see a working installation: YSF#22220<br>
  http://ysf22220.dmrbrescia.it/ysf/main.php
