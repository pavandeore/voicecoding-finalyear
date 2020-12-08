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