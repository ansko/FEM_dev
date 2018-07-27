import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint


def q860955():
    """
filenames = []
trees = []
for dirname, dirs, files in os.walk(path, topdown=True):
    for file in files:
        if file.endswith('.py'):
            filenames.append(os.path.join(dirname, file))
            if len(filenames) == 100:
                break
    """

    import os
    from itertools import islice
 
    path = '/home/anton/AspALL/Projects/'

    filenames = [
        f for f in [fname for aaa, bbb, fname in os.walk(path, topdown=True)]
            #if fname.endswith('.py')
    ]


    pprint(filenames)
    print(len(filenames))


if __name__ == '__main__':
    q860955()
