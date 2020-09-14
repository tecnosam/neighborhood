from waitress import serve
import server

serve( server.sock, host = '0.0.0.0' )