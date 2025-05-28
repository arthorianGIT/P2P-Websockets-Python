import asyncio
import websockets
from aiofile import AIOFile
import os
from keyboard import send

async def entry_point():
    exit_status = False
    global status
    status = True
    while not exit_status:
        command = await asyncio.to_thread(input, 'Command or /help for commands or /exit to disconnect >> ')
        
        if command.startswith('/help'):
            print('CONNECT <ip> <port> - request to connect to other client\nLISTCLIENTS - list of active clients to connect\nCHANGESTATUS <normalorprivate> - your server availability status')
        elif command.startswith('/exit'):
            print('Disconnecting...')
            async with AIOFile('E:/python projects/my_projects/nodes_file_transfers/servers_config.txt', 'r') as file:
                current_data = await file.read(os.path.getsize('servers_config.txt'))
                data_lines = current_data.splitlines()
            open('E:/python projects/my_projects/nodes_file_transfers/servers_config.txt', 'w').close()
            async with AIOFile('E:/python projects/my_projects/nodes_file_transfers/servers_config.txt', 'a') as file:
                for line in data_lines:
                    if str(port) in line:
                        continue
                    await file.write(f'{line}\n')
            send('ctrl+c')
            exit_status = True
        else:
            if command.startswith('CONNECT'):
                splitted_command = command.split()
                async with websockets.connect(f'ws://{splitted_command[1]}:{splitted_command[2]}') as server:
                    server_status = await server.recv()
                    if server_status == 'PRIVATE':
                        print('Sorry, this client is now private!')
                    else:
                        while True:
                            prompt = input('Prompt or /help for prompts or /disconnect to disconnect >> ')

                            if prompt.startswith('/help'):
                                print('LISTFILES - show all files in client directory\nGET <filename> - prompt client for exactly file\nSEND <filenameorpath> - prompt for sending a file to client')
                            elif prompt.startswith('/disconnect'):
                                print('Disconnecting from client...')
                                break
                            else:
                                if prompt.startswith('LISTFILES'):
                                    await server.send('LISTFILES')
                                    client_data = await server.recv()
                                    print(client_data)
                                elif prompt.startswith('GET'):
                                    await server.send(f'{prompt}|{ip}|{port}')
                                    server_response = await server.recv()
                                    if server_response == 'ok':
                                        print('Client accepted your request!')
                                        async with AIOFile(f'new_{prompt.split()[1]}', 'wb') as file:
                                            file_data = await server.recv()
                                            await file.write(file_data)
                                            print('File successfully was written, check out!')
                                    elif server_response == 'reject':
                                        print('Client rejected your request!')
                                elif prompt.startswith('SEND'):
                                    splitted_prompt = prompt.split()
                                    await server.send('SEND')
                                    server_response = await server.recv()
                                    if server_response == 'ok':
                                        await server.send(splitted_prompt[1])
                                        async with AIOFile(splitted_prompt[1], 'rb') as file:
                                            file_data = await file.read(os.path.getsize(splitted_prompt[1]))
                                            await server.send(file_data)
                                            print('File successfully sent to other client!')
            elif command.startswith('LISTCLIENTS'):
                async with AIOFile('E:/python projects/my_projects/nodes_file_transfers/servers_config.txt', 'r') as file:
                    data = await file.read(os.path.getsize('servers_config.txt'))
                    print(data)
            elif command.startswith('CHANGESTATUS'):
                splitted_command = command.split()
                status = False if splitted_command[1] == 'private' else True
                print(f'Your status now is {'normal' if status else 'private'}, enjoy :)')

async def client(websocket):
    global status
    if not status:
        await websocket.send('PRIVATE')
    else:
        await websocket.send('NORMAL') 
        async for message in websocket:
            if message == 'LISTFILES':
                await websocket.send(os.listdir('E:/python projects/my_projects/nodes_file_transfers/'))
            elif message.startswith('GET'):
                splitted_request = message.split('|')
                print('\nYou have 1 unreaded message, please click enter to see')
                response = input(f'Ip {splitted_request[1]} port {splitted_request[2]} requesting for GET, ok or reject >> ')
                await websocket.send(response)
                if response == 'ok':
                    filename = ''.join(splitted_request[0]).split()[1]
                    async with AIOFile(f'E:/python projects/my_projects/nodes_file_transfers/{filename}', 'rb') as file:
                        file_data = await file.read(os.path.getsize(filename))
                        await websocket.send(file_data)
            elif message.startswith('SEND'):
                print('\nYou have 1 unreaded message, please click enter to see')
                response = input(f'Ip {splitted_request[1]} port {splitted_request[2]} requesting for SEND, ok or reject >> ')
                await websocket.send(response)
                if response == 'ok':
                    filename = await websocket.recv()
                    async with AIOFile(filename, 'wb') as file:
                        file_data = await websocket.recv()
                        await file.write(file_data)
async def main():
    async with websockets.serve(client, '127.0.0.1', 0, ping_interval=10, ping_timeout=120) as server:
        global port
        global ip
        ip, port = server.sockets[0].getsockname()
        async with AIOFile('servers_config.txt', 'a+') as file:
            await file.write(f'{ip}:{port}\n')
        await asyncio.gather(server.serve_forever(), entry_point())

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass