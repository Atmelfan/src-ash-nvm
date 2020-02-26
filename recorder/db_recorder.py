import datetime
import logging
import os
import queue
import sqlite3
import threading
import time
from logging.handlers import QueueHandler


class DbRecorder(threading.Thread):

    def __init__(self, name, tables, dir='.', max_pages=256*1024):
        super().__init__(name=name)
        self.tables = tables
        self.name = name
        self.dir = dir
        self.max_pages = max_pages

        # Create output directory
        if not os.path.exists(dir):
            os.mkdir(dir)

        # Input queue
        self.queue = queue.Queue()
        self.kill = True

        # Start thread
        self.start()

    def record(self, table, msg):
        if self.queue:
            if table in self.tables:
                self.queue.put((table, msg))
            else:
                raise KeyError

    def run(self) -> None:
        """Put messages into database"""
        conn = sqlite3.connect(
            os.path.join(self.dir, '%s_%s.db' % (self.name, datetime.datetime.now().isoformat(timespec='seconds'))))
        try:
            # Setup database tables
            conn.execute('PRAGMA max_page_count = %d;' % self.max_pages)
            for name, columns in self.tables.items():
                statement = '''CREATE TABLE %s (%s)''' % (name, ", ".join(columns))
                # print(statement)
                conn.execute(statement)

            conn.commit()

            # Start recording
            while self.kill or not self.queue.empty():
                batch = {}
                try:
                    # Add up to 50 items in batch operation
                    for x in range(50):
                        table, item = self.queue.get(block=True, timeout=2)
                        if table not in batch:
                            batch[table] = []
                        batch[table].append(item)

                except queue.Empty:
                    pass

                for table, items in batch.items():
                    columns = self.tables[table]
                    insert = "INSERT INTO %s VALUES (%s)" % (table, ','.join(len(columns) * '?'))
                    # print('Inserting %s items into %s' % (len(items), table))
                    conn.executemany(insert, items)
                conn.commit()
        except sqlite3.Error as sqle:
            logging.exception("SQL error: %s", str(sqle), exc_info=sqle)
        finally:
            # print('Closed')
            self.queue = None
            conn.close()

    def stop(self):
        """Stop recorder but allow 5s to finish and close"""
        self.kill = False
        self.join(10)


class DbRecordHandler(QueueHandler):
    def __init__(self, dbrec: DbRecorder, *kvargs, **kwargs):
        super().__init__(None)
        self.dbrec = dbrec

    def enqueue(self, record: logging.LogRecord):
        self.dbrec.record('log', (int(time.monotonic()*10e6), record.name, record.levelname, record.msg))