import socket
import threading
import sys
import signal
from datetime import datetime
from collections import deque


"""
Simple Chat Application Server
-------------------------------------------------
It is a  multi-threaded TCP chat server that allows multiple clients to connect
and communicate with each other in real-time.

Faetures:
- Multi-threaded architecture to handle multiple clients simultaneously
- Broadcasting messages from one client to all connected clients
- Online users list
- Help command
- Client nickname system
- Connection/disconnection notifications
- Gracefull error handling

Extra Credit Features:
- Online users list (/users, /who)
- Message timestamps
- Help command (/help)

"""
class ChatServer:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.sock = None  # main server socket
        self.clients = [] 
        self.names = [] 
        self.recent_msgs = deque(maxlen=10) 
        self.running = False
        self.lock = threading.Lock()  # for thread safety
    
    def get_time(self):
        return datetime.now().strftime('%H:%M:%S')
    
    
    def broadcast(self, msg, skip_client=None, save=False):
        # send message to all clients and if you do not want to send particular person then add there name after messsage it skips that client.
        if isinstance(msg, str):
            msg_text = msg
            msg = msg.encode('utf-8')
        else:
            msg_text = msg.decode('utf-8')
            
        if save:
            with self.lock:
                self.recent_msgs.append(msg_text.strip())
                
        with self.lock:
            clients_list = self.clients[:]
        
        for client in clients_list:
            if client != skip_client:
                try:
                    client.send(msg)
                except:
                    # if sending fails, kick them out
                    self.remove_client(client)
    
    def send_msg(self, client, msg):
        # send message to just one client
        try:
            if isinstance(msg, str):
                msg = msg.encode('utf-8')
            client.send(msg)
            return True
        except:
            return False
    
    def get_users_list(self):
        # get formatted list of who's online
        with self.lock:
            if not self.names:
                return "No other users are online.\n"
            
            users = "Online Users:\n"
            for i, name in enumerate(self.names):
                users += f"  {i+1}. {name}\n"
            users += "\n"  # Add extra newline for spacing
            return users
    
    def send_history(self, client):
        # send recent messages to new client so they can catch up
        with self.lock:
            if self.recent_msgs:
                history = "\n--- Recent Messages ---\n"
                for msg in self.recent_msgs:
                    history += msg + "\n"
                history += "--- End of History ---\n\n"
                self.send_msg(client, history)
    
    def handle_cmd(self, client, name, cmd):
        # handle commands like /quit, /help, etc
        parts = cmd.split(maxsplit=2)
        command = parts[0].lower()
        time = self.get_time()
        
        if command == '/quit':
            self.send_msg(client, 'Goodbye!\n')
            return False
 
        elif command == '/help':
            help_text = """
Available Commands:
  /help                      Show this help message
  /users or /who             List all online users
  /msg <user> <message>      Send private message to specific user
  /quit                      Exit the chat

"""
            self.send_msg(client, help_text)
        
        # list of  users
        elif command in ['/users', '/who']:
            users = self.get_users_list()
            self.send_msg(client, users)
        
        #one to one client communication 
        elif command == '/msg':
            if len(parts) < 3:
                self.send_msg(client, 'Usage: /msg <username> <message>\n\n')
            else:
                target_name = parts[1]
                message = parts[2]
                
                # find the target client
                with self.lock:
                    if target_name not in self.names:
                        self.send_msg(client, f'Error: User "{target_name}" not found.\n\n')
                    else:
                        idx = self.names.index(target_name)
                        target_client = self.clients[idx]
                        
                        # send to target
                        private_msg = f'[{time}] [PRIVATE from {name}]: {message}\n\n'
                        self.send_msg(target_client, private_msg)
                        
                        # confirm to sender
                        self.send_msg(client, f'[{time}] [PRIVATE to {target_name}]: {message}\n\n')
                        
                        print(f'[{time}] [PRIVATE] {name} -> {target_name}: {message}')
        
        else:
            self.send_msg(client, f'Unknown command: {command}. Type /help for available commands.\n\n')
        
        return True
    
    def remove_client(self, client):
        # remove  a client  and notify everyone
        with self.lock:
            if client in self.clients:
                idx = self.clients.index(client)
                name = self.names[idx]
                
                self.clients.remove(client)
                self.names.remove(name)
                
                # tell everyone they left
                time = self.get_time()
                self.broadcast(f'[{time}] SERVER: {name} has left the chat!\n', save=True)
                print(f'[{time}] [DISCONNECTED] {name} has left the chat')
                
                try:
                    client.close()
                except:
                    pass  # ignore errors
    
    def handle_client(self, client, addr):
        # this handles one client's connection in its own thread
        name = None
        try:
            client.send('NICK'.encode('utf-8'))
            name = client.recv(1024).decode('utf-8').strip()
            
            # check if name is already taken
            with self.lock:
                if name in self.names:
                    client.send('ERROR: Nickname already taken!\n'.encode('utf-8'))
                    client.close()
                    return
                
                # add them to the lists
                self.clients.append(client)
                self.names.append(name)
            
            time = self.get_time()
            print(f'[{time}] [CONNECTED] {name} connected from {addr[0]}:{addr[1]}')
            
            # send welcome message
            welcome = f'[{time}] Connected to the chat server!\n'
            welcome += 'Type /help to see available commands.\n\n'
            
            self.send_msg(client, welcome)
            
            # send them recent messages
            self.send_history(client)
            
            # tell everyone they joined
            self.broadcast(f'[{time}] SERVER: {name} has joined the chat!\n', save=True)
            
            while self.running:
                try:
                    data = client.recv(1024)
                    
                    if not data:
                        break
                    
                    msg = data.decode('utf-8').strip()
                    
                    # first check is this command or messagee
                    if msg.startswith('/'):
                        if not self.handle_cmd(client, name, msg):
                            break
                        continue
                    
                    # regular message - broadcast it
                    time = self.get_time()
                    full_msg = f'[{time}] {name}: {msg}\n'
                    print(f'[{time}] [MESSAGE] {name}: {msg}')
                    self.broadcast(full_msg, save=True)
                    
                except ConnectionResetError:
                    break
                except Exception as e:
                    print(f'[ERROR] Error handling client {name}: {str(e)}')
                    break
        
        except Exception as e:
            print(f'[ERROR] Error in client setup: {str(e)}')
        
        finally:
            if client in self.clients:
                self.remove_client(client)
    
    def accept_clients(self):
        # main loop to accept new connections
        time = self.get_time()
        print(f'[{time}] [LISTENING] Server is listening on {self.host}:{self.port}')
        
        while self.running:
            try:
                # timeout so we can check if running changed
                if self.sock:
                    self.sock.settimeout(1.0)
                    try:
                        client, addr = self.sock.accept()
                        
                        # spawn a new thread for this client
                        thread = threading.Thread(target=self.handle_client, args=(client, addr))
                        thread.daemon = True
                        thread.start()
                        
                    except socket.timeout:
                        continue
                        
            except OSError:
                # socket closed
                break
            except Exception as e:
                if self.running:
                    print(f'[ERROR] Error accepting connection: {str(e)}')
    
    def start(self):
        try:
            # socket creation 
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # bind to the address
            self.sock.bind((self.host, self.port))
            
            # start listening
            self.sock.listen()
            
            self.running = True
            
            print('=' * 60)
            print('CHAT SERVER STARTED')
            print('=' * 60)
            print(f'Host: {self.host}')
            print(f'Port: {self.port}')
            print('\nPress Ctrl+C to stop the server')
            print('=' * 60)
            
    
            self.accept_clients()
            
        except Exception as e:
            print(f'[ERROR] Failed to start server: {str(e)}')
            self.stop()
    
    def stop(self):
        # shut down the server
        time = self.get_time()
        print(f'\n[{time}] [SHUTDOWN] Shutting down server...')
        self.running = False
        
        # close all client connections
        with self.lock:
            clients_list = self.clients[:]
        
        for client in clients_list:
            try:
                time = self.get_time()
                client.send(f'[{time}] SERVER: Server is shutting down...\n'.encode('utf-8'))
                client.close()
            except:
                pass  
        
        # close main socket
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        
        time = self.get_time()
        print(f'[{time}] [SHUTDOWN] Server stopped....')


def handle_ctrl_c(sig, frame):
    # handle ctrl+c to shutdown gracefully
    print('\n[SIGNAL] Received interrupt signal')
    if 'server' in globals():
        server.stop()
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_ctrl_c)
    server = ChatServer('127.0.0.1', 5555)
    server.start()
