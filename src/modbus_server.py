from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer
from datetime import datetime

def run_modbus_server(host="localhost", port=5020):
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0]*100),
        co=ModbusSequentialDataBlock(0, [0]*100),
        hr=ModbusSequentialDataBlock(0, [25]*100),  # sample temperature = 25°C
        ir=ModbusSequentialDataBlock(0, [0]*100)
    )
    context = ModbusServerContext(slaves=store, single=True)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "Pavan Automation"
    identity.ProductCode = "PMOD"
    identity.VendorUrl = "https://github.com/pavankalyan"
    identity.ProductName = "Virtual Modbus Server"
    identity.ModelName = "v1.0"
    identity.MajorMinorRevision = "1.0"

    print(f"[{datetime.now()}] Starting Modbus server on {host}:{port}")
    StartTcpServer(context, identity=identity, address=(host, port))

if __name__ == "__main__":
    run_modbus_server()
