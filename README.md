## Chat Application

chat app built with Python that lets multiple people connect and chat in real-time.

## What You Need
Just Python 3.6 or newer version and Everything else is already in Python's standard library (socket, threading, sys, signal).


### Starting the Server
First,start  the server:

```bash
cd server
python server.py
```

By default it runs on `127.0.0.1:5555`. If you want to use a different host or port:

```bash
python server.py [host] [port]
```

### Connecting Clients

Open another terminal (or a few) and run the client.

```bash
cd client
python3 client.py
```

It will ask for a nickname - just write  whatever you want. Then you are in and can start chatting!

### Commands You Can Use

Once you're connected, here's what you can do:
- `/quit` - leave the chat
- `/users` or `/who` - see who else is online
- `/help` - get a list of commands

---

## How the Protocol Works

### Connection Flow

Here's what happens when someone connects:

1. Client connects to the server
2. Server asks for a nickname (sends "NICK")
3. Client sends back their chosen nickname
4. Server tells everyone that a new person joined
5. New client gets the last 10 messages so they can catch up

### Message Formats

straightforward:
**Regular chat:** `{nickname}: {message}\n`
**Server announcements:** `SERVER: {announcement}\n`
**Commands:** `/{command}\n`

+---------+          +---------+          +--------------+
| Client  |          | Server  |          | Other Clients|
+---------+          +---------+          +--------------+
     |                    |                       |
     | ---- Connect ----> |                       |
     |                    |                       |
     | <----- NICK ------ |                       |
     |                    |                       |
     | ---- nickname ---> |                       |
     |                    | ---- Join Msg ----->  |
     |                    |                       |
     | <---- History ---- |                       |
     |                    |                       |
     | ---- Message --->  |                       |
     |                    | ---- Broadcast ---->  |
     |                    |                       |
     | <---- Response --- |                       |
     |                    |                       |

## Design Overview

### How the Server Works
The server has one main thread whose job is to wait for new client connections.

When a new user connects, the server creates a new thread to handle that user.
Because of this, many people can chat at the same time.

The server keeps some important data:

clients list – stores all connected users
nicknames list – stores the usernames
message_history – stores the last 10 messages so new users can see recent chat

Since multiple threads are running at the same time, locks are used to make sure data is updated safely and messages do not get mixed up.


### How the Client Works
It uses two threads:
Main thread
Reads what the user types and sends the message to the server.

Receive thread
Keeps listening for messages from the server and shows them on the screen.

Because of this setup, the user can send and receive messages at the same time.

### Threading Diagram
SERVER SIDE

Main Thread
     |
     |----> Client Thread 1
     |        (handles messages of user 1)
     |
     |----> Client Thread 2
     |        (handles messages of user 2)
     |

CLIENT SIDE

Main Thread  -----> sends messages to server
Receive Thread ----> listens for messages from server


### What It Can Do

The app includes features:
* Broadcasts messages to everyone who's connected
* Timestamps on all messages (HH:MM:SS format)
* Keeps the last 10 messages in history
* Shows you who's online with the `/users` command
* Thread-safe operations (no race conditions!)
* Handles shutdowns gracefully when you press Ctrl+C
