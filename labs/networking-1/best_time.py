import socket

def main():
    host = ''
    port = 2023

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(1)

    print(f"Listening on port {port}...")

    while True:
        conn, addr = s.accept()
        print(f"Connection from {addr} has been established!")
        data = conn.recv(1024).decode('utf-8')
        if not data:
            break
        print(f"Received data: {data}")
        if "GET" in data:
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nThis is the BEST time."
        else:
            response = "HTTP/1.1 405 Method Not Allowed\r\nContent-Type: text/html\r\n\r\nMethod Not Allowed."
        conn.sendall(response.encode('utf-8'))
        conn.close()

if __name__ == '__main__':
    main()