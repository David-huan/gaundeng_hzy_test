# -*- coding: utf-8 -*-
import csv, collections, random, math

path = r'f:\programming\project\gaundeng\interviews.csv'
rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
def valid(r):
    v = r['is_valid'].strip()
    return None if v == '' else int(v)
def is_pool(r):
    return r['channel'] == '员工内推' and r['department'] != '商业销售部'

# chi-square: 内推x非商销 vs 其余
def chi2(a_inv, a_n, b_inv, b_n):
    # 2x2
    o = [[a_inv, a_n-a_inv], [b_inv, b_n-b_inv]]
    n = sum(sum(r) for r in o)
    rt = [sum(r) for r in o]
    ct = [o[0][i]+o[1][i] for i in range(2)]
    x = 0.0
    for i in range(2):
        for j in range(2):
            e = rt[i]*ct[j]/n
            if e > 0: x += (o[i][j]-e)**2/e
    return x

pr = [r for r in rows if is_pool(r) and valid(r) is not None]
ot = [r for r in rows if not is_pool(r) and valid(r) is not None]
pi = sum(1 for r in pr if valid(r)==0); oi = sum(1 for r in ot if valid(r)==0)
x = chi2(pi, len(pr), oi, len(ot))
print('A池 %d 无效 %d (%.1f%%) | 其余 %d 无效 %d (%.1f%%)' % (len(pr), pi, pi/len(pr)*100, len(ot), oi, oi/len(ot)*100))
print('chi2=%.1f df=1  (临界 10.83 @ p=0.001)' % x)

# split-half
print('\n== 分半验证 (随机 50/50, 重复20次) ==')
random.seed(42)
res = []
for t in range(20):
    random.shuffle(rows)
    h1, h2 = rows[:len(rows)//2], rows[len(rows)//2:]
    rr = []
    for h in (h1, h2):
        p = [r for r in h if is_pool(r) and valid(r) is not None]
        o = [r for r in h if not is_pool(r) and valid(r) is not None]
        pi = sum(1 for r in p if valid(r)==0); oi = sum(1 for r in o if valid(r)==0)
        rr.append((len(p), pi, pi/len(p)*100 if p else 0, len(o), oi, oi/len(o)*100 if o else 0))
    res.append(rr)
import statistics
h1r = [r[0][2] for r in res]; h1o = [r[0][5] for r in res]
h2r = [r[1][2] for r in res]; h2o = [r[1][5] for r in res]
print('  半A 复筛池无效率 %.1f%% (SD %.1f)  其余 %.1f%% (SD %.1f)' % (statistics.mean(h1r), statistics.stdev(h1r), statistics.mean(h1o), statistics.stdev(h1o)))
print('  半B 复筛池无效率 %.1f%% (SD %.1f)  其余 %.1f%% (SD %.1f)' % (statistics.mean(h2r), statistics.stdev(h2r), statistics.mean(h2o), statistics.stdev(h2o)))
print('  两半差值均值 %.1f pp' % statistics.mean([abs(a-b) for a,b in zip(h1r,h2r)]))

# 商销内推 是否真的特殊：与其他部门内推比较
print('\n== 商销内推 vs 非商销内推 ==')
a = [r for r in rows if r['channel']=='员工内推' and r['department']=='商业销售部' and valid(r) is not None]
b = [r for r in rows if r['channel']=='员工内推' and r['department']!='商业销售部' and valid(r) is not None]
ai = sum(1 for r in a if valid(r)==0); bi = sum(1 for r in b if valid(r)==0)
print('  商销内推 %d/%d=%.1f%% | 非商销内推 %d/%d=%.1f%% chi2=%.1f' % (ai,len(a),ai/len(a)*100, bi,len(b),bi/len(b)*100, chi2(ai,len(a),bi,len(b))))

# 规则A vs 规则B
print('\n== 规则A(全部内推) vs 规则B(内推x非商销) ==')
for name, cond in [('A: 全部内推', lambda r: r['channel']=='员工内推'),
                   ('B: 内推x非商销', is_pool)]:
    p = [r for r in rows if cond(r) and valid(r) is not None]
    pi = sum(1 for r in p if valid(r)==0)
    allinv = sum(1 for r in rows if valid(r)==0)
    n_all = len(p)
    print('  %-16s 池=%d (%.1f%%总量) 覆盖无效=%d/%d (%.1f%%) 池无效率=%.1f%% 复筛成本=%d工时 上限收益=%d工时' % (
        name, n_all, n_all/len(rows)*100, pi, allinv, pi/allinv*100, pi/len(p)*100, n_all*12, pi*75))

# 净收益敏感性 (规则B)
print('\n== 规则B 净工时收益敏感性 (池=%d, 无效=%d) ==' % (len(pr), pi))
cost = len(pr)*12
for f in [0.2, 0.3, 0.334, 0.4, 0.5, 0.6, 0.8, 1.0]:
    save = f*pi*75
    print('  拦截率 %3.0f%% -> 节省 %6.0f 工时 - 成本 %5d 工时 = 净 %+6.0f' % (f*100, save, cost, save-cost))
be = cost/(pi*75)
print('  盈亏平衡拦截率 = %d/(%d*75) = %.1f%%' % (cost, pi, be*100))
