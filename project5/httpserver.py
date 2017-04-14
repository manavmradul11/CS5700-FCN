from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import errno
import sys
import urllib2
import getopt
import os


class NewHTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, cache, origin, *args):
        self.cache = cache
        self.origin = origin
        BaseHTTPRequestHandler.__init__(self, *args)


    def download(self, path, response):
        """Download the file from the origin server.
        Args:
            path:
            response:
        """
        filename = os.pardir + path
        d = os.path.dirname(filename)
        is_downloaded = False
        if not os.path.exists(d):
            os.makedirs(d)
        f = open(filename, 'w')
        while not is_downloaded:
            try:
                f.write(response.read())  # Download succeed
                is_downloaded = True
                self.cache.append(path)
            except IOError as e:
                if e.errno == errno.EDQUOT:  # Disk has no space
                    print '[DEBUG]DISK IS NOW FULL'
                    # Update cache
                    # Remove stack bottom element
                    remove_file_path = self.cache.pop(0)
                    # Delete this file
                    os.remove(os.pardir + remove_file_path)
                    print '[DEBUG]Delete - %s' % remove_file_path
                else:
                    raise e
        f.close()

    def do_GET(self):
        if self.path not in self.cache:
            # No such file found on the replica server, fetch the file from origin server
            try:
                request = 'http://' + self.origin + ':8080' + self.path
                res = urllib2.urlopen(request)
            except urllib2.HTTPError as he:
                self.send_error(he.code, he.reason)
                return
            except urllib2.URLError as ue:
                self.send_error(ue.reason)
                return
            else:
                print '[DEBUG]Error - Try downloading  %s' % self.path
                self.download(self.path, res)
        # File is in server
        with open(os.pardir + self.path) as page:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(page.read())
        # Update cache
        self.cache.remove(self.path)
        self.cache.append(self.path)



def server(origin,port):
    cache = []

    def handler(*args):
        NewHTTPHandler(cache, origin, *args)

    httpd = HTTPServer(('', port), handler)
    httpd.serve_forever()


def parse(argvs):
    (port, origin) = (0, '')
    opts, args = getopt.getopt(argvs[1:], 'p:o:')
    for o, a in opts:
        if o == '-p':
            port = int(a)
        elif o == '-o':
            origin = a
        else:
            sys.exit('Usage in: %s -p <port> -o <origin>' % argvs[0])
    return port, origin


if __name__ == '__main__':
    port_number, origin_server = parse(sys.argv)
    server(origin_server,port_number)
