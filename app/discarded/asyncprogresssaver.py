        async with AsyncConnectionPool(
            conninfo=settings.PSYCOPG3_DATABASE_URL,
            min_size=1,
            max_size=3,
            timeout=30,
            kwargs={
                "autocommit": True,
                "row_factory": dict_row,
                "prepare_threshold": None,
            },
        ) as pool:
        import psycopg

        conn = await psycopg.AsyncConnection.connect(
            conninfo=settings.PSYCOPG3_DATABASE_URL,
            prepare_threshold=None,
            autocommit=True,
            row_factory=dict_row,
        )
        async with conn.cursor() as cur:
            test = await cur.execute("SELECT * from checkpoints")
            pprint(test)
            blub = await cur.fetchone()
            pprint(blub)
        await conn.close()