
import unittest
from mock import MagicMock, patch

from sqlalchemy_grt import AttributeObject, ColumnObject, camelize, functionalize, quote, endsWith, \
    singular, SqlaType, TableObject

from grt import get_grt_foreignKey, get_grt_column, get_grt_index, get_grt_table


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

    def test_name_switch_primary_key(self):
        column = get_grt_column('id_something', 'table_test', 'INTEGER')
        column.owner.indices.append(get_grt_index(columns=[column]))
        column_obj = ColumnObject(column, primary=True)
        self.assertEquals('id', column_obj.name)

        self.assertEquals(
            '    id = Column("id_something", INTEGER, autoincrement=False, primary_key=True)  # pylint: disable=invalid-name',
            str(column_obj)
        )

    def test_basic(self):
        column_obj = ColumnObject(
            get_grt_column('test_column', 'test_table', 'VARCHAR(45)', comment='alias=test')
        )

        self.assertEquals('    test = Column("test_column", VARCHAR(45))', str(column_obj))

    def test_datetime(self):
        column_obj = ColumnObject(
            get_grt_column('test_column', 'test_table', 'DATETIME', defaultValue='CURRENT_TIMESTAMP', comment='alias=test')
        )

        self.assertEquals('    test = Column("test_column", DATETIME, default=datetime.datetime.utcnow)', str(column_obj))
        column_obj._column.defaultValue = 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
        self.assertEquals(
            '    test = Column("test_column", DATETIME, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)',
            str(column_obj)
        )

    def test_few_options(self):
        column = get_grt_column('test', 'test', 'INTEGER', defaultValue='1234567890', isNotNull=1, autoIncrement=1)
        column_obj = ColumnObject(column, primary=True, unique=True, index=True)

        self.assertEquals(
            '    test = Column(\n'
            '        INTEGER, nullable=False, autoincrement=True, primary_key=True, unique=True, index=True, default=1234567890\n'
            '    )',
            str(column_obj)
        )

    def test_backref(self):
        column_obj = ColumnObject(
            get_grt_column('test', 'tables', 'INTEGER', comment="remote_side=remote_test,use_alter=True")
        )

        column_ref = get_grt_column('ref', 'table_refs', 'INTEGER')

        self.assertIsNone(column_obj.getBackref())

        column_obj.setForeignKey(get_grt_foreignKey('fk_test', referencedColumns=[column_ref]))

        self.assertEquals(
            '    tableRef = relationship("TableRef", foreign_keys=[test], backref="tables", remote_side=[remote_test])',
            column_obj.getBackref()
        )

        self.assertEquals(
            '    test = Column(INTEGER, ForeignKey("table_refs.ref", name="fk_test", use_alter=True, onupdate="SET NULL"))',
            str(column_obj)
        )
        column_obj.foreign_key.deleteRule = 'CASCADE'
        self.assertEquals(
            '    test = Column(\n'
            '        INTEGER, ForeignKey("table_refs.ref", name="fk_test", use_alter=True, ondelete="CASCADE", onupdate="SET NULL")\n'
            '    )',
            str(column_obj)
        )


    def test_backref_ignore(self):
        column_obj = ColumnObject(get_grt_column('test', 'tables', 'INTEGER', comment="relation=False"))
        column_ref = get_grt_column('ref', 'table_refs', 'INTEGER')

        self.assertIsNone(column_obj.getBackref())

        column_obj.setForeignKey(get_grt_foreignKey('fk_test', referencedColumns=[column_ref]))

        self.assertEquals(
            '    # relation for test.ForeignKey ignored as configured in column comment',
            column_obj.getBackref()
        )


class TestTableObject(unittest.TestCase):

    def test_basics(self):
        id_col = get_grt_column('id', 'table_test', 'INT(16)', isNotNull=1, autoIncrement=1)
        name_col = get_grt_column('name', 'table_test', 'VARCHAR(145)', isNotNull=1)
        description_col = get_grt_column('description', 'table_test', 'BLOB')

        table = get_grt_table(
            'table_test',
            columns=[id_col, name_col, description_col],
            indices=[get_grt_index(columns=[id_col])]
        )

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
            str(TableObject(table))
        )

    def test_with_foreignkeys(self):
        id_col = get_grt_column('id', 'table_test', 'INT(16)', isNotNull=1, autoIncrement=1)

        id_other_ref = get_grt_column('id', 'table_test_other', 'INT(16)', isNotNull=1)

        id_other = get_grt_column('id_other', 'table_test', 'INT(16)', isNotNull=1)
        id_other2 = get_grt_column('id_other2', 'table_test', 'INT(16)', isNotNull=1, comment="relation=False")
        id_other3 = get_grt_column('id_other3', 'table_test', 'INT(16)', isNotNull=1, comment="backref=False")
        id_other4 = get_grt_column('id_other4', 'table_test', 'INT(16)', isNotNull=1, comment="remote_side='alias'")
        id_other5 = get_grt_column('id_other5', 'table_test', 'INT(16)', isNotNull=1, comment="backrefname=newbr")

        table = get_grt_table(
            'table_test',
            columns=[id_col, id_other, id_other2, id_other3, id_other4, id_other5],
            indices=[get_grt_index(columns=[id_col])],
            foreignKeys=[
                get_grt_foreignKey('fk_id_other', columns=[id_other], referencedColumns=[id_other_ref]),
                get_grt_foreignKey('fk_id_other2', columns=[id_other2], referencedColumns=[id_other_ref]),
                get_grt_foreignKey('fk_id_other3', columns=[id_other3], referencedColumns=[id_other_ref]),
                get_grt_foreignKey('fk_id_other4', columns=[id_other4], referencedColumns=[id_other_ref]),
                get_grt_foreignKey('fk_id_other5', columns=[id_other5], referencedColumns=[id_other_ref]),
            ]
        )
        self.assertEquals(
            'class TableTest(DECLARATIVE_BASE):\n'
            '\n'
            '    __tablename__ = \'table_test\'\n'
            '    __table_args__ = (\n'
            '        {\'mysql_charset\': \'utf8\', \'sqlite_autoincrement\': True}\n'
            '    )\n'
            '\n'
            '    id = Column(INTEGER, nullable=False, autoincrement=True, primary_key=True)  # pylint: disable=invalid-name\n'
            '    id_other = Column(\n'
            '        INTEGER, ForeignKey("table_test_other.id", name="fk_id_other", onupdate="SET NULL"), nullable=False\n'
            '    )\n'
            '    id_other2 = Column(\n'
            '        INTEGER, ForeignKey("table_test_other.id", name="fk_id_other2", onupdate="SET NULL"), nullable=False\n'
            '    )\n'
            '    id_other3 = Column(\n'
            '        INTEGER, ForeignKey("table_test_other.id", name="fk_id_other3", onupdate="SET NULL"), nullable=False\n'
            '    )\n'
            '    id_other4 = Column(\n'
            '        INTEGER, ForeignKey("table_test_other.id", name="fk_id_other4", onupdate="SET NULL"), nullable=False\n'
            '    )\n'
            '    id_other5 = Column(\n'
            '        INTEGER, ForeignKey("table_test_other.id", name="fk_id_other5", onupdate="SET NULL"), nullable=False\n'
            '    )\n'
            '\n'
            '    tableTestOther = relationship("TableTestOther", foreign_keys=[id_other], backref="tableTest")\n'
            '    # relation for id_other2.ForeignKey ignored as configured in column comment\n'
            '    tableTestOther = relationship("TableTestOther", foreign_keys=[id_other3])\n'
            '    tableTestOther = relationship(\n'
            '        "TableTestOther", foreign_keys=[id_other4], backref="tableTest", remote_side=[\'alias\']\n'
            '    )\n'
            '    tableTestOther = relationship("TableTestOther", foreign_keys=[id_other5], backref="newbr")\n'
            '\n'
            '    def __repr__(self):\n'
            '        return self.__str__()\n'
            '\n'
            '    def __str__(self):\n'
            '        return "<TableTest(%(id)s)>" % self.__dict__',
            str(TableObject(table))
        )
