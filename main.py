"""
Industrial Automation Simulation
---------------------------------
Combines:
  - Modbus TCP Server  → process I/O layer
  - OPC UA Server      → data exchange / monitoring
  - PID Controller     → process control logic
  - Sensor Validator   → sanity checking of measurements

Author: Pavan Kalyan Narra
Compatible with: PyModbus >= 3.5, freeopcua >= 1.0, Python >= 3.10
"""

import asyncio
import threading
import time
import logging
from datetime import datetime

# ---------------- Core Imports ----------------
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext

from opcua import ua, Server
from src.pid_control import PIDController
from src.sensor_validate import check_sensor_range

# ---------------- Logging ----------------
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)


# ======================================================================
#  SECTION 1: MODBUS TCP SERVER (ASYNC)
# ======================================================================
async def run_modbus_server(host="127.0.0.1", port=5020):
    """Start asynchronous Modbus TCP server with 100 holding registers."""

    # Data blocks (DI, CO, HR, IR)
    blocks = {
        "di": ModbusSequentialDataBlock(0, [0] * 100),
        "co": ModbusSequentialDataBlock(0, [0] * 100),
        "hr": ModbusSequentialDataBlock(0, [25] * 100),  # Default temperature = 25°C
        "ir": ModbusSequentialDataBlock(0, [0] * 100),
    }

    # Newer PyModbus supports passing dict directly
    context = ModbusServerContext(blocks, single=True)

    # Device identification (human-readable in logs)
    class Identity:
        VendorName = "Pavan Automation"
        ProductCode = "PMOD"
        VendorUrl = "https://github.com/pavan-narra"
        ProductName = "Virtual Modbus Server"
        ModelName = "v1.0"
        MajorMinorRevision = "1.0"

    identity = Identity()

    log.info(f" Modbus TCP server started on {host}:{port}")
    await StartAsyncTcpServer(context=context, identity=identity, address=(host, port))


def _start_modbus_server_bg():
    """Run async Modbus server in background thread."""
    def _run():
        asyncio.run(run_modbus_server(host="127.0.0.1", port=5020))
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


# ======================================================================
#  SECTION 2: OPC UA SERVER
# ======================================================================
def _start_opcua_server():
    """Start OPC UA server with process tags."""
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4841/freeopcua/server/")
    uri = "http://pavan-automation.local/industrial-automation-sim"
    idx = server.register_namespace(uri)

    root = server.nodes.objects
    temp_node = root.add_variable(idx, "ProcessTemperature", 25.0)  # PV
    ctrl_node = root.add_variable(idx, "ControlOutput", 0.0)        # CV
    sp_node = root.add_variable(idx, "Setpoint", 50.0)              # SP
    valid_node = root.add_variable(idx, "SensorValid", True)
    sp_node.set_writable()

    server.start()
    log.info(f"[{datetime.now()}]  OPC UA server running at opc.tcp://localhost:4841/freeopcua/server/")
    return server, {"PV": temp_node, "CV": ctrl_node, "SP": sp_node, "VALID": valid_node}


# ======================================================================
#  SECTION 3: CONTROL LOOP (PID + COMM)
# ======================================================================
def main(start_modbus_server=True):
    log.info("=== Industrial Automation Simulation: PID + Modbus + OPC UA ===")

    # 1️⃣ Start Modbus TCP server (background)
    if start_modbus_server:
        _start_modbus_server_bg()
        time.sleep(2.0)

    # 2️⃣ Start OPC UA server
    opcua_server, tags = _start_opcua_server()

    # 3️⃣ Modbus Client connection
    client = ModbusTcpClient("127.0.0.1", port=5020)
    if not client.connect():
        log.error(" Could not connect to Modbus server.")
        opcua_server.stop()
        return
    log.info(" Connected to Modbus server 127.0.0.1:5020")

    # 4️⃣ Initialize PID Controller
    pid = PIDController(kp=1.0, ki=0.2, kd=0.05, setpoint=50.0)
    last_time = time.time()

    log.info(" Control loop active (press Ctrl+C to stop)")
    try:
        while True:
            now = time.time()
            dt = max(1e-3, now - last_time)
            last_time = now

            # --- Read SP from OPC UA
            sp_val = float(tags["SP"].get_value())
            pid.setpoint = sp_val

            # --- Read PV from Modbus (HR0)
            try:
                rr = client.read_holding_registers(address=0, count=1)
                if not rr or rr.isError():
                    raise ModbusException("Read failed")
                pv = float(rr.registers[0])
            except Exception as e:
                log.warning(f"Modbus read error: {e}")
                pv = None

            # --- Validate Sensor Input
            valid = check_sensor_range(pv, low=0, high=200) if pv is not None else False

            # --- Compute Control Output
            if valid:
                cv = pid.compute(measured_value=pv, dt=dt)
                cv_clamped = max(-1000.0, min(1000.0, cv))
                cv_scaled = int(round(cv_clamped))
            else:
                cv_scaled = 0  # Fail-safe

            # --- Write CV to Modbus (HR1)
            try:
                client.write_register(address=1, value=cv_scaled)
            except Exception as e:
                log.warning(f"Modbus write error: {e}")

            # --- Publish to OPC UA
            if pv is not None:
                tags["PV"].set_value(ua.Variant(pv, ua.VariantType.Double))
            tags["CV"].set_value(ua.Variant(float(cv_scaled), ua.VariantType.Double))
            tags["VALID"].set_value(ua.Variant(bool(valid), ua.VariantType.Boolean))

            # --- Console Heartbeat
            print(f"SP={sp_val:.1f}  PV={pv if pv is not None else 'None'}  CV={cv_scaled}  VALID={valid}")

            time.sleep(0.5)

    except KeyboardInterrupt:
        log.info(" Stopping control simulation...")

    finally:
        try:
            client.close()
        except Exception:
            pass
        try:
            opcua_server.stop()
        except Exception:
            pass
        log.info(" Clean shutdown complete.")


# ======================================================================
#  SECTION 4: ENTRY POINT
# ======================================================================
if __name__ == "__main__":
    main(start_modbus_server=True)
