import asyncio
import json
from aiokafka import AIOKafkaConsumer  # async kafka consumer (reads from kafka)
from datetime import datetime, timezone
from config.settings import settings
from config.database import get_pg_pool, get_mongo_db, get_redis
from workflow.alerting import get_alert_strategy  # our strategy pattern
from models.signal import ComponentType

async def get_consumer():
    # Create the kafka consumer — the thing that READS from kafka
    consumer = AIOKafkaConsumer(
        settings.kafka_topic,
        # which topic/channel to read from = "ims-signals"

        bootstrap_servers=settings.kafka_bootstrap_servers,
        # where is kafka

        group_id="ims-consumer-group",
        # group_id = name of this consumer group
        # kafka remembers which messages this group already read
        # so if we restart, we continue from where we left off

        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        # opposite of serializer in producer
        # bytes → string → Python dict

        auto_offset_reset="earliest",
        # if starting fresh, read from very beginning of topic

        enable_auto_commit=True,
        # auto tell kafka "I have read this message" after processing
    )
    await consumer.start()  # connect to kafka
    return consumer

async def store_raw_signal(signal: dict):
    # Store EVERY signal in MongoDB as audit log
    # MongoDB = good for storing many documents quickly
    db = await get_mongo_db()  # get mongodb connection

    # add a timestamp for when we stored it
    signal["stored_at"] = datetime.now(timezone.utc).isoformat()
    # .isoformat() = converts datetime to string like "2024-01-01T12:00:00"

    # insert_one = save one document to MongoDB
    # raw_signals = collection name (like a table in SQL)
    await db.raw_signals.insert_one(signal)

async def get_or_create_work_item(signal: dict) -> str:
    # This is the DEBOUNCING logic — the most important function
    # Debouncing = if 100 signals for same component in 10 seconds
    #              → create only 1 work item
    # Returns the work_item_id (string)

    redis = await get_redis()    # get redis connection
    pool  = await get_pg_pool()  # get postgres connection

    component_id   = signal["component_id"]    # example: "RDBMS_PRIMARY_01"
    component_type = signal.get("component_type", "API")
    # .get(key, default) = get value, use "API" if key not found

    # ── Step 1: Check Redis for existing work item ──
    debounce_key = f"debounce:{component_id}"
    # key example: "debounce:RDBMS_PRIMARY_01"
    # Redis is like a dictionary: key → value

    existing_id = await redis.get(debounce_key)
    # redis.get = look up this key in Redis
    # returns the work_item_id if found, None if not found

    if existing_id:
        # work item already exists for this component
        # just increment the signal count in postgres
        async with pool.acquire() as conn:
            # async with = safely borrow a connection from pool
            await conn.execute(
                # SQL UPDATE = modify existing row
                "UPDATE work_items SET signal_count = signal_count + 1, updated_at = NOW() WHERE id = $1",
                existing_id
                # $1 = placeholder for existing_id (prevents SQL injection)
            )
        return existing_id  # return existing work item id

    # ── Step 2: No existing work item — create a new one ──

    # pick the right alert strategy for this component type
    strategy   = get_alert_strategy(ComponentType(component_type))
    priority   = strategy.get_priority()
    alert_msg  = strategy.get_alert_message(component_id, signal.get("message", ""))
    print(f"[ALERT] {alert_msg}")  # print alert to terminal

    async with pool.acquire() as conn:
        # INSERT INTO = add new row to postgres table
        # RETURNING id = after inserting, give us back the new id
        row = await conn.fetchrow(
            """
            INSERT INTO work_items (component_id, priority, status, signal_count, start_time)
            VALUES ($1, $2, 'OPEN', 1, NOW())
            RETURNING id::text
            """,
            # $1 = component_id, $2 = priority.value
            component_id,
            priority.value  # .value = get the string "P0" from Priority.P0
        )
        work_item_id = row["id"]  # get the id from the returned row

    # ── Step 3: Save in Redis with 10 second expiry ──
    await redis.setex(
        debounce_key,                          # key to save
        settings.debounce_window_seconds,      # expire after 10 seconds
        work_item_id                           # value to save
    )
    # After 10 seconds Redis automatically deletes this key
    # So the next signal after 10s will create a NEW work item

    # ── Step 4: Cache work item in Redis for dashboard ──
    await redis.hset(
        f"work_item:{work_item_id}",
        # hset = hash set (like a nested dictionary in Redis)
        mapping={  # mapping = dictionary of fields to save
            "component_id": component_id,
            "priority":     priority.value,
            "status":       "OPEN",
            "signal_count": "1",
        }
    )

    print(f"[WORK ITEM CREATED] {work_item_id} for {component_id} | Priority: {priority.value}")
    return work_item_id

async def link_signal_to_work_item(signal: dict, work_item_id: str):
    # After creating/finding work item, link the raw signal to it
    # This lets us show "which signals caused this incident" in the UI
    db = await get_mongo_db()

    # update_one = find one document and update it
    await db.raw_signals.update_one(
        # filter = find the document with these fields
        {"component_id": signal["component_id"], "timestamp": signal.get("timestamp")},
        # update = set this field on the found document
        {"$set": {"work_item_id": work_item_id}}
        # $set = MongoDB operator meaning "set this field"
    )

async def run_consumer():
    # Main loop — reads signals from Kafka forever
    consumer = await get_consumer()
    print("[CONSUMER] Started listening to Kafka topic:", settings.kafka_topic)

    try:
        # async for = loop that waits for next kafka message
        async for msg in consumer:
            signal = msg.value
            # msg.value = the signal dict (already deserialized from bytes)

            try:
                # Step 1: save raw signal to MongoDB
                await store_raw_signal(signal)

                # Step 2: get or create work item (debouncing happens here)
                work_item_id = await get_or_create_work_item(signal)

                # Step 3: link signal to its work item in MongoDB
                await link_signal_to_work_item(signal, work_item_id)

            except Exception as e:
                # if one signal fails, log it and continue
                # we don't want one bad signal to crash everything
                print(f"[CONSUMER ERROR] Failed to process signal: {e}")

    finally:
        # finally = runs even if an error happens
        await consumer.stop()  # always disconnect cleanly