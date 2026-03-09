
import socket
import threading
import sys
import signal


# Chat client for connecting to the server
# run this and enter your nickname to start chatting

class ChatClient:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.sock = None  #socket connection
        self.name = None  #user's nickname
        self.running = False
        self.is_connected = False
    
    def format_msg(self, msg):
        return msg.strip()
    
    def receive_msgs(self):
        #runs in background to get messages from server
        while self.running:
            try:
                if self.sock is None:
                    break
                data = self.sock.recv(1024)
                if not data:
                    print('\n[DISCONNECTED] Lost connection to server')
                    self.running = False
                    break
                msg = data.decode('utf-8')
                # this is just the initial handshake, not a message
                if msg == 'NICK':
                    if self.sock and self.name:
                        self.sock.send(self.name.encode('utf-8'))
                else:
                    # Clear current line and print the message
                    print(f'\r{msg}', end='')
                    # Ensure there's a newline after the message
                    if not msg.endswith('\n'):
                        print()
                    # Reprint the prompt
                    print(f'{self.name}: ', end='', flush=True)
                    
            except ConnectionResetError:
                print('\n[ERROR] Connection reset by server')
                self.running = False
                break
            except Exception as e:
                if self.running:
                    print(f'\n[ERROR] Error receiving message: {str(e)}')
                    self.running = False
                break
    
    def send_msgs(self):
        print('\n' + '=' * 60)
        print('Connected to chat server!')
        print('=' * 60)
        print('\nCommands:')
        print('  /help                     Show all commands')
        print('  /users                    List online users')
        print('  /msg <user> <message>     Send private message')
        print('  /quit                     Exit the chat')
        print('=' * 60 + '\n')
        
        while self.running:
            try:
                # get what user types in input
                user_input = input(f'{self.name}: ')
                if not self.running:
                    break
                # ignore empty messages
                if not user_input.strip():
                    continue
                
                # send it to the server
                if self.sock:
                    self.sock.send(user_input.encode('utf-8'))
                
                # for quit
                if user_input.strip().lower() == '/quit':
                    self.running = False
                    break
                    
            except KeyboardInterrupt:
                print('\n[INFO] Use /quit to exit')
                continue
            except EOFError:
                self.running = False
                break
            except Exception as e:
                if self.running:
                    print(f'\n[ERROR] Error sending message: {str(e)}')
                    self.running = False
                break
    
    def connect(self):
        # connect to the server and start chatting.
        try:
            # ask for nickname
            print('=' * 60)
            print('CHAT CLIENT')
            print('=' * 60)
            
            while True:
                self.name = input('Enter your nickname: ').strip()
                if self.name:
                    break
                print('Nickname cannot be empty. Please try again.')
            
            print(f'\nConnecting to {self.host}:{self.port}...')
            
            # make connection
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            
            self.running = True
            self.is_connected = True
            
            # start background thread for receiving
            recv_thread = threading.Thread(target=self.receive_msgs)
            recv_thread.daemon = True
            recv_thread.start()
            
            # main thread handles sending
            self.send_msgs()
            
        except ConnectionRefusedError:
            print(f'\n[ERROR] Could not connect to server at {self.host}:{self.port}')
            print('Make sure the server is running and the address is correct.')
        except Exception as e:
            print(f'\n[ERROR] Failed to connect: {str(e)}')
        finally:
            self.disconnect()
    
    def disconnect(self):
        self.running = False
        
        if self.is_connected:
            print('\n[INFO] Disconnecting from server...')
            self.is_connected = False
        
        if self.sock:
            try:
                self.sock.close()
            except:
                pass 
        
        print('[INFO] Disconnected. Goodbye!')


def handle_ctrl_c(sig, frame):
    print('\n[SIGNAL] Received interrupt signal')
    if 'client' in globals():
        client.running = False
        client.disconnect()
    sys.exit(0)
    
    
if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_ctrl_c)
    
    client = ChatClient('127.0.0.1', 5555)
    client.connect()
