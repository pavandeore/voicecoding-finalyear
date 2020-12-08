import speech_recognition as sr

from execute_command import execute_fun

r = sr.Recognizer()
m = sr.Microphone()

try:
    print("A moment of silence, please...")
    with m as source:
        r.adjust_for_ambient_noise(source)
        while True:
            print("\nSay Command: ")
            audio = r.listen(source)
            print("Recognizing...")
            try:
                value = r.recognize_google(audio)
                command = value

                print('You said -> ' + command) 
                execute_fun(command)

            except sr.UnknownValueError:
                print("Oops! Didn't catch that")
            except sr.RequestError as e:
                print("Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
except KeyboardInterrupt:
    pass
