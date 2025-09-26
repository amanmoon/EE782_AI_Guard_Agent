import eel

eel.init('build')

@eel.expose
def say_hello_from_python(name):
    """A function that can be called from the React frontend."""
    print(f"Hello from Python, {name}!")
    return f"Python says: Hello, {name}!"

eel.start('index.html', size=(800, 600), mode='chrome-app')