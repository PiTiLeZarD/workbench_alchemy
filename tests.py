
import unittest
from mock import MagicMock, patch

from sqlalchemy_grt import AttributeObject, ColumnObject


class TestAttributeObject(unittest.TestCase):

    def test_00(self):
        self.assertEquals('test = Test()', str(AttributeObject('test', 'Test')))

    def test_01(self):
        attr = AttributeObject('test', 'Test')
        attr.pylint_message = '  # pylint-test'
        self.assertEquals('test = Test()  # pylint-test', str(attr))

    def test_02(self):
        attr = AttributeObject('test', 'Test')
        attr.args.extend(['"a"', 'b', 'c'])
        attr.kwargs['test'] = '"value"'
        attr.pylint_message = '  # pylint-test'
        attr.tab = '    '
        self.assertEquals('    test = Test("a", b, c, test="value")  # pylint-test', str(attr))

    def test_03(self):
        self.assertEquals('Test()', str(AttributeObject(None, 'Test')))


class TestGetType(unittest.TestCase):

    def test_00(self):
        pass


class TestColumnObject(unittest.TestCase):

    @patch("sqlalchemy_grt.getType", autospec=True)
    def test_00(self, getType_mock):
        getType_mock.return_value = 'String'
        column = MagicMock(comment='alias=test', defaultValue=None)
        column.name = 'test_column'
        table_obj = MagicMock(foreign_keys={})
        column_obj = ColumnObject(column, table_obj)
        self.assertEquals('    test = Column("test_column", String)', str(column_obj))


class TestTableObject(unittest.TestCase):

    def test_00(self):
        pass
