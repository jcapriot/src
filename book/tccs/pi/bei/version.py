import  sys

def old_version():
    version = sys.version.replace("+","")
    version = version.split()[0].split(".")
    old = map(lambda x: int(x[0]), version) < [2, 2, 0]
    return old
