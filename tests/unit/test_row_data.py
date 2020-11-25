# Copyright 2016 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest
import mock

from google.api_core.exceptions import DeadlineExceeded
from google.cloud.bigtable.row_set import RowRange
from google.cloud.bigtable_v2.proto import data_pb2 as data_v2_pb2


class TestCell(unittest.TestCase):
    timestamp_micros = 18738724000  # Make sure millis granularity

    @staticmethod
    def _get_target_class():
        from google.cloud.bigtable.row_data import Cell

        return Cell

    def _make_one(self, *args, **kwargs):
        return self._get_target_class()(*args, **kwargs)

    def _from_pb_test_helper(self, labels=None):
        import datetime
        from google.cloud._helpers import _EPOCH
        from google.cloud.bigtable_v2.proto import data_pb2 as data_v2_pb2

        timestamp_micros = TestCell.timestamp_micros
        timestamp = _EPOCH + datetime.timedelta(microseconds=timestamp_micros)
        value = b"value-bytes"

        if labels is None:
            cell_pb = data_v2_pb2.Cell(value=value, timestamp_micros=timestamp_micros)
            cell_expected = self._make_one(value, timestamp_micros)
        else:
            cell_pb = data_v2_pb2.Cell(
                value=value, timestamp_micros=timestamp_micros, labels=labels
            )
            cell_expected = self._make_one(value, timestamp_micros, labels=labels)

        klass = self._get_target_class()
        result = klass.from_pb(cell_pb)
        self.assertEqual(result, cell_expected)
        self.assertEqual(result.timestamp, timestamp)

    def test_from_pb(self):
        self._from_pb_test_helper()

    def test_from_pb_with_labels(self):
        labels = [u"label1", u"label2"]
        self._from_pb_test_helper(labels)

    def test_constructor(self):
        value = object()
        cell = self._make_one(value, TestCell.timestamp_micros)
        self.assertEqual(cell.value, value)

    def test___eq__(self):
        value = object()
        cell1 = self._make_one(value, TestCell.timestamp_micros)
        cell2 = self._make_one(value, TestCell.timestamp_micros)
        self.assertEqual(cell1, cell2)

    def test___eq__type_differ(self):
        cell1 = self._make_one(None, None)
        cell2 = object()
        self.assertNotEqual(cell1, cell2)

    def test___ne__same_value(self):
        value = object()
        cell1 = self._make_one(value, TestCell.timestamp_micros)
        cell2 = self._make_one(value, TestCell.timestamp_micros)
        comparison_val = cell1 != cell2
        self.assertFalse(comparison_val)

    def test___ne__(self):
        value1 = "value1"
        value2 = "value2"
        cell1 = self._make_one(value1, TestCell.timestamp_micros)
        cell2 = self._make_one(value2, TestCell.timestamp_micros)
        self.assertNotEqual(cell1, cell2)


class TestPartialRowData(unittest.TestCase):
    @staticmethod
    def _get_target_class():
        from google.cloud.bigtable.row_data import PartialRowData

        return PartialRowData

    def _make_one(self, *args, **kwargs):
        return self._get_target_class()(*args, **kwargs)

    def test_constructor(self):
        row_key = object()
        partial_row_data = self._make_one(row_key)
        self.assertIs(partial_row_data._row_key, row_key)
        self.assertEqual(partial_row_data._cells, {})

    def test___eq__(self):
        row_key = object()
        partial_row_data1 = self._make_one(row_key)
        partial_row_data2 = self._make_one(row_key)
        self.assertEqual(partial_row_data1, partial_row_data2)

    def test___eq__type_differ(self):
        partial_row_data1 = self._make_one(None)
        partial_row_data2 = object()
        self.assertNotEqual(partial_row_data1, partial_row_data2)

    def test___ne__same_value(self):
        row_key = object()
        partial_row_data1 = self._make_one(row_key)
        partial_row_data2 = self._make_one(row_key)
        comparison_val = partial_row_data1 != partial_row_data2
        self.assertFalse(comparison_val)

    def test___ne__(self):
        row_key1 = object()
        partial_row_data1 = self._make_one(row_key1)
        row_key2 = object()
        partial_row_data2 = self._make_one(row_key2)
        self.assertNotEqual(partial_row_data1, partial_row_data2)

    def test___ne__cells(self):
        row_key = object()
        partial_row_data1 = self._make_one(row_key)
        partial_row_data1._cells = object()
        partial_row_data2 = self._make_one(row_key)
        self.assertNotEqual(partial_row_data1, partial_row_data2)

    def test_to_dict(self):
        cell1 = object()
        cell2 = object()
        cell3 = object()

        family_name1 = u"name1"
        family_name2 = u"name2"
        qual1 = b"col1"
        qual2 = b"col2"
        qual3 = b"col3"

        partial_row_data = self._make_one(None)
        partial_row_data._cells = {
            family_name1: {qual1: cell1, qual2: cell2},
            family_name2: {qual3: cell3},
        }

        result = partial_row_data.to_dict()
        expected_result = {
            b"name1:col1": cell1,
            b"name1:col2": cell2,
            b"name2:col3": cell3,
        }
        self.assertEqual(result, expected_result)

    def test_cell_value(self):
        family_name = u"name1"
        qualifier = b"col1"
        cell = _make_cell(b"value-bytes")

        partial_row_data = self._make_one(None)
        partial_row_data._cells = {family_name: {qualifier: [cell]}}

        result = partial_row_data.cell_value(family_name, qualifier)
        self.assertEqual(result, cell.value)

    def test_cell_value_invalid_index(self):
        family_name = u"name1"
        qualifier = b"col1"
        cell = _make_cell(b"")

        partial_row_data = self._make_one(None)
        partial_row_data._cells = {family_name: {qualifier: [cell]}}

        with self.assertRaises(IndexError):
            partial_row_data.cell_value(family_name, qualifier, index=None)

    def test_cell_value_invalid_column_family_key(self):
        family_name = u"name1"
        qualifier = b"col1"

        partial_row_data = self._make_one(None)

        with self.assertRaises(KeyError):
            partial_row_data.cell_value(family_name, qualifier)

    def test_cell_value_invalid_column_key(self):
        family_name = u"name1"
        qualifier = b"col1"

        partial_row_data = self._make_one(None)
        partial_row_data._cells = {family_name: {}}

        with self.assertRaises(KeyError):
            partial_row_data.cell_value(family_name, qualifier)

    def test_cell_values(self):
        family_name = u"name1"
        qualifier = b"col1"
        cell = _make_cell(b"value-bytes")

        partial_row_data = self._make_one(None)
        partial_row_data._cells = {family_name: {qualifier: [cell]}}

        values = []
        for value, timestamp_micros in partial_row_data.cell_values(
            family_name, qualifier
        ):
            values.append(value)

        self.assertEqual(values[0], cell.value)

    def test_cell_values_with_max_count(self):
        family_name = u"name1"
        qualifier = b"col1"
        cell_1 = _make_cell(b"value-bytes-1")
        cell_2 = _make_cell(b"value-bytes-2")

        partial_row_data = self._make_one(None)
        partial_row_data._cells = {family_name: {qualifier: [cell_1, cell_2]}}

        values = []
        for value, timestamp_micros in partial_row_data.cell_values(
            family_name, qualifier, max_count=1
        ):
            values.append(value)

        self.assertEqual(1, len(values))
        self.assertEqual(values[0], cell_1.value)

    def test_cells_property(self):
        partial_row_data = self._make_one(None)
        cells = {1: 2}
        partial_row_data._cells = cells
        self.assertEqual(partial_row_data.cells, cells)

    def test_row_key_getter(self):
        row_key = object()
        partial_row_data = self._make_one(row_key)
        self.assertIs(partial_row_data.row_key, row_key)


class _Client(object):

    data_stub = None


class Test_retry_read_rows_exception(unittest.TestCase):
    @staticmethod
    def _call_fut(exc):
        from google.cloud.bigtable.row_data import _retry_read_rows_exception

        return _retry_read_rows_exception(exc)

    @staticmethod
    def _make_grpc_call_error(exception):
        from grpc import Call
        from grpc import RpcError

        class TestingException(Call, RpcError):
            def __init__(self, exception):
                self.exception = exception

            def code(self):
                return self.exception.grpc_status_code

            def details(self):
                return "Testing"

        return TestingException(exception)

    def test_w_miss(self):
        from google.api_core.exceptions import Conflict

        exception = Conflict("testing")
        self.assertFalse(self._call_fut(exception))

    def test_w_service_unavailable(self):
        from google.api_core.exceptions import ServiceUnavailable

        exception = ServiceUnavailable("testing")
        self.assertTrue(self._call_fut(exception))

    def test_w_deadline_exceeded(self):
        from google.api_core.exceptions import DeadlineExceeded

        exception = DeadlineExceeded("testing")
        self.assertTrue(self._call_fut(exception))

    def test_w_miss_wrapped_in_grpc(self):
        from google.api_core.exceptions import Conflict

        wrapped = Conflict("testing")
        exception = self._make_grpc_call_error(wrapped)
        self.assertFalse(self._call_fut(exception))

    def test_w_service_unavailable_wrapped_in_grpc(self):
        from google.api_core.exceptions import ServiceUnavailable

        wrapped = ServiceUnavailable("testing")
        exception = self._make_grpc_call_error(wrapped)
        self.assertTrue(self._call_fut(exception))

    def test_w_deadline_exceeded_wrapped_in_grpc(self):
        from google.api_core.exceptions import DeadlineExceeded

        wrapped = DeadlineExceeded("testing")
        exception = self._make_grpc_call_error(wrapped)
        self.assertTrue(self._call_fut(exception))


class TestPartialRowsData(unittest.TestCase):
    ROW_KEY = b"row-key"
    FAMILY_NAME = u"family"
    QUALIFIER = b"qualifier"
    TIMESTAMP_MICROS = 100
    VALUE = b"value"

    @staticmethod
    def _get_target_class():
        from google.cloud.bigtable.row_data import PartialRowsData

        return PartialRowsData

    def _make_one(self, *args, **kwargs):
        return self._get_target_class()(*args, **kwargs)

    def test_constructor(self):
        from google.cloud.bigtable.row_data import DEFAULT_RETRY_READ_ROWS

        read_method = mock.Mock()
        request = object()

        instance = self._make_one(read_method, request)

        self.assertIs(instance.read_method, read_method)
        self.assertIs(instance.request, request)
        self.assertEqual(instance.rows, {})
        self.assertIs(instance.retry, DEFAULT_RETRY_READ_ROWS)
        self.assertEqual(instance.response_iterator, read_method.return_value)
        self.assertEqual(instance.state, instance.NEW_ROW)

        read_method.assert_called_once_with(
            request,
            timeout=DEFAULT_RETRY_READ_ROWS._deadline + 1,
        )

    def test_constructor_with_retry(self):
        from google.cloud.bigtable.row_data import DEFAULT_RETRY_READ_ROWS

        read_method = mock.Mock()
        request = object()
        deadline = 123
        retry = DEFAULT_RETRY_READ_ROWS.with_deadline(123)

        instance = self._make_one(read_method, request, retry)

        self.assertIs(instance.read_method, read_method)
        self.assertIs(instance.request, request)
        self.assertEqual(instance.rows, {})
        self.assertIs(instance.retry, retry)
        self.assertEqual(instance.response_iterator, read_method.return_value)
        self.assertEqual(instance.state, instance.NEW_ROW)

        read_method.assert_called_once_with(request, timeout=deadline + 1)

    def _consume_all(self, instance):
        return [row.row_key for row in instance]

    def test___iter__(self):
        chunk = _ReadRowsResponseCellChunkPB(
            row_key=self.ROW_KEY,
            family_name=self.FAMILY_NAME,
            qualifier=self.QUALIFIER,
            timestamp_micros=self.TIMESTAMP_MICROS,
            value=self.VALUE,
            commit_row=True,
        )
        chunks = [chunk]

        response = _ReadRowsResponseV2(chunks)
        iterator = iter([response])
        read_method = mock.Mock(return_value=iterator)
        request = object()

        instance = self._make_one(read_method, request)

        self.assertEqual(self._consume_all(instance), [self.ROW_KEY])

    def test___iter___new_row_w_row(self):
        chunk = _ReadRowsResponseCellChunkPB(
            row_key=self.ROW_KEY,
            family_name=self.FAMILY_NAME,
            qualifier=self.QUALIFIER,
            timestamp_micros=self.TIMESTAMP_MICROS,
            value=self.VALUE,
            commit_row=True,
        )
        chunks = [chunk]

        response = _ReadRowsResponseV2(chunks)
        responses = [response]
        iterator = iter(responses)

        read_method = mock.Mock(return_value=iterator)
        request = object()
        instance = self._make_one(read_method, request)

        self.assertEqual(self._consume_all(instance), [self.ROW_KEY])

        self.assertEqual(instance._counter, 1)
        self.assertEqual(instance.state, instance.NEW_ROW)

    def test___iter___w_multiple_chunks(self):
        chunk1 = _ReadRowsResponseCellChunkPB(
            row_key=self.ROW_KEY,
            family_name=self.FAMILY_NAME,
            qualifier=self.QUALIFIER,
            timestamp_micros=self.TIMESTAMP_MICROS,
            value=self.VALUE,
            commit_row=False,
        )
        chunk2 = _ReadRowsResponseCellChunkPB(
            qualifier=self.QUALIFIER + b"1",
            timestamp_micros=self.TIMESTAMP_MICROS,
            value=self.VALUE,
            commit_row=True,
        )
        chunks = [chunk1, chunk2]

        response = _ReadRowsResponseV2(chunks)
        responses = [response]
        iterator = iter(responses)

        read_method = mock.Mock(return_value=iterator)
        request = object()
        instance = self._make_one(read_method, request)

        self.assertEqual(self._consume_all(instance), [self.ROW_KEY])

        self.assertEqual(instance._counter, 1)
        self.assertEqual(instance.state, instance.NEW_ROW)

    def test___iter___w_cancellation(self):
        chunk1 = _ReadRowsResponseCellChunkPB(
            row_key=self.ROW_KEY,
            family_name=self.FAMILY_NAME,
            qualifier=self.QUALIFIER,
            timestamp_micros=self.TIMESTAMP_MICROS,
            value=self.VALUE,
            commit_row=True,
        )
        chunk2 = _ReadRowsResponseCellChunkPB(
            row_key=b"other-row",
            family_name=self.FAMILY_NAME,
            qualifier=self.QUALIFIER,
            timestamp_micros=self.TIMESTAMP_MICROS + 100,
            value=self.VALUE,
            commit_row=True,
        )
        chunks = [chunk1, chunk2]

        response = _ReadRowsResponseV2(chunks)
        iterator = _MockCancellableIterator(response)
        read_method = mock.Mock(return_value=iterator)
        request = object()

        instance = self._make_one(read_method, request)

        result = []

        for row in instance:
            result.append(row.row_key)
            instance.cancel()

        self.assertEqual(result, [self.ROW_KEY])

    def test___iter___w_retry(self):
        from google.api_core import retry

        retry_read_rows = retry.Retry(predicate=_read_rows_retry_exception)

        chunk = _ReadRowsResponseCellChunkPB(
            row_key=self.ROW_KEY,
            family_name=self.FAMILY_NAME,
            qualifier=self.QUALIFIER,
            timestamp_micros=self.TIMESTAMP_MICROS,
            value=self.VALUE,
            commit_row=True,
        )
        chunks = [chunk]
        response = _ReadRowsResponseV2(chunks)

        failed_iterator = _MockFailureIterator_1()
        iterator = _MockCancellableIterator(response)

        read_method = mock.Mock(side_effect=[failed_iterator, iterator])
        request = object()

        instance = self._make_one(read_method, request, retry_read_rows)

        self.assertEqual(self._consume_all(instance), [self.ROW_KEY])

    def test_cancel(self):
        iterator = _MockCancellableIterator()
        read_method = mock.Mock(return_value=iterator)
        request = object()
        instance = self._make_one(read_method, request)
        self.assertEqual(iterator.cancel_calls, 0)

        instance.cancel()

        self.assertEqual(iterator.cancel_calls, 1)
        self.assertEqual(list(instance), [])

    # 'consume_next' tested via 'TestPartialRowsData_JSON_acceptance_tests'

    def test__copy_from_previous_unset(self):
        iterator = iter([])
        read_method = mock.Mock(return_value=iterator)
        request = object()
        instance = self._make_one(read_method, request)
        cell = _PartialCellData()

        instance._copy_from_previous(cell)

        self.assertEqual(cell.row_key, b"")
        self.assertEqual(cell.family_name, u"")
        self.assertIsNone(cell.qualifier)
        self.assertEqual(cell.timestamp_micros, 0)
        self.assertEqual(cell.labels, [])

    def test__copy_from_previous_blank(self):
        ROW_KEY = "RK"
        FAMILY_NAME = u"A"
        QUALIFIER = b"C"
        TIMESTAMP_MICROS = 100
        LABELS = ["L1", "L2"]
        iterator = iter([])
        read_method = mock.Mock(return_value=iterator)
        request = object()
        instance = self._make_one(read_method, request)
        cell = _PartialCellData(
            row_key=ROW_KEY,
            family_name=FAMILY_NAME,
            qualifier=QUALIFIER,
            timestamp_micros=TIMESTAMP_MICROS,
            labels=LABELS,
        )
        instance._previous_cell = _PartialCellData()

        instance._copy_from_previous(cell)

        self.assertEqual(cell.row_key, ROW_KEY)
        self.assertEqual(cell.family_name, FAMILY_NAME)
        self.assertEqual(cell.qualifier, QUALIFIER)
        self.assertEqual(cell.timestamp_micros, TIMESTAMP_MICROS)
        self.assertEqual(cell.labels, LABELS)

    def test__copy_from_previous_filled(self):
        ROW_KEY = "RK"
        FAMILY_NAME = u"A"
        QUALIFIER = b"C"
        TIMESTAMP_MICROS = 100
        LABELS = ["L1", "L2"]
        iterator = iter([])
        read_method = mock.Mock(return_value=iterator)
        request = object()
        instance = self._make_one(read_method, request)
        instance._previous_cell = _PartialCellData(
            row_key=ROW_KEY,
            family_name=FAMILY_NAME,
            qualifier=QUALIFIER,
            timestamp_micros=TIMESTAMP_MICROS,
            labels=LABELS,
        )
        cell = _PartialCellData()

        instance._copy_from_previous(cell)

        self.assertEqual(cell.row_key, ROW_KEY)
        self.assertEqual(cell.family_name, FAMILY_NAME)
        self.assertEqual(cell.qualifier, QUALIFIER)
        self.assertEqual(cell.timestamp_micros, 0)
        self.assertEqual(cell.labels, [])

    def test_valid_last_scanned_row_key_on_start(self):
        response = _ReadRowsResponseV2(chunks=(), last_scanned_row_key="2.AFTER")
        iterator = iter([response])
        read_method = mock.Mock(return_value=iterator)
        request = object()
        instance = self._make_one(read_method, request)
        instance.last_scanned_row_key = "1.BEFORE"

        self._consume_all(instance)

        self.assertEqual(instance.last_scanned_row_key, "2.AFTER")

    def test_invalid_empty_chunk(self):
        from google.cloud.bigtable.row_data import InvalidChunk

        chunks = _generate_cell_chunks([""])
        response = _ReadRowsResponseV2(chunks)
        iterator = iter([response])
        read_method = mock.Mock(return_value=iterator)
        request = object()
        instance = self._make_one(read_method, request)

        with self.assertRaises(InvalidChunk):
            self._consume_all(instance)

    def test_state_cell_in_progress(self):
        LABELS = ["L1", "L2"]

        request = object()
        read_rows = mock.MagicMock()
        instance = self._make_one(read_rows, request)

        chunk = _ReadRowsResponseCellChunkPB(
            row_key=self.ROW_KEY,
            family_name=self.FAMILY_NAME,
            qualifier=self.QUALIFIER,
            timestamp_micros=self.TIMESTAMP_MICROS,
            value=self.VALUE,
            labels=LABELS,
        )
        instance._update_cell(chunk)

        more_cell_data = _ReadRowsResponseCellChunkPB(value=self.VALUE)
        instance._update_cell(more_cell_data)

        self.assertEqual(instance._cell.row_key, self.ROW_KEY)
        self.assertEqual(instance._cell.family_name, self.FAMILY_NAME)
        self.assertEqual(instance._cell.qualifier, self.QUALIFIER)
        self.assertEqual(instance._cell.timestamp_micros, self.TIMESTAMP_MICROS)
        self.assertEqual(instance._cell.labels, LABELS)
        self.assertEqual(instance._cell.value, self.VALUE + self.VALUE)


class Test_ReadRowsRequestManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table_name = "table_name"
        cls.row_range1 = RowRange(b"row_key21", b"row_key29")
        cls.row_range2 = RowRange(b"row_key31", b"row_key39")
        cls.row_range3 = RowRange(b"row_key41", b"row_key49")

        cls.request = _ReadRowsRequestPB(table_name=cls.table_name)
        cls.request.rows.row_ranges.add(**cls.row_range1.get_range_kwargs())
        cls.request.rows.row_ranges.add(**cls.row_range2.get_range_kwargs())
        cls.request.rows.row_ranges.add(**cls.row_range3.get_range_kwargs())

    @staticmethod
    def _get_target_class():
        from google.cloud.bigtable.row_data import _ReadRowsRequestManager

        return _ReadRowsRequestManager

    def _make_one(self, *args, **kwargs):
        return self._get_target_class()(*args, **kwargs)

    def test_constructor(self):
        request = mock.Mock()
        last_scanned_key = "last_key"
        rows_read_so_far = 10

        request_manager = self._make_one(request, last_scanned_key, rows_read_so_far)
        self.assertEqual(request, request_manager.message)
        self.assertEqual(last_scanned_key, request_manager.last_scanned_key)
        self.assertEqual(rows_read_so_far, request_manager.rows_read_so_far)

    def test__filter_row_key(self):
        table_name = "table_name"
        request = _ReadRowsRequestPB(table_name=table_name)
        request.rows.row_keys.extend(
            [b"row_key1", b"row_key2", b"row_key3", b"row_key4"]
        )

        last_scanned_key = b"row_key2"
        request_manager = self._make_one(request, last_scanned_key, 2)
        row_keys = request_manager._filter_rows_keys()

        expected_row_keys = [b"row_key3", b"row_key4"]
        self.assertEqual(expected_row_keys, row_keys)

    def test__filter_row_ranges_all_ranges_added_back(self):
        last_scanned_key = b"row_key14"
        request_manager = self._make_one(self.request, last_scanned_key, 2)
        row_ranges = request_manager._filter_row_ranges()

        exp_row_range1 = data_v2_pb2.RowRange(
            start_key_closed=b"row_key21", end_key_open=b"row_key29"
        )
        exp_row_range2 = data_v2_pb2.RowRange(
            start_key_closed=b"row_key31", end_key_open=b"row_key39"
        )
        exp_row_range3 = data_v2_pb2.RowRange(
            start_key_closed=b"row_key41", end_key_open=b"row_key49"
        )
        exp_row_ranges = [exp_row_range1, exp_row_range2, exp_row_range3]

        self.assertEqual(exp_row_ranges, row_ranges)

    def test__filter_row_ranges_all_ranges_already_read(self):
        last_scanned_key = b"row_key54"
        request_manager = self._make_one(self.request, last_scanned_key, 2)
        row_ranges = request_manager._filter_row_ranges()

        self.assertEqual(row_ranges, [])

    def test__filter_row_ranges_all_ranges_already_read_open_closed(self):
        last_scanned_key = b"row_key54"

        row_range1 = RowRange(b"row_key21", b"row_key29", False, True)
        row_range2 = RowRange(b"row_key31", b"row_key39")
        row_range3 = RowRange(b"row_key41", b"row_key49", False, True)

        request = _ReadRowsRequestPB(table_name=self.table_name)
        request.rows.row_ranges.add(**row_range1.get_range_kwargs())
        request.rows.row_ranges.add(**row_range2.get_range_kwargs())
        request.rows.row_ranges.add(**row_range3.get_range_kwargs())

        request_manager = self._make_one(request, last_scanned_key, 2)
        request_manager.new_message = _ReadRowsRequestPB(table_name=self.table_name)
        row_ranges = request_manager._filter_row_ranges()

        self.assertEqual(row_ranges, [])

    def test__filter_row_ranges_some_ranges_already_read(self):
        last_scanned_key = b"row_key22"
        request_manager = self._make_one(self.request, last_scanned_key, 2)
        request_manager.new_message = _ReadRowsRequestPB(table_name=self.table_name)
        row_ranges = request_manager._filter_row_ranges()

        exp_row_range1 = data_v2_pb2.RowRange(
            start_key_open=b"row_key22", end_key_open=b"row_key29"
        )
        exp_row_range2 = data_v2_pb2.RowRange(
            start_key_closed=b"row_key31", end_key_open=b"row_key39"
        )
        exp_row_range3 = data_v2_pb2.RowRange(
            start_key_closed=b"row_key41", end_key_open=b"row_key49"
        )
        exp_row_ranges = [exp_row_range1, exp_row_range2, exp_row_range3]

        self.assertEqual(exp_row_ranges, row_ranges)

    def test_build_updated_request(self):
        from google.cloud.bigtable.row_filters import RowSampleFilter

        row_filter = RowSampleFilter(0.33)
        last_scanned_key = b"row_key25"
        request = _ReadRowsRequestPB(
            filter=row_filter.to_pb(), rows_limit=8, table_name=self.table_name
        )
        request.rows.row_ranges.add(**self.row_range1.get_range_kwargs())

        request_manager = self._make_one(request, last_scanned_key, 2)

        result = request_manager.build_updated_request()

        expected_result = _ReadRowsRequestPB(
            table_name=self.table_name, filter=row_filter.to_pb(), rows_limit=6
        )
        expected_result.rows.row_ranges.add(
            start_key_open=last_scanned_key, end_key_open=self.row_range1.end_key
        )

        self.assertEqual(expected_result, result)

    def test_build_updated_request_full_table(self):
        last_scanned_key = b"row_key14"

        request = _ReadRowsRequestPB(table_name=self.table_name)
        request_manager = self._make_one(request, last_scanned_key, 2)

        result = request_manager.build_updated_request()
        expected_result = _ReadRowsRequestPB(table_name=self.table_name, filter={})
        expected_result.rows.row_ranges.add(start_key_open=last_scanned_key)
        self.assertEqual(expected_result, result)

    def test_build_updated_request_no_start_key(self):
        from google.cloud.bigtable.row_filters import RowSampleFilter

        row_filter = RowSampleFilter(0.33)
        last_scanned_key = b"row_key25"
        request = _ReadRowsRequestPB(
            filter=row_filter.to_pb(), rows_limit=8, table_name=self.table_name
        )
        request.rows.row_ranges.add(end_key_open=b"row_key29")

        request_manager = self._make_one(request, last_scanned_key, 2)

        result = request_manager.build_updated_request()

        expected_result = _ReadRowsRequestPB(
            table_name=self.table_name, filter=row_filter.to_pb(), rows_limit=6
        )
        expected_result.rows.row_ranges.add(
            start_key_open=last_scanned_key, end_key_open=b"row_key29"
        )

        self.assertEqual(expected_result, result)

    def test_build_updated_request_no_end_key(self):
        from google.cloud.bigtable.row_filters import RowSampleFilter

        row_filter = RowSampleFilter(0.33)
        last_scanned_key = b"row_key25"
        request = _ReadRowsRequestPB(
            filter=row_filter.to_pb(), rows_limit=8, table_name=self.table_name
        )
        request.rows.row_ranges.add(start_key_closed=b"row_key20")

        request_manager = self._make_one(request, last_scanned_key, 2)

        result = request_manager.build_updated_request()

        expected_result = _ReadRowsRequestPB(
            table_name=self.table_name, filter=row_filter.to_pb(), rows_limit=6
        )
        expected_result.rows.row_ranges.add(start_key_open=last_scanned_key)

        self.assertEqual(expected_result, result)

    def test_build_updated_request_rows(self):
        from google.cloud.bigtable.row_filters import RowSampleFilter

        row_filter = RowSampleFilter(0.33)
        last_scanned_key = b"row_key4"
        request = _ReadRowsRequestPB(
            filter=row_filter.to_pb(), rows_limit=5, table_name=self.table_name
        )
        request.rows.row_keys.extend(
            [
                b"row_key1",
                b"row_key2",
                b"row_key4",
                b"row_key5",
                b"row_key7",
                b"row_key9",
            ]
        )

        request_manager = self._make_one(request, last_scanned_key, 3)

        result = request_manager.build_updated_request()

        expected_result = _ReadRowsRequestPB(
            table_name=self.table_name, filter=row_filter.to_pb(), rows_limit=2
        )
        expected_result.rows.row_keys.extend([b"row_key5", b"row_key7", b"row_key9"])

        self.assertEqual(expected_result, result)

    def test_build_updated_request_rows_limit(self):
        last_scanned_key = b"row_key14"

        request = _ReadRowsRequestPB(table_name=self.table_name, rows_limit=10)
        request_manager = self._make_one(request, last_scanned_key, 2)

        result = request_manager.build_updated_request()
        expected_result = _ReadRowsRequestPB(
            table_name=self.table_name, filter={}, rows_limit=8
        )
        expected_result.rows.row_ranges.add(start_key_open=last_scanned_key)
        self.assertEqual(expected_result, result)

    def test__key_already_read(self):
        last_scanned_key = b"row_key14"
        request = _ReadRowsRequestPB(table_name=self.table_name)
        request_manager = self._make_one(request, last_scanned_key, 2)

        self.assertTrue(request_manager._key_already_read(b"row_key11"))
        self.assertFalse(request_manager._key_already_read(b"row_key16"))


class TestPartialRowsData_JSON_acceptance_tests(unittest.TestCase):

    _json_tests = None

    @staticmethod
    def _get_target_class():
        from google.cloud.bigtable.row_data import PartialRowsData

        return PartialRowsData

    def _make_one(self, *args, **kwargs):
        return self._get_target_class()(*args, **kwargs)

    def _load_json_test(self, test_name):
        import os

        if self.__class__._json_tests is None:
            dirname = os.path.dirname(__file__)
            filename = os.path.join(dirname, "read-rows-acceptance-test.json")
            raw = _parse_readrows_acceptance_tests(filename)
            tests = self.__class__._json_tests = {}
            for (name, chunks, results) in raw:
                tests[name] = chunks, results
        return self.__class__._json_tests[test_name]

    # JSON Error cases:  invalid chunks

    def _fail_during_consume(self, testcase_name):
        from google.cloud.bigtable.row_data import InvalidChunk

        chunks, results = self._load_json_test(testcase_name)
        response = _ReadRowsResponseV2(chunks)
        iterator = _MockCancellableIterator(response)
        read_method = mock.Mock(return_value=iterator)
        request = object()
        prd = self._make_one(read_method, request)

        with self.assertRaises(InvalidChunk):
            prd.consume_all()

        expected_result = self._sort_flattend_cells(
            [result for result in results if not result["error"]]
        )
        flattened = self._sort_flattend_cells(_flatten_cells(prd))
        self.assertEqual(flattened, expected_result)

    def test_invalid_no_cell_key_before_commit(self):
        self._fail_during_consume("invalid - no cell key before commit")

    def test_invalid_no_cell_key_before_value(self):
        self._fail_during_consume("invalid - no cell key before value")

    def test_invalid_new_col_family_wo_qualifier(self):
        self._fail_during_consume("invalid - new col family must specify qualifier")

    def test_invalid_no_commit_between_rows(self):
        self._fail_during_consume("invalid - no commit between rows")

    def test_invalid_no_commit_after_first_row(self):
        self._fail_during_consume("invalid - no commit after first row")

    def test_invalid_duplicate_row_key(self):
        self._fail_during_consume("invalid - duplicate row key")

    def test_invalid_new_row_missing_row_key(self):
        self._fail_during_consume("invalid - new row missing row key")

    def test_invalid_bare_reset(self):
        self._fail_during_consume("invalid - bare reset")

    def test_invalid_bad_reset_no_commit(self):
        self._fail_during_consume("invalid - bad reset, no commit")

    def test_invalid_missing_key_after_reset(self):
        self._fail_during_consume("invalid - missing key after reset")

    def test_invalid_reset_with_chunk(self):
        self._fail_during_consume("invalid - reset with chunk")

    def test_invalid_commit_with_chunk(self):
        self._fail_during_consume("invalid - commit with chunk")

    # JSON Error cases:  incomplete final row

    def _sort_flattend_cells(self, flattened):
        import operator

        key_func = operator.itemgetter("rk", "fm", "qual")
        return sorted(flattened, key=key_func)

    def _incomplete_final_row(self, testcase_name):
        chunks, results = self._load_json_test(testcase_name)
        response = _ReadRowsResponseV2(chunks)
        iterator = _MockCancellableIterator(response)
        read_method = mock.Mock(return_value=iterator)
        request = object()
        prd = self._make_one(read_method, request)
        with self.assertRaises(ValueError):
            prd.consume_all()
        self.assertEqual(prd.state, prd.ROW_IN_PROGRESS)
        expected_result = self._sort_flattend_cells(
            [result for result in results if not result["error"]]
        )
        flattened = self._sort_flattend_cells(_flatten_cells(prd))
        self.assertEqual(flattened, expected_result)

    def test_invalid_no_commit(self):
        self._incomplete_final_row("invalid - no commit")

    def test_invalid_last_row_missing_commit(self):
        self._incomplete_final_row("invalid - last row missing commit")

    # Non-error cases

    _marker = object()

    def _match_results(self, testcase_name, expected_result=_marker):
        chunks, results = self._load_json_test(testcase_name)
        response = _ReadRowsResponseV2(chunks)
        iterator = _MockCancellableIterator(response)
        read_method = mock.Mock(return_value=iterator)
        request = object()
        prd = self._make_one(read_method, request)
        prd.consume_all()
        flattened = self._sort_flattend_cells(_flatten_cells(prd))
        if expected_result is self._marker:
            expected_result = self._sort_flattend_cells(results)
        self.assertEqual(flattened, expected_result)

    def test_bare_commit_implies_ts_zero(self):
        self._match_results("bare commit implies ts=0")

    def test_simple_row_with_timestamp(self):
        self._match_results("simple row with timestamp")

    def test_missing_timestamp_implies_ts_zero(self):
        self._match_results("missing timestamp, implied ts=0")

    def test_empty_cell_value(self):
        self._match_results("empty cell value")

    def test_two_unsplit_cells(self):
        self._match_results("two unsplit cells")

    def test_two_qualifiers(self):
        self._match_results("two qualifiers")

    def test_two_families(self):
        self._match_results("two families")

    def test_with_labels(self):
        self._match_results("with labels")

    def test_split_cell_bare_commit(self):
        self._match_results("split cell, bare commit")

    def test_split_cell(self):
        self._match_results("split cell")

    def test_split_four_ways(self):
        self._match_results("split four ways")

    def test_two_split_cells(self):
        self._match_results("two split cells")

    def test_multi_qualifier_splits(self):
        self._match_results("multi-qualifier splits")

    def test_multi_qualifier_multi_split(self):
        self._match_results("multi-qualifier multi-split")

    def test_multi_family_split(self):
        self._match_results("multi-family split")

    def test_two_rows(self):
        self._match_results("two rows")

    def test_two_rows_implicit_timestamp(self):
        self._match_results("two rows implicit timestamp")

    def test_two_rows_empty_value(self):
        self._match_results("two rows empty value")

    def test_two_rows_one_with_multiple_cells(self):
        self._match_results("two rows, one with multiple cells")

    def test_two_rows_multiple_cells_multiple_families(self):
        self._match_results("two rows, multiple cells, multiple families")

    def test_two_rows_multiple_cells(self):
        self._match_results("two rows, multiple cells")

    def test_two_rows_four_cells_two_labels(self):
        self._match_results("two rows, four cells, 2 labels")

    def test_two_rows_with_splits_same_timestamp(self):
        self._match_results("two rows with splits, same timestamp")

    def test_no_data_after_reset(self):
        # JSON testcase has `"results": null`
        self._match_results("no data after reset", expected_result=[])

    def test_simple_reset(self):
        self._match_results("simple reset")

    def test_reset_to_new_val(self):
        self._match_results("reset to new val")

    def test_reset_to_new_qual(self):
        self._match_results("reset to new qual")

    def test_reset_with_splits(self):
        self._match_results("reset with splits")

    def test_two_resets(self):
        self._match_results("two resets")

    def test_reset_to_new_row(self):
        self._match_results("reset to new row")

    def test_reset_in_between_chunks(self):
        self._match_results("reset in between chunks")

    def test_empty_cell_chunk(self):
        self._match_results("empty cell chunk")

    def test_empty_second_qualifier(self):
        self._match_results("empty second qualifier")


def _flatten_cells(prd):
    # Match results format from JSON testcases.
    # Doesn't handle error cases.
    from google.cloud._helpers import _bytes_to_unicode
    from google.cloud._helpers import _microseconds_from_datetime

    for row_key, row in prd.rows.items():
        for family_name, family in row.cells.items():
            for qualifier, column in family.items():
                for cell in column:
                    yield {
                        u"rk": _bytes_to_unicode(row_key),
                        u"fm": family_name,
                        u"qual": _bytes_to_unicode(qualifier),
                        u"ts": _microseconds_from_datetime(cell.timestamp),
                        u"value": _bytes_to_unicode(cell.value),
                        u"label": u" ".join(cell.labels),
                        u"error": False,
                    }


class _MockCancellableIterator(object):

    cancel_calls = 0

    def __init__(self, *values):
        self.iter_values = iter(values)

    def cancel(self):
        self.cancel_calls += 1

    def next(self):
        return next(self.iter_values)

    __next__ = next


class _MockFailureIterator_1(object):
    def next(self):
        raise DeadlineExceeded("Failed to read from server")

    __next__ = next


class _PartialCellData(object):

    row_key = b""
    family_name = u""
    qualifier = None
    timestamp_micros = 0

    def __init__(self, **kw):
        self.labels = kw.pop("labels", [])
        self.__dict__.update(kw)


class _ReadRowsResponseV2(object):
    def __init__(self, chunks, last_scanned_row_key=""):
        self.chunks = chunks
        self.last_scanned_row_key = last_scanned_row_key


def _generate_cell_chunks(chunk_text_pbs):
    from google.protobuf.text_format import Merge
    from google.cloud.bigtable_v2.proto.bigtable_pb2 import ReadRowsResponse

    chunks = []

    for chunk_text_pb in chunk_text_pbs:
        chunk = ReadRowsResponse.CellChunk()
        chunks.append(Merge(chunk_text_pb, chunk))

    return chunks


def _parse_readrows_acceptance_tests(filename):
    """Parse acceptance tests from JSON

    See
    https://github.com/googleapis/python-bigtable/blob/master/\
    tests/unit/read-rows-acceptance-test.json
    """
    import json

    with open(filename) as json_file:
        test_json = json.load(json_file)

    for test in test_json["tests"]:
        name = test["name"]
        chunks = _generate_cell_chunks(test["chunks"])
        results = test["results"]
        yield name, chunks, results


def _ReadRowsResponseCellChunkPB(*args, **kw):
    from google.cloud.bigtable_v2.proto import bigtable_pb2 as messages_v2_pb2

    family_name = kw.pop("family_name", None)
    qualifier = kw.pop("qualifier", None)
    message = messages_v2_pb2.ReadRowsResponse.CellChunk(*args, **kw)

    if family_name:
        message.family_name.value = family_name
    if qualifier:
        message.qualifier.value = qualifier

    return message


def _make_cell(value):
    from google.cloud.bigtable import row_data

    return row_data.Cell(value, TestCell.timestamp_micros)


def _ReadRowsRequestPB(*args, **kw):
    from google.cloud.bigtable_v2.proto import bigtable_pb2 as messages_v2_pb2

    return messages_v2_pb2.ReadRowsRequest(*args, **kw)


def _read_rows_retry_exception(exc):
    return isinstance(exc, DeadlineExceeded)
