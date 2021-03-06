#!/usr/bin/env python
##############################################################################
# dhcp_discover.py - script to get DHCP parameter                            #
# Based on work by Matt, available at                                        #
# http://www.attackvector.org/network-discovery-via-dhcp-using-python-scapy/ #
# Updates May 2012 - Nicolas Biscos (buffer at 0x90 period fr )              #
#                                                                            #
# This program is free software: you can redistribute it and/or modify       #
# it under the terms of the GNU General Public License as published by       #
# the Free Software Foundation, either version 3 of the License, or          #
# (at your option) any later version.                                        #
#                                                                            #
# This program is distributed in the hope that it will be useful,            #
# but WITHOUT ANY WARRANTY; without even the implied warranty of             #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the               #
# GNU General Public License for more details.                               #
#                                                                            #
# This should have received a copy of the GNU General Public License         #
# along with this program. If not, see <http://www.gnu.org/licenses/>.       #
##############################################################################

import sys
# Suppress scapy complaints
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
from getopt import getopt;
from getopt import GetoptError;
from threading import Thread

 
class DHCP_discover:
   def __init__(self):
      ipv6_enabled = 0
      conf.verb = 0
      conf.checkIPaddr = False

   """
   Print syntax help message
   """
   def doHelp(self):
      print """dhcp_discover.py - display DHCP response parameters
   Syntax ./dhcp_discover.py [-i iface] [-h] [-c count] [-t timeout]
      -i iface   interface to listen on
      -c count   number of response to capture (defaulting to 1). Can be useful to detect rogue DHCP server
      -t timeout timeout 
      -h         print this message and exits
   """
   
   """
   Nicely (?) format and display key/values messages
   @param key 
   @param values can be either a string or a tuple or an array.
          Tuples and array are reformatted
   """
   def format(self, key, values):
      if( type(values) == type(()) or type(values) == type([]) ):
         value = ', '.join([str(x) for x in values]);
      else:
         value = values;
      print '[+] %-20s: %s' % (str(key), value)
   
   """
   Hook that parses DHCP options and display them
   @param packet the packet to be analysed
   """
   def dhcp_discover(self, packet):
       self.format('Got response', '');
       src = str(packet[Ether].src);
       dst = str(packet[Ether].dst);
       self.format('Source', src);
       self.format('Destination', dst);
       for opt in packet[DHCP].options:
           if 'end' == opt:
               break
           elif 'pad' == opt:
               break
           if( len(opt) > 1 ):
              self.format(opt[0], opt[1:]);
       print ''
   
   """
   Check whether a packet is a DHCP response
   @param packet packet to be inspected
   @return True if packet is a DHCP response
   """
   def isDHCPResponse(self, packet):
      return packet.haslayer(Ether) and packet[Ether].src != self.mac \
         and packet.haslayer(UDP) and 67 == packet[UDP].sport and 68 == packet[UDP].dport;
   
   """
   Parse command line arguments
   """
   def parseArgs(self):
      self.count = 1;
      self.timeout = 10;
      try:
         opts, garbage = getopt(sys.argv[1:], 'i:hc:t:', ['interface=', 'help', 'timeout=', 'count=']);
      except GetoptError, e:
         print '[!] %s' % str(e) 
         doHelp()
         sys.exit(-1);

      try:
         for k, v in opts:
            if( '-i' == k or '--interface' == k ):
               conf.iface = v
            elif( '-c' == k or '--count' == k ):
               self.count = int(v);
            elif( '-t' == k or '--timeout' == k ):
               timeout=int(v);
            elif( '-h' == k or '--help' == k ):
               self.doHelp();
               sys.exit(0);
      except ValueError, e:
         print '[!] %s' % str(e) 
         sys.exit(-1);

      if( 0 != len(garbage) ):
         print '[*] Extra argument will be ignored'
   
   def run(self):
      self.parseArgs();
       
      try:
         fam,hw = get_if_raw_hwaddr(conf.iface)
         self.mac = get_if_hwaddr(conf.iface)
         
         p  = Ether(dst="ff:ff:ff:ff:ff:ff")
         p /= IP(src="0.0.0.0",dst="255.255.255.255")
         p /= UDP(sport=68,dport=67)
         p /= BOOTP(chaddr=hw)
         p /= DHCP(options=[("message-type","discover")])
         
         print '[+] Sending packet...'
         SendThread(p, count=3).start()
         cap = sniff(lfilter=self.isDHCPResponse, prn=self.dhcp_discover, count=self.count, timeout=self.timeout, store=1);
         if( 0 == len(cap) ):
            print '[!] No response'
      except Exception, e:
         print '[!] %s' % str(e) 

class SendThread(Thread):
   def __init__(self, p, count):
      Thread.__init__(self)
      self.p = p
      self.count = count
   def run(self):
      sendp(self.p, count=self.count)


if( '__main__' == __name__ ):
   DHCP_discover().run()

