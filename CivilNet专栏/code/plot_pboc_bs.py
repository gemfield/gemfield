import re
import matplotlib.pyplot as plt
import base64

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
            # fields = [field for field in fields if field ]
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

    def field2int(self):
        del self.bs['']
        for k in self.bs:            
            if k == '日期':
                continue

            self.bs[k] = [float(v) if v else None for v in self.bs[k] ]
            print("k:",k)

pboc = BS('../data/Depository_Corporations_Survey.md')
pboc.prepareData()
print(pboc.headers)
print(pboc.bs['M2'])

ax=plt.subplot()
ax.plot(pboc.bs['日期'], pboc.bs['((M0))'])
ax.set_xlabel('Date')
ax.set_ylabel('M2')
plt.title("Gemfield, A CivilNet Maintainer.")
plt.show()