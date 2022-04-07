import re
import matplotlib.pyplot as plt
import base64

lines = None
with open('../中国每年出生人口数量.txt','r') as f:
    lines = f.read()
    lines = lines.split()

lines = [line for line in lines if line]
year_list = []
population_list = []

weights = {
            25:0.03,
            26:0.07,
            27:0.12,
            28:0.15,
            29:0.15,
            30:0.14,
            31:0.11,
            32:0.09,
            33:0.07,
            34:0.05,
            35:0.02}

target = 0
for birth_year in range(2017,2046):
    target = 0
    for line in lines:
        # print("gemfield: ",line)
        year,population = re.findall('[0-9]+', line)[:2]
        population = int(population)
        if not population:
            continue

        age = birth_year - int(year)
        
        if age in weights:
            # print("age: ",age)
            target += weights[age] * population

        year_list.append(year[-2:])
        population_list.append(population)

    print(birth_year,": ",target//2)
