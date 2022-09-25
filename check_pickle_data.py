import pickle

with open('data_base_Беларусь.pickle', 'rb') as f:
    data = pickle.load(f)

print('Барановичи' in 'Барановичский район')
for region in data:
    for district in data[region]:
        print(district)