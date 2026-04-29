import numpy as np
import math
import os
from collections import defaultdict

def set_directory(directory, ascent):
    Total_STAT_ARRAY = np.zeros((38, 1))
    Total_IGNORE = []
    exclude_files = {'hat.txt', 'ring1.txt', 'ring2.txt', 'ring3.txt', 'ring4.txt'}
    for file in os.listdir(directory):
        if file.endswith('.txt'):
            if ascent == 1 and file in exclude_files:
                continue              
            filepath = os.path.join(directory, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = f.read().splitlines()            
            STAT_ARRAY, IGNORE = import_stat(data)
            Total_STAT_ARRAY += STAT_ARRAY 
            Total_IGNORE.append(IGNORE)
            
    return Total_STAT_ARRAY, Total_IGNORE


def import_stat(data):
    stats = defaultdict(float)
    IGNORE = []
    for line in data:
        line = line.strip()
        if line in ('MAIN', 'UPT', 'LPT', '') or line.startswith('%%') or '=' not in line:
            continue         
        k, v = line.split('=', 1)
        val = float(v) if '.' in v else int(v)
        if k == 'IGNORE':
            IGNORE.append(int(val))
        elif k == 'ALL':
            stats['DEX'] += val
            stats['STR'] += val
        elif k == 'ALL%':
            stats['DEX%'] += val
            stats['STR%'] += val
        elif k == 'WEAPON_ATTACK':
            stats['WEAPON_ATTACK'] += val
            stats['ATTACK'] += val
        else:
            stats[k] += val
    keys = [
        'STR', 'STR%', 'DEX', 'DEX%', 'LVS', 'LVD', 'ATTACK', 'ATTACK%', 'DAMAGE', 'BOSS_DAMAGE', 
        'CRI_RATE', 'CRI_DAMAGE', 'COOL', 'SYM_DEX', 'SYM_STR', 'LUMI_ATTACK', 'WEAPON_ATTACK',
        'level', 'haebang', 'Buff_duration', 'Restraint_level', 'Mer', 'Cardinal_ratio', 'Server_lag',
        'RT_ratio', 'Ability_additional_damage', 'Ability_passive', 'Ability_prob', 'Fatal_strike', 
        'Boss_slayer', 'Just_one', 'Nobless_damage', 'Nobless_boss_damage', 'Nobless_critical_damage', 
        'Nobless_ignore_guard', 'Defense_smash', 'Continuous_level', 'Soul_con'
    ]
    STAT_ARRAY = np.vstack([stats[key] for key in keys])

    return STAT_ARRAY, IGNORE
    
def cal_stat(Total_STAT_ARRAY, Total_IGNORE):
    T = Total_STAT_ARRAY
    FINAL_ATTACK = 87.70 if T[18] == 1 else 70.64  
    level = T[17]
    base_stat = 5 * level + 18
    lv_ratio = level // 9 
    NET_ATTACK = math.floor(T[6,0] * (1 + T[7,0]/100) + T[15,0])
    NET_IGNORE = 0
    for sublist in Total_IGNORE:
        for item in sublist:
            NET_IGNORE += (100 - NET_IGNORE) * item / 100
    NET_IGNORE = round(NET_IGNORE, 2)
    a = math.floor(base_stat * 1.16) + T[0,0] + T[4,0] * lv_ratio
    NET_STR = math.floor(a * (1 + T[1,0]/100) + T[14,0]) # 메용O
    NET_STR2 = math.floor((base_stat + T[0,0] + T[4,0] * lv_ratio) * (1 + T[1,0]/100) + T[14,0]) # 메용X
    NET_DEX = math.floor((4 + T[2,0] + T[5,0] * lv_ratio) * (1 + T[3,0]/100) + T[13,0])
    SGONG_MAX = math.floor(round((NET_STR * 4 + NET_DEX) * 0.01 * NET_ATTACK * 1.3) * (1 + T[8,0]/100) * (1 + FINAL_ATTACK/100))
    NET_STAT = [NET_ATTACK, NET_IGNORE, NET_STR, NET_DEX, NET_STR2, SGONG_MAX, FINAL_ATTACK]
    
    return NET_STAT, a

def get_final_stats(directory, print_property, ascent):
    Total_STAT_ARRAY, Total_IGNORE = set_directory(directory, ascent)
    NET_STAT, a = cal_stat(Total_STAT_ARRAY, Total_IGNORE)
    if ascent == 0:
        print_stat(print_property, Total_STAT_ARRAY, NET_STAT, a)
        return parse_character_stats(Total_STAT_ARRAY, NET_STAT)
    else:
        return ascent_parse_character_stats(Total_STAT_ARRAY, NET_STAT)

def parse_character_stats(Total_STAT_ARRAY, NET_STAT):
    T, N = Total_STAT_ARRAY, NET_STAT
    mer = int(T[21])
    w_atk = int(T[16,0])
    passive = int(T[26])
    prob = float(T[27]) + 7.5
    ig = N[1]
    ig += (100 - ig) * int(T[34]) / 100 # 노블방무
    ig += (100 - ig) * 0.09 # 모법 링크

    return {
        'Buff_Duration': 1 + int(T[19]) / 100,
        'Damage': int(T[8]) + int(T[31]) + 5, # 기본 + 노블 + 와헌유니온
        'Boss_Damage': int(T[9]) + int(T[32]) + int(T[25]) + 20 + 32, # 기본+노블+어빌+도핑+링크(11+9+12)
        'Ignore_Guard': ig,
        'Critical_Prob': int(T[10]),
        'Critical_Damage': int(T[11]) + int(T[33]) + 5 - 1, # 기본+노블+도핑-4차저주
        'STR_with_MY': N[2],
        'DEX': N[3],
        'Attack_Ratio': int(T[7]) + 4 + passive, # 기본 + 영메 + 어빌패시브
        'Attack': int(N[0]),
        'Attack_abs': int(T[6,0]),
        'Attack_lumi': int(T[15,0]) * 100,
        'Weapon_attack': w_atk,
        'Cool': int(T[12,0]),
        'Weapon_DEX': round(N[2] + w_atk * 4 * (1 + T[3,0] / 100)),
        'FINAL_ATTACK': 1 + N[6] / 100,
        'Restraint_level': int(T[20]),
        'Continuous_level': int(T[36]),
        'Soul_con': int(T[37]),
        'Mer': mer,
        'Server_Lag': int(T[23]),
        'Ability_Additional_Damage': int(T[25]),
        'Ability_Passive': passive,
        'Ability_Prob': prob / (1 - prob / 100),
        'Fatal_Strike': int(T[28]),
        'Boss_Slayer': int(T[29]),
        'Just_One': int(T[30]),
        'Defense_Smash': int(T[35]),
        'HyperSkill': [1, 0, 0, 1, 0, 1, 1, 1, 0],
        'MY2_STR': N[4] + 5 * (N[2] - N[4]),
        'Cool_R': 0.94 if mer == 250 else (0.95 if mer == 200 else 1.0),
        # 소울20 + 어빌패시브1랩 + 230(길축/몬파 등 버프 합산)
        'Real_Attack': int(T[6,0]) + 20 + 2 * passive + 230
    }

def ascent_parse_character_stats(Total_STAT_ARRAY, NET_STAT):
    T, N = Total_STAT_ARRAY, NET_STAT
    passive = int(T[26])
    ig = N[1]

    return {
        'Damage': int(T[8]),
        'Boss_Damage': int(T[9]) + 20, # 기본+도핑
        'Ignore_Guard': ig,
        'Critical_Damage': int(T[11]),
        'STR_with_MY': N[2],
        'DEX': N[3],
        'Attack_Ratio': int(T[7]) + passive, # 기본 + 어빌패시브
        'Attack': int(N[0]),
        'Attack_abs': int(T[6,0]),
        'Attack_lumi': int(T[15,0]) * 100,
        'FINAL_ATTACK': 1 + N[6] / 100,
        # 230(길축/몬파 등 버프 합산)
        'Real_Attack': int(T[6,0]) + 230 
    }

def print_stat(print_property, Total_STAT_ARRAY, NET_STAT, a):
    T = Total_STAT_ARRAY
    N = NET_STAT
    if print_property == 1:
        print(
            f"STR = {int(a)}\n"
            f"STR% = {round(T[1,0])}\n"
            f"DEX = {round(T[2,0])}\n"
            f"DEX% = {round(T[3,0])}\n"
            f"TOTAL STR w/ MY= {N[2]}\n"
            f"TOTAL STR w/o MY= {N[4]}\n"
            f"ATT = {round(T[6,0])}\n"
            f"ATT% = {round(T[7,0])}\n"
            f"NET ATT = {N[0]}\n"
            f"FINAL ATTACK = {N[6]}\n"
            f"DAMAGE = {round(T[8,0])}\n"
            f"BOSS DAMAGE = {round(T[9,0])}\n"
            f"IGNORE GUARD = {N[1]}\n"
            f"CRITICAL RATE = {round(T[10,0])}\n"
            f"CRITICAL DAMAGE = {round(T[11,0])}\n"
            f"COOLTIME REDUCE = {round(T[12,0])}\n"
            f"REUSE = {T[27,0] + 7.5}\n"  # 아티팩트 반영
            f"ABS DEX = {round(T[13,0])}\n"
            f"ABS STR = {round(T[14,0])}"
        )  
    elif print_property == 2:
        print(
            f"STR = {N[3]}\n"
            f"DEX(메용X) = {N[4]}\n"
            f"DEX(메용O) = {N[2]}\n"
            f"공격력 = {N[0]}\n"
            f"뒷스공 = {N[5]//10000}만 {N[5]%10000}"
        )


