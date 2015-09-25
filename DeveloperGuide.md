# Database object #

Database objects represent whole database schema and provide access to all other objects. Currently ` fathom ` supports three databases: **Sqlite3**, **PostgreSQL** and **MySQL**. For every database different function must be called from ` fathom ` package.

| **Database** | **function** | **arguments** |
|:-------------|:-------------|:--------------|
| Sqlite3      | ` get_sqlite3_database(path) ` | ` path ` - string with a path to **Sqlite3** database file |
| PostgreSQL   | ` get_postgresql_database(conninfo) ` | ` conninfo ` - connection string for **PostgreSQL** connection described in [documentation](http://www.postgresql.org/docs/8.1/static/libpq.html) |
| MySQL        | ` get_mysql_database(**kwargs) ` | ` kwargs ` - dictionary of parametres for **MySQL** connection described in [documentation](http://dev.mysql.com/doc/refman/5.0/en/mysql-real-connect.html) |
| Oracle       | ` get_oracle_database(user, password) ` | ` user ` - database user name, ` password ` - database user password |

There is also additional convenience function: `get_database(*args, **kwargs)` that will try to guess database type and will then call proper function from the listed above.


# Table objects #

Retrieving tables is straightforward and provided by databse attribute `tables`. It returns dictionary where keys are table names and values are table objects. For example:

```

>>> db = fathom.get_sqlite3_database('example.db')
>>> user_table = db.tables['auth_user']

```

## Columns ##

Accessing table columns is done in similar fashion through `columns` attribute. Every column object contains information about the column, like its name, type, default value and whether it can contain null values.

```

>>> username = user_table.columns['username']
>>> username.name
'username'
>>> username.type
'varchar(30)'
>>> username.default # there is none
>>> username.not_null
True

```

## Indices ##

It is possible to access all indices through `indices` attribute of Database object:

```

>>> db.indices
{'sqlite_autoindex_auth_user_1': <fathom.schema.Index object at 0xb73e6d6c>}

```

You can access columns that are encompassed by an index by using `columns` attribute and check its uniqueness through `is_unique` attribute:

```

>>> index = user_table.indices['sqlite_autoindex_auth_user_1']
>>> index.columns
('username',)
>>> index.is_unique
True
```

## Foreign keys ##

You can access foreign key constraints that are defined on a table through `foreign_keys` attribute that is a list of `ForeignKey` objects. Every `ForeignKey` object provides information about columns under constraint, referenced table and referenced columns.

```

>>> foreign_key = auth_message.foreign_keys[0]
>>> foreign_key.referenced_table
'auth_user'
>>> foreign_key.columns
('user_id',)
>>> foreign_key.referenced_columns
('id',)

```

# View objects #

Retrieving views is straightforward and provided by databse attribute `views`. It returns dictionary where keys are view names and values are views objects. For example:

```

db = fathom.get_sqlite3_database('example.db')
active_user_view = db.views['active_users']

```

View object has `columns` attribute that works exactly the same as in `Table` object.

# Procedure objects #

For those DBMS that allow stored procedures they can be easily accessed through procedures attribute. You can also check, whether database supports stored procedures:

```
>>> sqlite_db.supports_stored_procedures()
False
>>> postgres_db.supports_stored_procedures()
True
>>> fib = postgres_db.procedures['fibonacci(int4)']
```

Procedure objects provide information about arguments:

```
>>> fib.arguments
{'value': <fathom.schema.Argument object at 0xb722e7ac>}
>>> fib.arguments['value'].type
'int4'
```

Procedures provide also information about return value:

```

>>> fib.returns
'int4'

```

as well as sql body of the procedure:

```
>>> fib.sql
    BEGIN
        IF fib_for < 2 THEN
            RETURN fib_for;
        END IF;
        RETURN fib(fib_for - 2) + fib(fib_for - 1);
    END;
```


# Trigger objects #

Retrieving trigger objects id one through `triggers` attribute and provides a dictionary from trigger names to trigger objects.

```

>>> db.triggers
{'auth_user_before': <fathom.schema.Trigger at 0xb722e7ac>}

```

Each trigger provides name of the table on which it was set:

```

>>> trigger = db.triggers['auth_user_before']
>>> trigger.table
'auth_user'

```

Trigger also provides information about when it is called through attributes:
  * `when` using constants `BEFORE` and `AFTER`
  * `event` using constants `INSERT`, `UPDATE`, `DELETE`

```
>>> trigger.when == Trigger.BEFORE
True
>>> trigger.event == Trigger.INSERT
False
```