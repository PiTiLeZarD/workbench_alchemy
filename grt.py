from mock import MagicMock

root = MagicMock()
modules = MagicMock()


def get_grt_foreignKey(fk_name, columns=None, referencedColumns=None, deleteRule='NO ACTION', updateRule='SET NULL'):
    """Mock a foreign key

    Returns a Mock object representing the basic needs of a foreignKey

    Arguments:
        fk_name {str} -- The name of the foreign key

    Keyword Arguments:
        columns {list} -- Local columns this key binds to (default: {None})
        referencedColumns {list} -- Remote columns this key binds to (default: {None})
        deleteRule {str} -- Delete rule (default: {'NO ACTION'})
        updateRule {str} -- Update rule (default: {'SET NULL'})

    Returns:
        MagicMock -- GRT Compatible Foreign Key
    """
    fk = MagicMock(
        columns=columns or [],
        referencedColumns=referencedColumns or [],
        deleteRule=deleteRule,
        updateRule=updateRule
    )
    fk.name = fk_name
    return fk


def get_grt_index(name, index_type='PRIMARY', columns=None):
    """Mock an index

    Returns a Mock object representing the basic needs of an index

    Arguments:
        name {str} -- The name of the index

    Keyword Arguments:
        index_type {str} -- The type of index (default: {'PRIMARY'})
        columns {list} -- The local colums this index binds to (default: {None})

    Returns:
        MagicMock -- GRT Compatible Index
    """
    indx = MagicMock(
        columns=[MagicMock(referencedColumn=c) for c in (columns or [])],
        indexType=index_type
    )
    indx.name = name
    return indx


def get_grt_table(table_name, columns=None, indices=None, foreignKeys=None, tableEngine=None, charset='utf8', comment=None):
    """Mock a table

    Returns a Mock object representing the basic needs of a table

    Arguments:
        table_name {str} -- The name of the database table

    Keyword Arguments:
        columns {list} -- All the columns of the table (default: {None})
        indices {list} -- All the indices of the table (default: {None})
        foreignKeys {list} -- All the foreign keys of the table (default: {None})
        tableEngine {str} -- Table engine if required (default: {None})
        charset {str} -- Charset (default: {'utf8'})
        comment {str} -- Comment (default: {None})

    Returns:
        MagicMock -- GRT Compatible Table
    """
    table = MagicMock(
        tableEngine=tableEngine,
        defaultCharacterSetName=charset,
        columns=columns or [],
        indices=indices or [],
        foreignKeys=foreignKeys or []
    )
    table.name = table_name
    if comment is not None:
        table.comment = comment
    for c in table.columns:
        c.owner = table
    return table


def get_grt_column(column_name, table_name, sql_type, defaultValue=None, comment=None, isNotNull=0, autoIncrement=0):
    """Mock a column

    Returns a Mock object representing the basic needs of a column

    Arguments:
        column_name {str} -- The name of the column
        table_name {str} -- The name of the table (a table will be accessible at o.owner)
        sql_type {str} -- The SQL type of the column

    Keyword Arguments:
        defaultValue {str} -- Default value (default: {None})
        comment {str} -- Comment (default: {None})
        isNotNull {number} -- Is not null (default: {0})
        autoIncrement {number} -- Auto Increment (default: {0})

    Returns:
        MagicMock -- GRT Compatible Column
    """
    column = MagicMock(
        owner=get_grt_table(table_name),
        defaultValue=defaultValue,
        formattedType=sql_type,
        formattedRawType=sql_type,
        isNotNull=isNotNull,
        autoIncrement=autoIncrement
    )
    column.name = column_name
    if comment is not None:
        column.comment = comment
    return column
