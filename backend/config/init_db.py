from config.database import get_pg_pool  # import our postgres connection function

# This is the SQL to create the work_items table
# SQL = language to talk to PostgreSQL
# CREATE TABLE IF NOT EXISTS = create table only if it doesn't exist yet
CREATE_WORK_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS work_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- UUID = unique ID like "a1b2-c3d4-..." auto generated
    -- PRIMARY KEY = this is the unique identifier for each row

    component_id TEXT NOT NULL,
    -- TEXT = string, NOT NULL = required field

    priority TEXT NOT NULL DEFAULT 'P2',
    -- DEFAULT 'P2' = if no priority given, use P2

    status TEXT NOT NULL DEFAULT 'OPEN',
    -- new incidents start as OPEN

    signal_count INTEGER DEFAULT 1,
    -- how many signals linked to this work item

    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- TIMESTAMPTZ = timestamp with timezone, NOW() = current time

    end_time TIMESTAMPTZ,
    -- nullable = can be empty (filled when incident closes)

    mttr_seconds INTEGER,
    -- Mean Time To Repair in seconds (calculated when closed)

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

# SQL to create the rca_records table
CREATE_RCA_TABLE = """
CREATE TABLE IF NOT EXISTS rca_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    work_item_id UUID REFERENCES work_items(id) ON DELETE CASCADE,
    -- REFERENCES = foreign key, links to work_items table
    -- ON DELETE CASCADE = if work item deleted, delete RCA too

    incident_start TIMESTAMPTZ NOT NULL,
    incident_end TIMESTAMPTZ NOT NULL,
    root_cause_category TEXT NOT NULL,
    fix_applied TEXT NOT NULL,
    prevention_steps TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

async def init_db():
    # get our postgres connection
    pool = await get_pg_pool()

    # acquire = borrow one connection from the pool
    async with pool.acquire() as conn:
        # execute = run the SQL query
        await conn.execute(CREATE_WORK_ITEMS_TABLE)
        await conn.execute(CREATE_RCA_TABLE)

    print("PostgreSQL tables initialized")
    # this message appears in terminal when server starts