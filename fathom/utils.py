POSTGRES_PARAMETRES = set('host', 'hostaddr', 'port', 'dbname', 'user', 
                          'password', 'connect_timeout', 'options', 'tty',
                          'sslmode', 'requiressl', 'sslcert', 'sslkey',
                          'sslrootcert', 'sslcrl', 'krbsrvname', 'gsslib',
                          'service')

def postgres_connection_string(**kwargs):
    params = ['%s=%s' % (name, value) for name, value in kwargs.items() 
                                      if name in POSTGRES_PARAMETRES]
    return ' '.join(params)
        
    
