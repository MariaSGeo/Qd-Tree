import unittest

import sqlparse


class MyTestCase(unittest.TestCase):

    def test_simple_query(self):
        # Split a string containing two SQL statements:
        raw = 'select * from foo; select * from bar;'
        statements = sqlparse.split(raw)

        # Format the first statement and print it out:
        first = statements[0]
        print(sqlparse.format(first, reindent=True, keyword_case='upper'))

        # Parsing a SQL statement:
        parsed = sqlparse.parse('select foo.id from foo where ha LIKE 1')[0]
        self.assertEqual({}, {})

