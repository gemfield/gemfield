import re
import matplotlib.pyplot as plt
import base64
import requests

src_url = "https://raw.githubusercontent.com/gemfield/gemfield/master/CivilNet%E4%B8%93%E6%A0%8F/%E4%B8%AD%E5%9B%BD%E6%AF%8F%E5%B9%B4%E5%87%BA%E7%94%9F%E4%BA%BA%E5%8F%A3%E6%95%B0%E9%87%8F.txt"
req = requests.get(src_url)
req = req.text

lines = req.splitlines()

lines = [line for line in lines if line]
year_list = []
population_list = []

for line in lines:
    year,population = re.findall('[0-9]+', line)[:2]
    population = int(population)
    if not population:
        continue

    year_list.append(year[-2:])
    population_list.append(population)

ax=plt.subplot()
ax.plot(year_list, population_list)
ax.set_xlabel('year')
ax.set_ylabel('population')
plt.title("Gemfield, A CivilNet Maintainer.")
plt.show()