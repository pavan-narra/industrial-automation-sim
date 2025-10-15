import logging
from datetime import datetime
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext

# ---------------- Logging ----------------
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)


def run_modbus_server(host="localhost", port=5020):
    # ---------------- Data Blocks ----------------
    # Create Modbus data blocks for coils, discrete inputs, etc.
    blocks = {
        "di": ModbusSequentialDataBlock(0, [0] * 100),   # Discrete Inputs
        "co": ModbusSequentialDataBlock(0, [0] * 100),   # Coils
        "hr": ModbusSequentialDataBlock(0, [25] * 100),  # Holding Registers (default 25°C)
        "ir": ModbusSequentialDataBlock(0, [0] * 100),   # Input Registers
    }

    # ---------------- Server Context ----------------
    # Newer versions accept dictionary directly (no ModbusSlaveContext)
    context = ModbusServerContext(blocks, single=True)


    # ---------------- Identity (optional placeholder) ----------------
    class Identity:
        VendorName = "Pavan Automation"
        ProductCode = "PMOD"
        VendorUrl = "https://github.com/pavankalyan"
        ProductName = "Virtual Modbus Server"
        ModelName = "v1.0"
        MajorMinorRevision = "1.0"

    identity = Identity()

    # ---------------- Start Server ----------------
    print(f"[{datetime.now()}] Starting Modbus server on {host}:{port}")
    try:
        StartTcpServer(context, identity=identity, address=(host, port))
    except KeyboardInterrupt:
        print(f"[{datetime.now()}] Modbus server stopped manually.")


if __name__ == "__main__":
    run_modbus_server()
