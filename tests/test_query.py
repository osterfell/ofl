import unittest

from ofl.query import QueryError, parse


class ParseTests(unittest.TestCase):
    def test_terms_combine(self):
        self.assertEqual(
            parse("vram>=80 region=eu price<1.2"),
            {"vram": {"gte": 80}, "region": {"eq": "eu"}, "price": {"lt": 1.2}},
        )

    def test_a_range_on_one_field(self):
        self.assertEqual(parse("gpus>=2 gpus<=4"), {"gpus": {"gte": 2, "lte": 4}})

    def test_quoted_value(self):
        self.assertEqual(parse('gpu="rtx 4090"'), {"gpu": {"eq": "rtx 4090"}})

    def test_boolean(self):
        self.assertEqual(parse("interruptible=true"), {"interruptible": {"eq": True}})

    def test_empty_query_is_no_filters(self):
        self.assertEqual(parse(""), {})

    def test_unknown_field(self):
        with self.assertRaises(QueryError):
            parse("colour=red")

    def test_ordering_a_string_is_refused(self):
        with self.assertRaises(QueryError):
            parse("region>eu")

    def test_wrong_type(self):
        with self.assertRaises(QueryError):
            parse("vram>=lots")


if __name__ == "__main__":
    unittest.main()
