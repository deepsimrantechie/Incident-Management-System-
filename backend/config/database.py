# asynchronously = mean talking to datababse without blocking other code from running or other connection 



# Libraries imported to talk to database

import asyncpg         # asyncpg = talk to postgresql acnchronously 
import redis.asyncio as aioredis   # talk to readis asynchronously basically redis use ram as storage to make dashboard faster 
from motor.motor_asyncio import AsyncIOMotorClient   # talk to mongodb asynchronously without it it will block other code while rnning or need to ensure the api
from config.settings import settings   # out settings.py file where we have all the database url and other settings

# ─── PostgreSQL ───────────────────────────────────────────────

pg_pool = None # varibale to hold out connection pool to postgrest databse

async def get_pg_pool():
   
    global pg_pool  # making it global varibale so we can modify inside function and impact can be seen outside to function as well

    if pg_pool is None:  # if connection pool is not created yet
        pg_pool = await asyncpg.create_pool(     # create a pool of connection to postgres database using await because this is an async functions
            settings.postgres_url,   # importing the url from settings.py file
            min_size=5,    # settings min size of connections pool 
            max_size=20   # settings max size of connections pool
        )
    return pg_pool  

# ─── MongoDB ──────────────────────────────────────────────────
mongo_client = None # varible to hold our connection to client
mongo_db = None      # varibale to hold which database we are using 

async def get_mongo_db():
    global mongo_client, mongo_db # again making it global so we can modify inside function and impact can be seen outside

    if mongo_client is None:   # checking if connection is not created yet
        mongo_client = AsyncIOMotorClient(settings.mongo_url) # create a connection to mongodb using the url from settings.py file 
        mongo_db = mongo_client[settings.mongo_db] # select which database to use from the connection we just creatd using 

    return mongo_db 

# ─── Redis ────────────────────────────────────────────────────
redis_client = None  # no connection yet

async def get_redis():
    global redis_client # again creating global varibale 

    if redis_client is None:   #checking if connection is not created yet
        redis_client = aioredis.from_url(   # create a async connection to redis using the url from settings.py file 
            settings.redis_url,             # the url from settings.py file 
            decode_responses=True  # give us normal strings, not b"bytes"
        )
    return redis_client

# ─── Cleanup ──────────────────────────────────────────────────
async def close_connections():
    global pg_pool, mongo_client, redis_client    # using the global varibale to close the connecion we initialised 

    if pg_pool:
        await pg_pool.close()       # checking and using awit to close the postgres connection 

    if mongo_client:                 # checking if connection is creatd then close mongodb connections
        mongo_client.close()       

    if redis_client:        # same chcking and closing the redis connections
        await redis_client.aclose() 
