def execute_fun(command) : 
    keyword = command.split()[0]
    
    if keyword == 'exit':
        print('\nExiting Application.. ')
        exit()
