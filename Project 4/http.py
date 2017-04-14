import re
from rawsockets import TCPLayer, TCPPacket
from urlparse import urlparse
from time import time
TIME_OUT = 60 

class Http:
    def __init__(self):
        
        self.sock = TCPLayer()
        self.chunked = False
        self.content = ''
        self.header = ''

    def AssembleHTTPHeader(self, host, path):
      
        http_header = 'GET ' + path + ' HTTP/1.1\n' + \
                      'Host: ' + host + '\r\n' + \
                      'Connection: keep-alive\r\n' + \
                      'Accept: text/html\r\n' + \
                      '\r\n'

        if len(http_header) % 2 != 0:
            http_header += ' '

        return http_header

    def send(self, data):
       
        self.sock.send(data)

    def receive(self):
        
        data_recv = self.sock.recvPackets()
        
        page = self.remove_header(data_recv)
        # Verify chunk encoding in HTTP 1.1
        if self.parse_chunked(page):
            try:
                self.content = self.remove_chunk_length(page)
            except ValueError:
                self.content = page
        else:
            self.content = page

        return self.content

    def remove_header(self, data):
        
        header_offset = data.split('\r\n\r\n', 1)
        self.header = header_offset[0]
        return header_offset[1]

    def parse_chunked(self, data):
        
        first_line = data.split('\r\n', 1)[0]
        m = re.match(r'^[a-zA-Z0-9]+$', first_line)

        if m is not None:
            return True
        if m is None:
            return False

    def remove_chunk_length(self, data):
        content = []
        while True:
            
            first_line = data.split('\r\n', 1)[0]
            rest_data = data.split('\r\n', 1)[1]
            m = re.match(r'^[a-zA-Z0-9]+$', first_line)
            
            if m is not None:
                chunk_size = int(m.group(0), 16)
                content.append(rest_data[:chunk_size])
                data = rest_data[chunk_size + 2:]
                
                if chunk_size == 0:
                    break
            
            elif m is None:
                raise ValueError

        return ''.join(content)

    def save_file(self, data, url):
        new_file_name = ''

        path = urlparse(url).path
        file_name = path.split('/')[-1]
        if file_name == '':
            new_file_name = "index.html"
        else:
            new_file_name = file_name

        f = open(new_file_name, 'wb')
        f.write(data)
        f.close()

    def get_data(self, url, flag):
        if 'http://' == url[:7]:
            pass
        else:
            url += 'http://'
            
        # Parse URL into sections 
        url_obj = urlparse(url)

	#scheme://netloc/path;paramters
        host = url_obj.netloc
        path = url_obj.path
        if path == '':
            path = '/'
        else:
            pass

        
        port = 80
        self.sock.connect(host, port)

        data_sent = self.AssembleHTTPHeader(host,path)
        self.send(data_sent)
        data_recv = self.receive()
        self.save_file(data_recv, url)
       
        self.sock.close()
