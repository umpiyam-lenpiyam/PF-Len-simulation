from len_set_stat import *
from len_cal_function import *
from len_calculate_log import *

# print (1=Detail, 2=Brief, 0=None)
print_option = 2
# compare? (1=Yes, 0= No)
compare = 0
# plot graph (0= None, 1=Raw, 2=1s Resolution, 3=1s Resolution w/o color, 4=dmg inc, 5=build comp)
plot_graph = 0

VI_level1 = [30,30,30,30,30,   30,30,30,30,30,30,30]
VI_level2 = [10,4,13,6,19,   30,27,29,30, 15, 1, 1]

directory1, directory2 = 'lenpiyam', 'lenpiyam'
VI_1, VI_2 = VI_level1, VI_level1
ring1, ring2 = 1, 1
time = 650

#VI_level:  0 = 만리향
#           1 = 망혼각성
#           2 = 섬무
#           3 = 심검
#           4 = 승천
#           5 = 선참 VI
#           6 = 영격 연참 VI
#           7 = 열지 망탄 무량겁 VI
#           8 = 쇄매 예인 VI
#           9 = 일매낙화
#           10 = 솔 헤카테
#           11 = 화중군자 VI

def run_sim(label, ring, level, directory):
    if compare == 1: print(f'{label} ---------------------')
    return len_cal_damage(plot_graph, ring, level, time, print_option, directory)

res1 = run_sim('전', ring1, VI_1, directory1)
sum1, DC1, DCC1, time_int1 = res1

if compare == 1:
    res2 = run_sim('후', ring2, VI_2, directory2)
    sum2, DC2, DCC2, time_int2 = res2
    print(f'최종뎀 상승량 = {round((sum2/sum1-1)*100, 4)}%')

if plot_graph >= 3:
    compare_graph(plot_graph, time_int1, DC1, DC2, DCC1, DCC2, sum1, sum2)         
            


