import sys

age_min = 22
age_max = 60

def getIncomeGrowth(i):
    return max(0.03, 0.074 - (0.044 * i / 25))

def getInterestRate(i):
    return max(0.02, 0.0345 - (0.0145 * i / 10))

def getRetirementAge(current_age):
    return int(61 + min(9, (60 - current_age)/2.5))

def retire(age, s):
    income_2021 = 75002
    shebao_2021 = 27000
    interest_2021 = 0.0345
    if age < age_min or age > age_max:
        print('你不在考虑退休的年纪')
        return
    retirement_age = getRetirementAge(age)
    for i in range(age, retirement_age + 1):
        s = s - (income_2021+shebao_2021)
        interest_rate = 1 + getInterestRate(i-age)
        s = int(s * interest_rate)
        print("{}岁，剩余{}".format(i,s))
        if s <= 0:
            print("{}岁，钱花光了！".format(i))
            return
        
        income_abs_growth = 1 + getIncomeGrowth(i-age)
        income_2021 = income_2021 * income_abs_growth
        shebao_2021 = shebao_2021 * income_abs_growth

if len(sys.argv) < 3:
    print("Usage: {} <age> <savings>".format(sys.argv[0]))
    sys.exit(1)

age = int(sys.argv[1])
savings = int(sys.argv[2])
retire(age, savings)