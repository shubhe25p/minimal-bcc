import sys

with open(sys.argv[1], 'rb') as f:
    data = f.read()
    print(f'read {len(data)} bytes')
    
