import os

combined = open('urls.txt', 'w')
for dir_entry in os.listdir('.'):
    dir_entry_path = os.path.join('.', dir_entry)
    if os.path.isfile(dir_entry_path) and dir_entry[-3:] == 'txt':
        with open(dir_entry_path, 'r') as urls:
            combined.writelines(urls.readlines())
combined.close()