
import unittest
from mock import MagicMock, patch

from sqlalchemy_grt import AttributeObject, ColumnObject, camelize, functionalize, quote, endsWith, \
    singular, SqlaType, TableObject


class TestUtils(unittest.TestCase):

    def test_quote(self):
        self.assertEquals('"test"', quote('test'))

    def test_endswith(self):
        self.assertTrue(endsWith('something', ('ing', 'gni')))
        self.assertFalse(endsWith('something', ('pot', 'gni')))

    def test_singular(self):
        self.assertEquals('index', singular('indices'))
        self.assertEquals('suffix', singular('suffixes'))
        self.assertEquals('alias', singular('aliases'))
        self.assertEquals('address', singular('addresses'))
        self.assertEquals('company', singular('company'))
        self.assertEquals('party', singular('parties'))
        self.assertEquals('tree', singular('tree'))
        self.assertEquals('name', singular('names'))

    def test_camelize(self):
        self.assertEquals('SomethingHere', camelize('sOmEtHiNg_hErE'))

    def test_functionalize(self):
        self.assertEquals('somethingHere', functionalize('sOmEtHiNg_hErE'))


class TestAttributeObject(unittest.TestCase):

    def test_00(self):
        self.assertEquals('test = Test()', str(AttributeObject('test', 'Test')))

    def test_01(self):
        attr = AttributeObject('test', 'Test')
        attr.comment = 'pylint-test'
        self.assertEquals('test = Test()  # pylint-test', str(attr))

    def test_02(self):
        attr = AttributeObject('test', 'Test')
        attr.args.extend(['"a"', 'b', 'c'])
        attr.kwargs['test'] = '"value"'
        attr.comment = 'pylint-test'
        attr.tab = '    '
        self.assertEquals('    test = Test("a", b, c, test="value")  # pylint-test', str(attr))

    def test_03(self):
        self.assertEquals('Test()', str(AttributeObject(None, 'Test')))

    def test_04(self):
        attr = AttributeObject('test', 'Test')
        attr.tab = '    '
        attr.args.extend(['"qwertyuiop"', 'asdfghjkl', 'zxcvbnm', 'poiuytrew', 'qwertyui'])
        attr.comment = 'pylint-test'
        attr.kwargs.update({
            'sdljfsdf': '12',
            'sldkjfasdf': '"ewuhofnocnwoedsf"',
            'eoripu': '"ewiu"',
            'cxmvbxcvmnb': '"sdkjhflknslkfwelcwiemoimcoiwemc"',
            's230948d': '"ewuhofnocnwoedsf"',
        })
        expected = [
            '    test = Test(  # pylint-test',
            '        "qwertyuiop", asdfghjkl, zxcvbnm, poiuytrew, qwertyui, sdljfsdf=12, sldkjfasdf="ewuhofnocnwoedsf",',
            '        eoripu="ewiu", cxmvbxcvmnb="sdkjhflknslkfwelcwiemoimcoiwemc", s230948d="ewuhofnocnwoedsf"',
            '    )'
        ]
        self.assertEquals('\n'.join(expected), str(attr))

    def test_05(self):
        attr = AttributeObject(None, 'Integer')
        attr.kwargs['test'] = 'True'
        self.assertEquals('Integer(test=True)', str(attr))


class TestGetType(unittest.TestCase):

    def test_integer(self):
        obj = SqlaType()
        self.assertEquals(0, len(obj.mysql))
        self.assertEquals(0, len(obj.sqla))

        int_type = MagicMock(formattedType='INT(12)', flags='UNSIGNED')
        self.assertEquals('INTEGER(unsigned=True)', obj.get(int_type))
        self.assertEquals(1, len(obj.mysql))
        self.assertEquals(1, len(obj.sqla))

        self.assertEquals(['Integer'], list(obj.sqla))
        self.assertEquals(['INTEGER'], list(obj.mysql))

        int_type = MagicMock(formattedType='INT(12)')
        self.assertEquals('INTEGER', obj.get(int_type))
        self.assertEquals(1, len(obj.mysql))
        self.assertEquals(1, len(obj.sqla))


    def test_var(self):
        obj = SqlaType()
        self.assertEquals(0, len(obj.mysql))
        self.assertEquals(0, len(obj.sqla))

        varchar_type = MagicMock(formattedType='VARCHAR(45)')
        self.assertEquals('VARCHAR(45)', obj.get(varchar_type))
        self.assertEquals(1, len(obj.mysql))
        self.assertEquals(1, len(obj.sqla))

        self.assertEquals('VARCHAR', list(obj.mysql)[0])
        self.assertEquals('String as VARCHAR', list(obj.sqla)[0])

    def test_bool(self):
        obj = SqlaType()
        self.assertEquals(0, len(obj.mysql))
        self.assertEquals(0, len(obj.sqla))

        int_type = MagicMock(formattedType='TINYINT(1)', formattedRawType='BOOL')
        self.assertEquals('BOOLEAN', obj.get(int_type))
        self.assertEquals(1, len(obj.mysql))
        self.assertEquals(1, len(obj.sqla))

        self.assertEquals(['Boolean as BOOLEAN'], list(obj.sqla))
        self.assertEquals(['BOOLEAN'], list(obj.mysql))

        int_type = MagicMock(formattedType='BOOLEAN')
        self.assertEquals('BOOLEAN', obj.get(int_type))
        self.assertEquals(1, len(obj.mysql))
        self.assertEquals(1, len(obj.sqla))


class TestColumnObject(unittest.TestCase):

    @patch("sqlalchemy_grt.SqlaType.get", autospec=True)
    def test_name_switch_primary_key(self, get_type_mock):
        get_type_mock.return_value = 'INTEGER'
        column = MagicMock(owner=MagicMock(indices=[MagicMock(
            columns=['id_something'],
            indexType='PRIMARY'
        )]), defaultValue=None)
        column.name = 'id_something'

        column_obj = ColumnObject(column, primary=True)
        self.assertEquals('id', column_obj.name)

        self.assertEquals(
            '    id = Column("id_something", INTEGER, autoincrement=False, primary_key=True)  # pylint: disable=invalid-name',
            str(column_obj)
        )

    @patch("sqlalchemy_grt.SqlaType.get", autospec=True)
    def test_basic(self, get_type_mock):
        get_type_mock.return_value = 'String'
        column = MagicMock(comment='alias=test', defaultValue=None)
        column.name = 'test_column'
        column_obj = ColumnObject(column)
        self.assertEquals('    test = Column("test_column", String)', str(column_obj))

    @patch("sqlalchemy_grt.SqlaType.get", autospec=True)
    def test_datetime(self, get_type_mock):
        get_type_mock.return_value = 'Datetime'
        column = MagicMock(comment='alias=test', defaultValue=None)
        column.name = 'test_column'
        column.defaultValue = 'CURRENT_TIMESTAMP'
        column_obj = ColumnObject(column)
        self.assertEquals('    test = Column("test_column", Datetime, default=datetime.datetime.utcnow)', str(column_obj))
        column.defaultValue = 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
        self.assertEquals(
            '    test = Column("test_column", Datetime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)',
            str(column_obj)
        )

    @patch("sqlalchemy_grt.SqlaType.get", autospec=True)
    def test_few_options(self, get_type_mock):
        get_type_mock.return_value = 'INTEGER'
        column = MagicMock(defaultValue='"test"', isNotNull=1, autoIncrement=1)
        column.name = 'test'

        column_obj = ColumnObject(column, primary=True, unique=True, index=True)

        self.assertEquals(
            '    test = Column(\n'
            '        INTEGER, nullable=False, autoincrement=True, primary_key=True, unique=True, index=True, default="test"\n'
            '    )',
            str(column_obj)
        )

    @patch("sqlalchemy_grt.SqlaType.get", autospec=True)
    def test_backref(self, get_type_mock):
        get_type_mock.return_value = 'INTEGER'

        column = MagicMock(owner=MagicMock(), defaultValue=None, comment="remote_side=remote_test,use_alter=True")
        column.name = 'test'
        column.owner.name = 'tables'
        column_obj = ColumnObject(column)

        column_ref = MagicMock(owner=MagicMock())
        column_ref.name = 'ref'
        column_ref.owner.name = 'table_refs'
        column_ref_obj = ColumnObject(column_ref)

        self.assertIsNone(column_obj.getBackref())

        foreign_key = MagicMock(referencedColumns=[column_ref])
        foreign_key.name = 'fk_test'
        foreign_key.deleteRule = 'NO ACTION'
        foreign_key.updateRule = 'SET NULL'
        column_obj.setForeignKey(foreign_key, column_ref_obj)

        self.assertEquals(
            '    tableRef = relationship("TableRef", foreign_keys=[test], backref="tables", remote_side=[remote_test])',
            column_obj.getBackref()
        )

        self.assertEquals(
            '    test = Column(INTEGER, ForeignKey("table_refs.ref", name="fk_test", use_alter=True, onupdate="SET NULL"))',
            str(column_obj)
        )
        foreign_key.deleteRule = 'CASCADE'
        column_obj.setForeignKey(foreign_key, column_ref_obj)
        self.assertEquals(
            '    test = Column(\n'
            '        INTEGER, ForeignKey("table_refs.ref", name="fk_test", use_alter=True, ondelete="CASCADE", onupdate="SET NULL")\n'
            '    )',
            str(column_obj)
        )


    @patch("sqlalchemy_grt.SqlaType.get", autospec=True)
    def test_backref_ignore(self, get_type_mock):
        get_type_mock.return_value = 'INTEGER'

        column = MagicMock(owner=MagicMock(), defaultValue=None, comment="relation=False")
        column.name = 'test'
        column.owner.name = 'tables'
        column_obj = ColumnObject(column)

        column_ref = MagicMock(owner=MagicMock())
        column_ref.name = 'ref'
        column_ref.owner.name = 'table_refs'
        column_ref_obj = ColumnObject(column_ref)

        self.assertIsNone(column_obj.getBackref())

        foreign_key = MagicMock(referencedColumns=[column_ref])
        foreign_key.name = 'fk_test'
        foreign_key.deleteRule = 'NO ACTION'
        foreign_key.updateRule = 'SET NULL'
        column_obj.setForeignKey(foreign_key, column_ref_obj)

        self.assertEquals('    # relation <tableRef/tables> ignored for this table', column_obj.getBackref())


class TestTableObject(unittest.TestCase):

    def test_basics(self):
        id_col = MagicMock(defaultValue=None, isNotNull=1, autoIncrement=1, formattedType="INT(16)")
        id_col.name = 'id'
        primary_indx = MagicMock(
            columns=[
                MagicMock(referencedColumn=id_col)
            ],
            indexType='PRIMARY'
        )

        name_col = MagicMock(defaultValue=None, isNotNull=1, autoIncrement=0, formattedType="VARCHAR(145)")
        name_col.name = 'name'

        description_col = MagicMock(defaultValue=None, autoIncrement=0, formattedType="BLOB")
        description_col.name = 'description'


        table_mock = MagicMock(tableEngine=None, defaultCharacterSetName='utf8')
        table_mock.name = 'table_test'
        table_mock.columns = [id_col, name_col, description_col]
        table_mock.indices = [primary_indx]
        table = TableObject(table_mock)

        self.assertEquals(
            'class TableTest(DECLARATIVE_BASE):\n'
            '\n'
            '    __tablename__ = \'table_test\'\n'
            '    __table_args__ = (\n'
            '        {\'mysql_charset\': \'utf8\', \'sqlite_autoincrement\': True}\n'
            '    )\n'
            '\n'
            '    id = Column(INTEGER, nullable=False, autoincrement=True, primary_key=True)  # pylint: disable=invalid-name\n'
            '    name = Column(VARCHAR(145), nullable=False)\n'
            '    description = Column(BLOB)\n'
            '\n'
            '    def __repr__(self):\n'
            '        return self.__str__()\n'
            '\n'
            '    def __str__(self):\n'
            '        return "<TableTest(%(id)s)>" % self.__dict__',
            str(table)
        )
