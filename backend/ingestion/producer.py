import asyncio  # asyncio = Python's built-in async library
import json     # json = convert Python dict ↔ JSON string
import time     # time = for measuring seconds
from aiokafka import AIOKafkaProducer      # async kafka producer
from aiokafka.errors import KafkaConnectionError  # error when kafka is down
from config.settings import settings       # our settings

# ─── The Kafka Producer ───────────────────────────────────────
# producer = the thing that SENDS messages to Kafka
# starts as None, created when first needed
producer = None

# ─── In-Memory Buffer ─────────────────────────────────────────
# asyncio.Queue = a line/queue in memory (like a queue at a shop)
# maxsize=50000 = maximum 50,000 signals can wait in line
# If kafka is slow, signals wait here instead of crashing
signal_buffer = asyncio.Queue(maxsize=50000)

# ─── Throughput Tracking ──────────────────────────────────────
_signal_count = 0           # how many signals received since last report
_last_report_time = time.time()  # when we last printed the throughput

async def get_producer():
    global producer  # use the global producer variable

    if producer is None:  # only create once
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            # bootstrap_servers = where is kafka (address:port)

            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            # value_serializer = how to convert our dict to bytes
            # lambda v: = small anonymous function
            # json.dumps(v) = dict → JSON string
            # .encode("utf-8") = string → bytes (kafka needs bytes)

            compression_type="gzip",
            # compress messages to save bandwidth

            linger_ms=5,
            # wait 5ms to collect multiple signals into one batch
            # instead of sending one by one (much faster)

            max_batch_size=65536,
            # maximum batch size in bytes = 64KB
        )
        await producer.start()  # connect to kafka
    return producer

async def stop_producer():
    global producer
    if producer:
        await producer.stop()  # disconnect from kafka cleanly
        producer = None

async def buffer_signal(signal_data: dict):
    # signal_data = the signal as a Python dictionary
    # This function is called for EVERY incoming signal
    # It must return INSTANTLY — never wait, never block
    global _signal_count

    try:
        # put_nowait = add to queue WITHOUT waiting
        # if queue is full it raises exception (caught below)
        signal_buffer.put_nowait(signal_data)
        _signal_count += 1  # count this signal

    except asyncio.QueueFull:
        # Queue is full (50,000 signals waiting already)
        # Strategy: drop the OLDEST signal to make room for new one
        try:
            signal_buffer.get_nowait()    # remove oldest signal
            signal_buffer.put_nowait(signal_data)  # add new signal
        except Exception:
            pass  # if even this fails, just ignore this signal

async def flush_buffer_to_kafka():
    # This runs FOREVER in the background
    # Its job: take signals from buffer → send to kafka
    global _signal_count, _last_report_time

    p = await get_producer()  # get kafka producer

    while True:  # infinite loop — runs forever
        try:
            # ── Step 1: collect up to 500 signals from buffer ──
            batch = []  # empty list to collect signals
            for _ in range(500):
                # _ = throwaway variable (we don't use loop counter)
                try:
                    item = signal_buffer.get_nowait()  # take one signal
                    batch.append(item)  # add to batch
                except asyncio.QueueEmpty:
                    break  # no more signals in buffer, stop collecting

            # ── Step 2: send each signal to kafka ──
            for signal in batch:
                await p.send(settings.kafka_topic, value=signal)
                # kafka_topic = "ims-signals" (the channel name)

            # ── Step 3: print throughput every 5 seconds ──
            now = time.time()  # current time in seconds
            elapsed = now - _last_report_time  # seconds since last report

            if elapsed >= 5:  # if 5 seconds have passed
                rate = _signal_count / elapsed  # signals per second
                print(f"[THROUGHPUT] {rate:.1f} signals/sec | Buffer size: {signal_buffer.qsize()}")
                # .1f = show 1 decimal place
                # .qsize() = how many signals currently in buffer
                _signal_count = 0           # reset counter
                _last_report_time = now     # reset timer

        except KafkaConnectionError as e:
            # kafka is down — wait 2 seconds and retry
            print(f"[KAFKA ERROR] {e} - retrying in 2s")
            await asyncio.sleep(2)  # wait 2 seconds (async = doesn't block)

        except Exception as e:
            print(f"[FLUSH ERROR] {e}")  # log any other error

        await asyncio.sleep(0.01)  # wait 10ms before next batch
        # 0.01 seconds = 10 milliseconds
        # this prevents the loop from running 1000x per second uselessly