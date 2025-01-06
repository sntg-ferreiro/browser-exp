#!/usr/bin/env python3.12.1
import socket
import ssl

def createRequest(host, path, method="GET", httpVersion="HTTP/1.1", userAgent="ZantySurfingBoard", connection="Closed"):
        request = "{} {} {}\r\n".format(method, path, httpVersion)
        request += "Host: {}\r\n".format(host)
        request += "Connection: {}\r\n".format(connection)
        request += "User-Agent: {}\r\n".format(userAgent)
        request += "\r\n"
        return request

def makeFileFromUrl(host, path, socket):
    request = createRequest(host, path)
    print("Sending request... ")
    print(request)
    socket.send(request.encode("utf8"))
    return  socket.makefile("r", encoding="utf8", newline="\r\n")

def makeFileFromUrlTLS(host, path, socket):
    ctx = ssl.create_default_context()
    socket = ctx.wrap_socket(socket, server_hostname=host)
    request = createRequest(host, path)
    print("Sending request... ")
    print(request)
    socket.send(request.encode("utf8"))
    return  socket.makefile("r", encoding="utf8", newline="\r\n")

class URL:
    def __init__(self, url=""):
        if not url:
            url = "file:///G:/browser-eng/python/cmds.txt"
            self.port = 80
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file"]
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        if not "/" in url:
            url = url + "/"
        self.host , url = url.split("/", 1)
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
        self.path = "/" + url
        

    def request(self):
        #response = []
        
        match self.scheme:
            case "http": 
                s = socket.socket(
                    family=socket.AF_INET,
                    type=socket.SOCK_STREAM,
                    proto=socket.IPPROTO_TCP,
                )
                s.connect((self.host, self.port))
                response = makeFileFromUrl(self.host, self.path, s)
            case "https": 
                s = socket.socket(
                    family=socket.AF_INET,
                    type=socket.SOCK_STREAM,
                    proto=socket.IPPROTO_TCP,
                )
                s.connect((self.host, self.port))
                response = makeFileFromUrlTLS(self.host, self.path, s)
            case "file": 
                p1, p2 = self.path.split('/',1)
                print(f"self.host: {p2}")
                try:
                    with open(p2, 'r') as file:
                        print(f"file: {file}")
                        return file.read()
                except FileNotFoundError:
                    print(f"Error: File {self} not found.")
            case "data": return 
            case "view-source": return 
            
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        print("Reciving response... ")
        print(f"version {version}, status {status}, explanation {explanation}")
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        #print(f"Headers: {response_headers}")
        content = response.read()
        s.close()
        return content
        
def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

def load(url):
    body = url.request()
    print("showing content...")
    show(body)        

if __name__ == "__main__":
    import sys
    assert sys.version_info >= (3, 10)
    
    if len(sys.argv) == 1:
        load(URL())
    else:
        load(URL(sys.argv[1]))