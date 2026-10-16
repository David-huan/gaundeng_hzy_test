# -*- coding: utf-8 -*-
import csv, collections, statistics

path = r'f:\programming\project\gaundeng\interviews.csv'
rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
def valid(r):
    v = r['is_valid'].strip()
    return None if v == '' else int(v)

# 内推 x 部门 精确 (含空值)
print('== 内推 x 部门 (判定口径) ==')
tot_j = tot_i = 0
for d in ['研发部','产品运营部','客户成功部','商业销售部']:
    sub = [r for r in rows if r['channel']=='员工内推' and r['department']==d]
    nn = [r for r in sub if valid(r) is not None]
    inv = sum(1 for r in nn if valid(r)==0)
    blank = len(sub)-len(nn)
    print(f'  内推x{d}: n={len(sub):>3} 判定={len(nn):>3} 无效={inv:>3} 无效率={inv/len(nn)*100:5.1f}% 空={blank}')
    if d != '商业销售部':
        tot_j += len(nn); tot_i += inv
print(f'  合计(非商销): 判定={tot_j} 无效={tot_i} 无效率={tot_i/tot_j*100:.1f}%')

# 非内推 x 部门
print('\n== 非内推 各部门无效率 ==')
for d in ['研发部','产品运营部','商业销售部','客户成功部']:
    sub = [r for r in rows if r['channel']!='员工内推' and r['department']==d]
    nn = [r for r in sub if valid(r) is not None]
    inv = sum(1 for r in nn if valid(r)==0)
    print(f'  {d}: 判定={len(nn)} 无效={inv} 无效率={inv/len(nn)*100:.1f}%')

# resume_duration 是否只是内推的代理变量 -> 在非内推内部看
print('\n== resume_duration 分桶：分渠道组 ==')
def rb(m):
    m=float(m)
    return '<30' if m<30 else '30-44' if m<45 else '45-59' if m<60 else '60-74' if m<75 else '75+'
for gname, cond in [('员工内推', lambda r: r['channel']=='员工内推'),
                    ('其他渠道', lambda r: r['channel']!='员工内推')]:
    gg = collections.defaultdict(list)
    for r in rows:
        if cond(r): gg[rb(r['resume_duration_min'])].append(r)
    print(' ', gname)
    for b in ['<30','30-44','45-59','60-74','75+']:
        s = gg.get(b, [])
        nn=[r for r in s if valid(r) is not None]
        if not nn: continue
        inv=sum(1 for r in nn if valid(r)==0)
        print(f'    {b:<6} n={len(s):>4} 无效={inv:>3} 无效率={inv/len(nn)*100:5.1f}%')

# 其他渠道 match_score 单调性 -> 筛选阈值
print('\n== 非内推 match_score 分桶(用于阈值) ==')
gg = collections.defaultdict(list)
for r in rows:
    if r['channel']!='员工内推': gg[int(r['match_score'])].append(r)
for lo in range(0, 31, 5):
    sub=[]
    for k in range(lo, lo+5):
        sub += gg.get(k, [])
    nn=[r for r in sub if valid(r) is not None]
    if not nn: continue
    inv=sum(1 for r in nn if valid(r)==0)
    print(f'  {lo:02d}-{lo+4:02d} n={len(sub):>4} 无效={inv:>3} 无效率={inv/len(nn)*100:5.1f}%')

# 盈亏平衡
print('\n== 盈亏平衡 ==')
print('  复筛1次成本=12工时；避免1次无效面试节省75工时')
print('  盈亏平衡所需拦截率 = 12/75 = %.1f%%' % (12/75*100))
