
from wsgiref.simple_server import make_server

from bamboo.nas.simple_nas import CommonNasEndpoint, SimpleNasApp


if __name__ == "__main__":
    DOC_ROOT = "./res"
    app = SimpleNasApp(DOC_ROOT, CommonNasEndpoint)
    server = make_server("", 8000, app)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print()
