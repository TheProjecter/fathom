POSTGRES_PARAMETRES = set(['host', 'hostaddr', 'port', 'dbname', 'user', 
                          'password', 'connect_timeout', 'options', 'tty',
                          'sslmode', 'requiressl', 'sslcert', 'sslkey',
                          'sslrootcert', 'sslcrl', 'krbsrvname', 'gsslib',
                          'service'])

def get_postgres_connection_string(**kwargs):
    params = ['%s=%s' % (name, value) for name, value in list(kwargs.items()) 
                                      if name in POSTGRES_PARAMETRES]
    return ' '.join(params)
        
    
