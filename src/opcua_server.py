from opcua import Server
from datetime import datetime

def start_opcua_server(endpoint="opc.tcp://localhost:4841/freeopcua/server/"):
    server = Server()
    server.set_endpoint(endpoint)
    uri = "http://pavan-automation.local"
    idx = server.register_namespace(uri)
    nodes = server.nodes.objects

    temp_node = nodes.add_variable(idx, "Temperature", 25.0)
    temp_node.set_writable()
    server.start()
    print(f"[{datetime.now()}] OPC UA Server running at {endpoint}")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopping OPC UA server...")
        server.stop()

if __name__ == "__main__":
    start_opcua_server()
