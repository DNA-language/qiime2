# ----------------------------------------------------------------------------
# Copyright (c) 2016-2018, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import unittest
import tempfile
import pathlib
import collections
import datetime
import dateutil.relativedelta as relativedelta

import qiime2.core.util as util


class TestDurationTime(unittest.TestCase):

    def test_time_travel(self):
        start = datetime.datetime(1987, 10, 27, 1, 21, 2, 50)
        end = datetime.datetime(1985, 10, 26, 1, 21, 0, 0)
        reldelta = relativedelta.relativedelta(end, start)

        self.assertEqual(
            util.duration_time(reldelta),
            '-2 years, -1 days, -3 seconds, and 999950 microseconds')

    def test_no_duration(self):
        time = datetime.datetime(1985, 10, 26, 1, 21, 0)
        reldelta = relativedelta.relativedelta(time, time)

        self.assertEqual(util.duration_time(reldelta),
                         '0 microseconds')

    def test_singular(self):
        start = datetime.datetime(1985, 10, 26, 1, 21, 0, 0)
        end = datetime.datetime(1986, 11, 27, 2, 22, 1, 1)
        reldelta = relativedelta.relativedelta(end, start)

        self.assertEqual(
            util.duration_time(reldelta),
            '1 year, 1 month, 1 day, 1 hour, 1 minute, 1 second,'
            ' and 1 microsecond')

    def test_plural(self):
        start = datetime.datetime(1985, 10, 26, 1, 21, 0, 0)
        end = datetime.datetime(1987, 12, 28, 3, 23, 2, 2)
        reldelta = relativedelta.relativedelta(end, start)

        self.assertEqual(
            util.duration_time(reldelta),
            '2 years, 2 months, 2 days, 2 hours, 2 minutes, 2 seconds,'
            ' and 2 microseconds')

    def test_missing(self):
        start = datetime.datetime(1985, 10, 26, 1, 21, 0, 0)
        end = datetime.datetime(1987, 10, 27, 1, 21, 2, 50)
        reldelta = relativedelta.relativedelta(end, start)

        self.assertEqual(
            util.duration_time(reldelta),
            '2 years, 1 day, 2 seconds, and 50 microseconds')

    def test_unusually_round_number(self):
        start = datetime.datetime(1985, 10, 26, 1, 21, 0, 0)
        end = datetime.datetime(1985, 10, 27, 1, 21, 0, 0)
        reldelta = relativedelta.relativedelta(end, start)

        self.assertEqual(
            util.duration_time(reldelta), '1 day')

    def test_microseconds(self):
        start = datetime.datetime(1985, 10, 26, 1, 21, 0, 0)
        end = datetime.datetime(1985, 10, 26, 1, 21, 0, 1955)
        reldelta = relativedelta.relativedelta(end, start)

        self.assertEqual(
            util.duration_time(reldelta), '1955 microseconds')


class TestMD5Sum(unittest.TestCase):
    # All expected results where generated via GNU coreutils md5sum
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory(prefix='qiime2-test-temp-')
        self.test_path = pathlib.Path(self.test_dir.name)

    def make_file(self, bytes_):
        path = self.test_path / 'file'
        with path.open(mode='wb') as fh:
            fh.write(bytes_)

        return path

    def test_empty_file(self):
        self.assertEqual(util.md5sum(self.make_file(b'')),
                         'd41d8cd98f00b204e9800998ecf8427e')

    def test_single_byte_file(self):
        self.assertEqual(util.md5sum(self.make_file(b'a')),
                         '0cc175b9c0f1b6a831c399e269772661')

    def test_large_file(self):
        path = self.make_file(b'verybigfile' * (1024 * 50))
        self.assertEqual(util.md5sum(path),
                         '27d64211ee283283ad866c18afa26611')

    def test_can_use_string(self):
        string_path = str(self.make_file(b'Normal text\nand things\n'))
        self.assertEqual(util.md5sum(string_path),
                         '93b048d0202e4b06b658f3aef1e764d3')


class TestMD5SumDirectory(unittest.TestCase):
    # All expected results where generated via GNU coreutils md5sum
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory(prefix='qiime2-test-temp-')
        self.test_path = pathlib.Path(self.test_dir.name)

    def make_file(self, bytes_, relpath):
        path = self.test_path / relpath
        with path.open(mode='wb') as fh:
            fh.write(bytes_)

        return path

    def test_empty_directory(self):
        self.assertEqual(util.md5sum_directory(self.test_path),
                         collections.OrderedDict())

    def test_nested_empty_directories(self):
        (self.test_path / 'foo').mkdir()
        (self.test_path / 'foo' / 'bar').mkdir()
        (self.test_path / 'baz').mkdir()

        self.assertEqual(util.md5sum_directory(self.test_path),
                         collections.OrderedDict())

    def test_single_file(self):
        self.make_file(b'Normal text\nand things\n', 'foobarbaz.txt')

        self.assertEqual(
            util.md5sum_directory(self.test_path),
            collections.OrderedDict([
                ('foobarbaz.txt', '93b048d0202e4b06b658f3aef1e764d3')
            ]))

    def test_single_file_nested(self):
        nested_dir = self.test_path / 'bar'
        nested_dir.mkdir()

        filepath = (nested_dir / 'foo.baz').relative_to(self.test_path)
        self.make_file(b'anything at all', filepath)

        self.assertEqual(
            util.md5sum_directory(self.test_path),
            collections.OrderedDict([
                ('bar/foo.baz', 'dcc0975b66728be0315abae5968379cb')
            ]))

    def test_sorted_decent(self):
        nested_dir = self.test_path / 'beta'
        nested_dir.mkdir()
        filepath = (nested_dir / '10').relative_to(self.test_path)
        self.make_file(b'10', filepath)
        filepath = (nested_dir / '1').relative_to(self.test_path)
        self.make_file(b'1', filepath)
        filepath = (nested_dir / '2').relative_to(self.test_path)
        self.make_file(b'2', filepath)

        nested_dir = self.test_path / 'alpha'
        nested_dir.mkdir()
        filepath = (nested_dir / 'foo').relative_to(self.test_path)
        self.make_file(b'foo', filepath)
        filepath = (nested_dir / 'bar').relative_to(self.test_path)
        self.make_file(b'bar', filepath)

        self.make_file(b'z', 'z')

        self.assertEqual(
            list(util.md5sum_directory(self.test_path).items()),
            [
                ('z', 'fbade9e36a3f36d3d676c1b808451dd7'),
                ('alpha/bar', '37b51d194a7513e45b56f6524f2d51f2'),
                ('alpha/foo', 'acbd18db4cc2f85cedef654fccc4a4d8'),
                ('beta/1', 'c4ca4238a0b923820dcc509a6f75849b'),
                ('beta/10', 'd3d9446802a44259755d38e6d163e820'),
                ('beta/2', 'c81e728d9d4c2f636f067f89cc14862c'),
            ])

    def test_can_use_string(self):
        nested_dir = self.test_path / 'bar'
        nested_dir.mkdir()

        filepath = (nested_dir / 'foo.baz').relative_to(self.test_path)
        self.make_file(b'anything at all', filepath)

        self.assertEqual(
            util.md5sum_directory(str(self.test_path)),
            collections.OrderedDict([
                ('bar/foo.baz', 'dcc0975b66728be0315abae5968379cb')
            ]))


if __name__ == '__main__':
    unittest.main()
