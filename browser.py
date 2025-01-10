#!/usr/bin/env python3.12.1
import socket
import ssl
import tkinter
LINE_BREAK = '\n'



    
def layout(text, HSTEP, VSTEP, WIDTH):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    
    for c in text: 
        # Add to list the character and its position
        
        display_list.append((cursor_x, cursor_y, c))
        if c == LINE_BREAK: 
           cursor_y += VSTEP
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list

class Browser:
    def __init__(self):
        self.WIDTH, self.HEIGHT = 800, 600
        self.HSTEP, self.VSTEP = 13, 18
        self.SCROLL_STEP = 100
        
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=self.WIDTH,
            height=self.HEIGHT
        )
        self.canvas.pack(fill='both', expand=1)
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.scrollMouse)
        self.window.bind("<Configure>", self.resize)
    
    def resize(self, e):
        print(f"e: {e}")
        self.WIDTH = e.width
        self.HEIGHT = e.height
        self.display_list = layout(self.og_text, self.HSTEP, self.VSTEP, e.width)
        self.draw()
        
    def scrolldown(self, e):
        self.scrolling(self.SCROLL_STEP)
        
    def scrollup(self, e):
        self.scrolling(-1*self.SCROLL_STEP)
        
    def scrollMouse(self, e):
        #windows me los da vuelta... 
        self.scrolling(e.delta * -1)
        
    def scrolling(self, delta):
        self.scroll += delta
        if self.scroll < 0: self.scroll = 0
        self.draw()
    
    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + self.HEIGHT: continue
            if y + self.VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)
    
    def load(self, url):
        self.og_url = url
        view = url.view_source
        body = url.request()
        print("showing content...")
        text = ''
        if view: 
            text = lex_view(body)
        else:        
            text = lex(body) 
        self.og_text = text
        self.display_list = layout(text, self.HSTEP, self.VSTEP, self.WIDTH)
        self.draw()

def createRequest(host, path, method="GET", httpVersion="HTTP/1.1", userAgent="ZantySurfingBoard", connection="Closed"):
        request = "{} {} {}\r\n".format(method, path, httpVersion)
        request += "Host: {}\r\n".format(host)
        request += "Connection: {}\r\n".format(connection)
        request += "User-Agent: {}\r\n".format(userAgent)
        request += "\r\n"
        return request

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
        self.view_source = False
        if not url:
            url = "file:///G:/browser-eng/python/cmds.txt"
            self.port = 80
        if "data:" in url and "://" not in url: 
            self.scheme, url = url.split(",", 1)
            assert self.scheme == "data:text/html"
            self.content = url
        else:
            if "view-source:" in url:
                view, url = url.split(":", 1)
                self.view_source = True
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
        
    def request_http(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))
        if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
        request = createRequest(self.host, self.path)
        print("Sending request... ")
        print(request)
        s.send(request.encode("utf8"))
        response = s.makefile("r", encoding="utf8", newline="\r\n")
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
        content = response.read()
        s.close()
        return content

    def request_file(self):
        p1, p2 = self.path.split('/',1)
        try:
            with open(p2, 'r') as file:
                print(f"file: {file}")
                return file.read()
        except FileNotFoundError:
            print(f"Error: File {self} not found.")

    def request(self):        
        match self.scheme:
            case "http" | "https": 
                return self.request_http()
            case "file": 
                return self.request_file()
            case "data:text/html": 
                return self.content 
            case "view-source": 
                return 
            case _:
                print(f"Error on parsing schema")
        
def lex(body):
    text = ''
    in_tag = False
    in_entity = False
    entity = ''
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif c == "&":
            entity += c
            in_entity = True
        elif in_entity and not c == ';':
            entity += c
        elif c == ";" and not entity == '':
            text += parseEntity(entity)
            entity = ''
            in_entity = False
        elif not in_tag | in_entity:
             text += c
    return text

def parseEntity(e):
    remainder, e = e.split("&", 1)
    assert remainder == ""
    match e:
        case "gt":  return '>'
        case "lt":  return '<'

def lex_view(body):
    text = ''
    for c in body:
        text += c

       
if __name__ == "__main__":
    import sys
    assert sys.version_info >= (3, 10)
    
    if len(sys.argv) == 1:
        Browser().load(URL())
    else:
        Browser().load(URL(sys.argv[1]))
    
    tkinter.mainloop()