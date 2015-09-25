**Fathom** is **Python3** package that provides database inspection. It creates an objective model of database schema and allows you to easily retrieve information about it. Currently **Fathom** works with:
  * Sqlite3
  * PostgreSQL
  * MySQL
  * Oracle

If you wish to see **Fathom** in action you can take a look at either [Fathom-Tools](http://code.google.com/p/fathom-tools/) which provide some small database tools and utility functions or [QFathom](http://code.google.com/p/qfathom/) which is a graphical database inspection tool written using PyQt. All code is built on top of **Fathom** library.

## Example ##

Example use on sample database created by **Django** project:

```
>>> import fathom
>>> db = fathom.get_sqlite3_database('example/example.db')
>>> list(db.tables.keys())
['auth_permission', 'auth_group', 'auth_user_user_permissions', 'django_site',
'fbinteg_facebookuserprofile', 'django_content_type', 'django_session','auth_user_groups',
'decisions_vote', 'decisions_optioncomment', 'decisions_unpublishedoption', 
'django_admin_log', 'auth_group_permissions', 'decisions_decision', 
'common_temporaryfile', 'common_settings', 'decisions_decisioncomment',
'common_userprofile', 'auth_message', 'decisions_option', 'auth_user', 
'decisions_unpublisheddecision']
>>> list(db.tables['auth_user'].columns.keys())
['username', 'first_name', 'last_name', 'is_active', 'email', 
'is_superuser', 'is_staff', 'last_login', 'password', 'id', 'date_joined']
```