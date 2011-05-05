# different DBMSes have different take on case sensitivity; Sqlite3 is
# completely case insensitive; MySQL on the other hand is case sensitive;
# PostgreSQL and Oracle only keep identifiers case sensitive, if they are
# passed in scarecrows
CASE_SENSITIVE, CASE_SENSITIVE_QUOTED, CASE_INSENSITIVE = range(3)
CASE_SENSITIVITY = (CASE_SENSITIVE, CASE_SENSITIVE_QUOTED, CASE_INSENSITIVE)
