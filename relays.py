import time
import smbus
import sys

DEVICE_BUS = 1
DEVICE_ADDR = 0x10
bus = smbus.SMBus(DEVICE_BUS)

def relay_on(num):
    bus.write_byte_data(DEVICE_ADDR, num, 0x00)

def relay_off(num):
    bus.write_byte_data(DEVICE_ADDR, num, 0xFF)

def test():
    while True:
        try:
            for i in range(1,5):
                relay_on(i)
                time.sleep(1)
                relay_off(i)
                time.sleep(1) 
        except KeyboardInterrupt as e:
            sys.exit()


if __name__ == '__main__':
    test()
