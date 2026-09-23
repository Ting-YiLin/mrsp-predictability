from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--groups',type=int,default=40);a=ap.parse_args();root=Path(a.out);(root/'tx').mkdir(parents=True,exist_ok=True)
    depts=['GROCERY','PRODUCE','MEAT','MEAT-PCKGD','DRUG GM','DELI','PASTRY','SEAFOOD-PCKGD']
    prows=[];weeks={w:[] for w in range(1,54)};basket=0
    for g in range(a.groups):
        pids=[str(1000000+g*10+j) for j in range(6)];dept=depts[g%len(depts)];ptype=f'SYNTH_TYPE_{g:03d}'
        for j,p in enumerate(pids):prows.append({'product_id':p,'product_type':ptype,'department':dept,'manufacturer':'SYN','brand':f'B{j}','commodity_desc':ptype,'sub_commodity_desc':ptype,'package':'X','size':'1'})
        for hh_i in range(30):
            hh=f'H{g:03d}_{hh_i:02d}'
            for e,w in enumerate([4,8,12,16,20,24,28,32,36,40,44,48,52]):
                basket+=1
                if hh_i<15:y=hh_i%2
                else:y=(hh_i+e+g)%6
                p=pids[y]
                weeks[w].append({'household_id':hh,'store_id':'S1','basket_id':str(basket),'product_id':p,'quantity':1.0,'sales_value':2.0,'retail_disc':0.0,'coupon_disc':0.0,'coupon_match_disc':0.0,'week':w,'transaction_timestamp':f'2020-01-01 00:00:{basket%60:02d}','net_price':2.0,'gross_proxy':2.0})
    pd.DataFrame(prows).to_csv(root/'products.csv',index=False)
    cols=['household_id','store_id','basket_id','product_id','quantity','sales_value','retail_disc','coupon_disc','coupon_match_disc','week','transaction_timestamp','net_price','gross_proxy']
    for w in range(1,54):pd.DataFrame(weeks[w],columns=cols).to_csv(root/'tx'/f'w{w:02d}.csv',index=False)
    print('SYNTH_CJ9_PASS',a.groups)
if __name__=='__main__':main()
