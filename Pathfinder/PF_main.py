from PF_set_stat import *
from PF_cal_function import *
from PF_calculate_log import *

# print (1=Detail, 2=Brief, 0=None)
print_option = 1
# compare? (1=Yes, 0= No)
compare = 0
# plot graph (0= None, 1=Raw, 2=1s Resolution, 3=1s Resolution w/o color, 4=dmg inc, 5=build comp)
plot_graph = 0

VI_level1 = [30,30,30,30,30,   30,30,30,30,30,30,26]
VI_level2 = [10,4,13,6,19,   30,27,29,30, 15, 1, 1]

directory1, directory2 = 'umpiyam', 'umpiyam'
VI_1, VI_2 = VI_level1, VI_level1
ring1, ring2 = 1, 1
time = 660

#VI_level:  0 = 템페스트
#           1 = 언바운드
#           2 = 배리어
#           3 = 얼블
#           4 = 포세이큰
#           5 = 블래스트 VI
#           6 = 디스차지 VI
#           7 = 레조넌스 VI
#           8 = 콤보 어썰트 VI
#           9 = 페네트레이션
#           10 = 솔 헤카테
#           11 = 이볼브 VI

def run_sim(label, ring, level, directory):
    if compare == 1: print(f'{label} ---------------------')
    return PF_cal_damage(plot_graph, ring, level, time, print_option, directory)

res1 = run_sim('전', ring1, VI_1, directory1)
sum1, DC1, DCC1, time_int1 = res1

if compare == 1:
    res2 = run_sim('후', ring2, VI_2, directory2)
    sum2, DC2, DCC2, time_int2 = res2
    print(f'최종뎀 상승량 = {round((sum2/sum1-1)*100, 4)}%')

if plot_graph >= 3:
    compare_graph(plot_graph, time_int1, DC1, DC2, DCC1, DCC2, sum1, sum2)        
            


        




