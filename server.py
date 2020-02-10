import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      # data = str(data)
      data.decode('utf-8')
      print("Got this: "+str(data))
      if addr in clients:
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['position'] = json.loads(data) 
      else:
         if 'connect' in str(data):
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['position'] = "b'{\"x\":0.0,\"y\":0.0,\"z\":0.0}'"
            message = {"cmd": 0,"players":[]} #{"id":addr}}

            p = {}
            p['id'] = str(addr)
            p['position'] = 0
            message['players'].append(p)

            GameState = {"cmd": 4, "players":[]}
            for c in clients:
               if (c == addr):
                  message['cmd'] = 3
               else:
                  message['cmd'] = 0

               m = json.dumps(message,separators=(",", ":"))
               player = {}
               player['id'] = str(c)
               player['position']= clients[c]['position']
               GameState['players'].append(player)
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))

            m = json.dumps(GameState)
            sock.sendto(bytes(m,'utf8'), addr)

def cleanClients(sock):
   while True:
      droppedClients = []
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
            droppedClients.append(str(c))
      
      message = {"cmd": 2, "droppedPlayers":droppedClients}
      m = json.dumps(message,separators=(",", ":"))
      if (len(droppedClients) > 0):
         for c in clients:
            sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
      
      time.sleep(1)

def gameLoop(sock):
   pktID = 0
   while True:
      GameState = {"cmd": 1, "pktID": pktID, "players": []}
      clients_lock.acquire()
#      print (clients)
      for c in clients:
         player = {}
         ##clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         player['id'] = str(c)
         player['position'] = clients[c]['position']
         GameState['players'].append(player)
      s=json.dumps(GameState,separators=(",", ":"))
      print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      if (len(clients)>0):
         pktID = pktID +1
      time.sleep(0.033)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
