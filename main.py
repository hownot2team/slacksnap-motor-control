import os
import logging
logging.basicConfig(
        format='[%(asctime)s] %(levelname)s %(module)s/%(funcName)s - %(message)s',
        level=logging.DEBUG if os.environ.get('DEBUG') else logging.INFO)

logging.info('')
logging.info('BOOT UP')

import asyncio
import aiomqtt

import dyn4

dmm = None

async def process_mqtt(message):
    try:
        text = message.payload.decode()
    except UnicodeDecodeError:
        return

    topic = message.topic.value
    logging.debug('MQTT topic: %s, message: %s', topic, text)

    if topic == 'motion/set_rpm':
        rpm = int(float(text))
        dmm.set_speed(rpm)


async def monitor_mqtt():
    await asyncio.sleep(1)

    # from https://sbtinstruments.github.io/aiomqtt/reconnection.html
    # modified to make new client since their code didn't work
    # https://github.com/sbtinstruments/aiomqtt/issues/269
    while True:
        try:
            async with aiomqtt.Client('localhost') as client:
                await client.subscribe('motion/#')
                async for message in client.messages:
                    await process_mqtt(message)
        except aiomqtt.MqttError:
            logging.info('MQTT connection lost, reconnecting in 5 seconds...')
            await asyncio.sleep(5)


async def monitor_dyn4():
    while True:
        await asyncio.sleep(0.1)

        if not dmm:
            continue

        pos = dmm.read_AbsPos32()
        encoder_ppr = 65536

        revolutions = pos / 65536

        async with aiomqtt.Client('localhost') as client:
            message = str(revolutions)
            topic = 'server/position'
            await client.publish(topic, payload=message.encode())


async def init():
    global dmm

    dmm = dyn4.DMMDrive('/dev/ttyUSB0', 0)
    dmm.set_speed(0)


def task_died(future):
    if os.environ.get('SHELL'):
        logging.error('Motion control task died!')
    else:
        logging.error('Motion control task died! Waiting 60s and exiting...')
        time.sleep(60)
    exit()


def main():
    loop = asyncio.get_event_loop()

    a = loop.create_task(monitor_dyn4()).add_done_callback(task_died)
    b = loop.create_task(monitor_mqtt()).add_done_callback(task_died)
    z = loop.create_task(init())

    loop.run_forever()


if __name__ == '__main__':
    main()
