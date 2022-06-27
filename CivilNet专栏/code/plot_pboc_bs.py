#-*- coding: utf-8 -*-

import re
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rc("font",family="Noto Sans CJK JP")

import base64
import pandas as pd
import copy

class BS:
    def __init__(self, md_file):
        self.md_file = md_file
        self.raw_lines = None
        self.rows = []
        self.bs = {}
        self.headers = []

    def prepareData(self):
        self.prepareRows()
        self.prepareColumns()
        self.field2int()
    
    def prepareRows(self):
        lines = None
        self.rows = []
        with open(self.md_file,'r') as f:
            lines = f.readlines()
        
        lines = [line.strip() for line in lines]
        self.raw_lines = [line for line in lines if line]
        for line in self.raw_lines:
            fields = line.split('|')
            fields = [field.strip() for field in fields ]
            self.rows.append(fields)

    def prepareColumns(self):
        c = 0
        self.bs = {}
        for r,fields in enumerate(self.rows):
            for c,field in enumerate(fields):
                if '----' in field:
                    self.headers = self.rows[r-1]
                    self.bs = {header: [] for header in self.headers}
                    break
                
                if not self.bs:
                    continue
                
                self.bs[self.headers[c]].append(field.strip())
        #remove empty column
        del self.bs['']

    def field2int(self):
        for k in self.bs:
            if k == '日期':
                continue

            self.bs[k] = [float(v) if v else None for v in self.bs[k] ]

def test_col(sheet, col_header, target_name):
    for i,d in enumerate(sheet['日期']):
        total = 0
        for item in col_header:
            v = sheet[item][i]
            if v is None:
                continue
            total += v
        
        assert abs(total - sheet[target_name][i]) < 0.1,'{}: {} vs {}'.format(d,total, sheet[target_name][i])
        # print ('{}: {} vs {}'.format(d,total, sheet[target_name][i]) )


def pboc_test():
    pboc_asset = BS('../data/PBOC_Assets.md')
    pboc_liability = BS('../data/PBOC_Liabilities.md')
    pboc_asset.prepareData()
    pboc_liability.prepareData()
    #总资产等于总负债
    for x,y in zip(pboc_asset.bs['总资产'], pboc_liability.bs['总负债']):
        assert x==y,'{} should equal {}'.format(x,y)

    #资产等于各项之和
    pboc_asset__header = ['(外汇)','(货币黄金)','(其他国外资产)','对政府债权','其他存款性公司债权','其他金融性公司债权','非金融性公司债权','其他资产']
    test_col(pboc_asset.bs, pboc_asset__header, '总资产')

    pboc_liability_header = ['(货币发行)','((其他存款性公司))','((其他金融性公司))','(非金融机构存款)','不入储金存','发行债券','国外负债','政府存款','自有资金','其他负债']
    test_col(pboc_liability.bs, pboc_liability_header, '总负债')
    return pboc_asset,pboc_liability
    
 
def other_depository_test():
    other_depository_asset = BS('../data/Other_Depository_Corporations_Assets.md')
    other_depository_liability = BS('../data/Other_Depository_Corporations_Liabilities.md')
    other_depository_asset.prepareData()
    other_depository_liability.prepareData()
    #总资产等于总负债
    for x,y in zip(other_depository_asset.bs['总资产'], other_depository_liability.bs['总负债']):
        assert abs(x-y) < 0.1,'{} should equal {}'.format(x,y)

    #资产等于各项之和
    other_depository_asset_header = ['国外资产', '(准备金存款)', '(库存现金)', '对政府债权', '对央行债权', '其他存款性公司债权', '其他金融性公司债权', '非金融性公司债权', '其他居民部门债权', '其他资产']
    test_col(other_depository_asset.bs, other_depository_asset_header, '总资产')

    other_depository_liability_header = ['((企业活存))', '((企业定存))', '((居民储存))','((可转让存款))', '((其他存款))', '(其他负债)', '对央行负债', '对其他存款性公司负债', '对其他金融性公司负债', '国外负债', '债券发行', '实收资本', '其他负债']
    test_col(other_depository_liability.bs, other_depository_liability_header, '总负债')
    return other_depository_asset,other_depository_liability

def other_depository_survey_test():
    depository_survey = BS('../data/Depository_Corporations_Survey.md')
    depository_survey.prepareData()

    #资产等于各项之和
    depository_survey_header = ['国外净资产', '(政府净债权)', '(非金债权)', '(他金债权)', '((M0))', '((企业活存))', '((企业定存))', '((居民储蓄存款))', '((其他存款))', '非广存款', '债券', '实收资本', '其他（净）']
    return depository_survey

def foreign_asset_test(pboc_asset, pboc_liability,other_depository_asset,other_depository_liability,depository_survey):
    for i,d in enumerate(pboc_asset.bs['日期']):
        total_asset = pboc_asset.bs['国外资产'][i] + other_depository_asset.bs['国外资产'][i]
        total_liability = pboc_liability.bs['国外负债'][i] + other_depository_liability.bs['国外负债'][i]
        net_asset = depository_survey.bs['国外净资产'][i]

        assert abs(total_asset - total_liability - net_asset) < 0.1,'{} vs {} - {} = {}'.format(net_asset,total_asset, total_liability,total_asset - total_liability)
        #print ('{} vs {} - {} = {}'.format(net_asset,total_asset, total_liability,total_asset - total_liability))

#test pboc, other_depository, depository_survey
pboc_asset,pboc_liability = pboc_test()
other_depository_asset,other_depository_liability = other_depository_test()
depository_survey = other_depository_survey_test()
foreign_asset_test(pboc_asset, pboc_liability,other_depository_asset,other_depository_liability,depository_survey)

ax=plt.subplot()
ax.plot(pboc_liability.bs['日期'], pboc_liability.bs['国外负债'])
ax.set_ylabel('Gemfield: 央行国外负债')

plt.title("Gemfield: 央行国外负债")
ax.set_xlabel('日期')
plt.grid(True)
plt.xticks(rotation=90)
plt.show()
