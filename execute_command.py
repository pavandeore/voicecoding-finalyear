def execute_fun(command) : 
    keyword = command.split()[0]
    remaining_words = " ".join(command.split()[1:])

    if keyword == 'exit':
        return '\nExiting Application.. '
        exit()

    if keyword == 'print':
        formated_remaining_word = "('{}')".format(remaining_words)
        print("\nOutput ->")
        return exec(keyword+formated_remaining_word)
    
    if keyword == 'assign':
        value = remaining_words.split()[0]
        variable = remaining_words.split()[3]
        formated = '{} = {}'.format(variable,value)
        print(formated)
        return exec(formated)