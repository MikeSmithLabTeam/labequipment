
from serial.tools.list_ports import comports


com_ports_list = list(comports())

com_port = com_ports_list[0]
print(com_port.name,
      com_port.device,
      com_port.description,
      com_port.serial_number,
      com_port.product,
      com_port.pid)


print(com_ports_list)

