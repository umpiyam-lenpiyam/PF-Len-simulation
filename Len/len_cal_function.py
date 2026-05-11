import numpy as np
import matplotlib.pyplot as plt
    
def calc_vi_factor(lvl):
    if lvl == 30: return 1.6
    if lvl == 0: return 1.0
    return 1 + (10 + 15*(lvl//10) + (lvl%10)) / 100

def T(stats, time, time_test=0):
    R, C = stats["Cool_R"], stats["Cool"]
    raw_t = max(0, 360 * R - C) * (time / 360) * 1000 if time >= 60 else max(0, time * R - C) * 1000
    return int(round(raw_t / 10) * 10)

def T2(stats, time, time_test=0):
    R, C = stats["Cool_R"], stats["Cool"]
    effective_time = time
    if C >= 5 and time == 30:
        effective_time = 24
    raw_t = max(0, 360 * R - C) * (effective_time / 360) * 1000    
    return int(round(raw_t / 10) * 10)

def seed_ring(stats):
    r_lvl = stats["Restraint_level"]
    c_lvl = stats["Continuous_level"]
    r_att, r_time = {1: (17, 9), 2: (34, 11), 3: (51, 13), 4: (68, 15), 5: (68, 20), 6: (85, 20)}.get(r_lvl, (0, 0))
    
    return {
        "Restraint_att": r_att,
        "Restraint_time": r_time,
        "Continuous_att": (2 * c_lvl + 2) if c_lvl > 0 else 0,
        "Continuous_dmg": 9 * c_lvl,
        "Soul_con": {2: 45, 3: 60}.get(stats["Soul_con"], 0)
    }

def get_special_cooldowns(stats):
    mer = stats.get('Mer', 0)
    if mer == 250:
        return 3760, 4700
    elif mer >= 200:
        return 3800, 4750
    else:
        return 4000, 5000

def burst_time():
    delays = {
        # 시퀀스 등록 스킬
        'Sequence_Start': 60,
        'Sequence_End': 60-90,
        '그여축': 90,
        '만리향': 90,
        '망혼각성': 90,
        '승화': 90,
        '바디오브스틸': 90,
        '엔버': 90,
        '시드링': 90,
        
        '일격예인': 540,
        '섬무': 5010,
        '승천': 7170,
        'SiM': 570,
        'CoS': 630,
    }
    
    # 6차 극딜
    sequence1 = [
        'Sequence_Start', 
        '그여축', '만리향', '망혼각성', '승화', '바디오브스틸', '엔버', '시드링',
        'Sequence_End',
        '일격예인', '섬무', '승천'
    ]
    # 5차 극딜
    sequence2 = [
        'Sequence_Start', 
        '그여축', '만리향', '망혼각성', '승화', '바디오브스틸', '엔버', '시드링',
        'Sequence_End',
        '일격예인', '섬무'
    ]

    idx = {
        '그여축': 1, '만리향': 2, '망혼각성': 3, '승화': 4,
        '바디오브스틸': 5, '엔버': 6, '시드링': 7, '일격예인': 8,
        '섬무': 9, '승천': 10, 'Boss_Slayer': 11, 'Fatal_Strike': 12
    }
    
    def build_array(sequence):
        arr = np.zeros(17)
        current_time = 0
        for i, skill in enumerate(sequence):
            if skill in idx:
                arr[idx[skill]] = current_time
            current_time += delays[skill]
        arr[idx['Boss_Slayer']] = arr[idx['섬무']] 
        arr[idx['Fatal_Strike']] = arr[idx['섬무']]
        return arr
    ARRAY1 = build_array(sequence1)
    ARRAY2 = build_array(sequence2)

    return ARRAY1, ARRAY2

def apply_hyper_skills(stats):
    hs = stats['HyperSkill']
    return (
        hs[0] * 20,  # 영격_damage
        hs[1] * 20,  # 영격_ignore
        hs[3] * 20,  # 선참_damage
        hs[4] * 20,  # 선참_ignore
        hs[5] * 20,  # 선참_boss
        hs[6] * 20,  # 망혼강림_damage
        hs[7] * 20   # 망혼강림_ignore
    )

def get_승천_bonus(forsaken_level):
    return [(0, 0.0), (0, 0.2), (20, 0.2), (50, 0.5)][min(3, forsaken_level // 10)]

def calc_D(pct, base_ign, Boss_Guard, stats, Damage2, Boss_Damage2, Critical_Damage2, STR2, Attack_Ratio2, add_boss=0, add_ign=0, f_dmg=1.0):
    tot_ign = base_ign + (100 - base_ign) * add_ign / 100
    guard_pen = Boss_Guard * (1 - tot_ign / 100)
    if guard_pen < 0: guard_pen = 0       
    tot_atk = (100 + Attack_Ratio2) * stats['Real_Attack'] + stats['Attack_lumi']
    tot_stat = STR2 + stats['DEX'] / 4
    return pct * (100 + Damage2 + Boss_Damage2 + add_boss) * (135 + Critical_Damage2) * (100 - guard_pen) * tot_atk * tot_stat * f_dmg * stats['FINAL_ATTACK']

def calc_Ascent_D(pct, base_ign, Boss_Guard, ascent_stats, add_boss=0, add_ign=0, f_dmg=1.0):
    tot_ign = base_ign + (100 - base_ign) * add_ign / 100
    guard_pen = Boss_Guard * (1 - tot_ign / 100)
    if guard_pen < 0: guard_pen = 0       
    tot_atk = (100 + ascent_stats['Attack_Ratio']) * ascent_stats['Real_Attack'] + ascent_stats['Attack_lumi']
    tot_stat = ascent_stats['STR_with_MY'] + ascent_stats['DEX'] / 4
    return 1/0.525 * 0.8 * pct * (100 + ascent_stats['Damage'] + ascent_stats['Boss_Damage'] + add_boss) * (135 + ascent_stats['Critical_Damage']) * (100 - guard_pen) * tot_atk * tot_stat * f_dmg * ascent_stats['FINAL_ATTACK']
    #return pct * (100 + ascent_stats['Damage'] + ascent_stats['Boss_Damage'] + add_boss) * (135 + ascent_stats['Critical_Damage']) * (100 - guard_pen) * tot_atk * tot_stat * f_dmg * ascent_stats['FINAL_ATTACK']
# 최종 딜량 보정 (4*무기상수*직업보정상수*랩차보정*속성보정*포스보정*숙련도보정%10^12)
#    0.525
# 어센트 보정
#    1  

def log_array():
    skill_names = [
            "선참", "섬무", "일격예인", "열지", "망탄", "무량겁", "심검", "망혼강림", 
            "영격", "연참", "쇄매", "화중군자", "만리향", "망혼각성", 
            "승천", "천강", "진천", "낙화", "무량겁_지속",
            "오라웨폰", "Hecate", "Styx", "Phlegethon", "CoS", "SiM", "test_graph"
        ]
    state = {name: {"times_used": 0, "attacks": 0, "delay": 0, "step": 0, "action_delay": 0, "burst_count": 0, "damage": []} for name in skill_names}
    return state

def write_skill_log(total_sum, Deal_Cumulative, deal_order, state, filename='len_log.txt'):
    final_deal = {name: Deal_Cumulative[i] for i, name in enumerate(deal_order)}
    log_targets = [
        ('매화검 본초 : 선참', ['선참']),
        ('매화검 절기 : 섬무', ['섬무']),
        ('매화검 3초식 : 일격예인', ['일격예인']),
        ('망혼검 절기 : 열지', ['열지']),
        ('망혼검 절기 : 망탄', ['망탄']),
        ('망혼검 절기 : 무량겁', ['무량겁', '무량겁_지속']),
        ('망혼검 절기 : 심검', ['심검']),
        ('망혼강림 VI', ['망혼강림']),
        ('망혼검 본초 : 영격', ['영격']),
        ('망혼검 2초식 : 연참', ['연참']),
        ('매화검 2초식 : 쇄매', ['쇄매']),
        ('화중군자', ['화중군자']),
        ('매화검 절기 : 만리향', ['만리향']),
        ('망혼각성', ['망혼각성']),
        ('창룡파천검 : 승천', ['승천']),
        ('창룡파천검 : 일매낙화-천강', ['천강']),
        ('창룡파천검 : 일매낙화-진천', ['진천']),
        ('창룡파천검 : 일매낙화-낙화', ['낙화']),
        ('오라 웨폰', ['오라웨폰']),
        ('솔 헤카테', ['Hecate']),
        ('스틱스', ['Styx']),
        ('플레게톤', ['Phlegethon']),
        ('크레스트 오브 더 솔라', ["CoS"]),
        ('스파이더 인 미러', ["SiM"]),
    ]
    ref_targets = [('무량겁_지속', ["무량겁_지속"])]
    
    with open(filename, 'w', encoding='utf-8') as file:
        file.write('렌 스킬 점유율\n')
        file.write(f"총 딜량: {(total_sum / 10**12):.9f}\n\n")
        def write_log(targets):
            sorted_targets = []
            for kor_name, keys in targets:
                skill_deal = sum(final_deal[k] for k in keys)
                skill_times = sum(state[k]["times_used"] for k in keys)
                skill_attacks = sum(state[k]["attacks"] for k in keys)
                sorted_targets.append((kor_name, skill_deal, skill_times, skill_attacks))
            sorted_targets.sort(key=lambda x: x[1], reverse=True)
            for kor_name, skill_deal, skill_times, skill_attacks in sorted_targets:
                file.write(f'{kor_name}\n')
                file.write(f"{skill_deal / total_sum * 100:.2f}%\n")
                #file.write(f"{skill_deal:.0f}\n")
                file.write(f"{int(skill_times)}\n")
                file.write(f"{int(skill_attacks)}\n\n")
        write_log(log_targets)
        file.write('참고------------------\n\n')
        write_log(ref_targets)

def draw_graph(plot_graph, deal_time, time_int, Deal_Int, Deal_Int_C, Deal_Int_CC, stats, Deviation=0):
    # plot_graph == 0 None
    #               1 Raw
    #               2 1s Resolution
    #               3 1s Resolution w/o color (왜 만들었지..?)
    #               4 데미지 상승량 평가
    #               5 빌드 별 편차 계산 
    plt.style.use('dark_background')
    if plot_graph in [2, 3]:
        fig, axs = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [1, 1]}, dpi=500)
        plt.rc('font', family='Malgun Gothic')
        plt.rcParams['axes.unicode_minus'] = False
        axs[0].set_title('Integrated (1s) Data' if plot_graph == 2 else 'Integrated (1s) Data w/o color')
        axs[1].set_xlabel('Time [s]')
        axs[0].set_ylabel('초당 데미지 [AU]')
        axs[1].set_ylabel('누적 데미지 [AU]')
        if plot_graph == 2:
            indices = list(range(26))
            skill_labels = [
                    "선참", "섬무", "일격예인", "열지", "망탄", "무량겁", "심검", "망혼강림", 
                    "영격", "연참", "쇄매", "화중군자", "만리향", "망혼각성", 
                    "승천", "천강", "진천", "낙화", "무량겁_도트딜",
                    "오라웨폰", "솔 헤카테", "스틱스", "플레게톤", "크오솔", "스인미", "test_graph"
                ]
            
            colors = [
                '#fa4685',        # 선참 
                '#ff0303',        # 섬무 
                '#f9fc2b',        # 일격예인 
                '#23914f',        # 열지 
                '#166c6e',        # 망탄 
                '#0313fc',        # 무량겁 
                '#482391',        # 심검 
                '#6b0457',        # 망혼강림 
                '#8269ff',        # 영격 
                '#5cdb95',        # 연참 
                '#dbaf6e',        # 쇄매 
                '#8de9eb',        # 화중군자 
                '#14bf08',        # 만리향 
                'yellow',         # 망혼각성 
                '#f502e9',        # 승천 
                'white',          # 천강 
                'white',          # 진천 
                'white',          # 낙화 
                '#0313fc',        # 무량겁_지속 
                'cyan',           # 오라웨폰 
                'indigo',         # 솔 헤카테
                '#f547a4',        # 스틱스
                'white',          # 플레게톤
                'orange',         # 크오솔
                'saddlebrown',    # 스인미
            ]
            
            current_bottom = np.zeros(deal_time)
            for idx, color, label in zip(indices, colors, skill_labels):
                axs[0].bar(time_int, Deal_Int[idx, :], width=0.6, color=color, bottom=current_bottom, label=label)
                current_bottom += Deal_Int[idx, :]    
            axs[0].bar(time_int, Deal_Int[-1, :], width=0.6, color='white') # Test graph
            axs[0].legend(loc='upper right', fontsize='xx-small', ncol=4, framealpha=0.3)
        elif plot_graph == 3:
            axs[0].bar(time_int, Deal_Int_C, width=1.2, color='lightskyblue')
        axs[1].bar(time_int, Deal_Int_CC, width=1, color='lightskyblue')
        x = np.linspace(0, deal_time, 100)
        y = (Deal_Int_CC[-1] / deal_time) * x
        axs[1].plot(x, y, 'k--')
        axs[1].text(0, Deal_Int_CC[-1] * 0.95, 'Total Damage:')
        axs[1].text(deal_time / 8.5, Deal_Int_CC[-1] * 0.95, f'{Deal_Int_CC[-1]:.6e}')
        max_value = np.max(Deal_Int_C)
        if stats["Fatal_Strike"] == 1: axs[0].text(30, max_value * 0.8, 'Fatal Strike', size=20, color='blue')
        if stats["Boss_Slayer"] == 1: axs[0].text(30, max_value * 0.8, 'Boss Slayer', size=20, color='blue')
        if stats["Defense_Smash"] == 1: axs[0].text(30, max_value * 0.8, 'Defense Smash', size=20, color='blue')
        
    if plot_graph == 0:
        return
    
    Deviation = 0
    if Deviation == 1:
        Deal_Int_Test_C = Deal_Int_C.reshape(-1, 5).sum(axis=1)
        Average_Deal = np.mean(Deal_Int_Test_C)
        Deviation_Deal_C = np.sum(np.abs(Deal_Int_Test_C - Average_Deal) / Average_Deal)
        plt.figure(figsize=(8, 4), dpi=500)
        plt.title('5s Data')
        plt.xlabel('Time [s]')
        plt.ylabel('Non-Cumulative Damage [AU]')
        time_5s = np.linspace(0, deal_time, num=int(deal_time/5))
        plt.bar(time_5s, Deal_Int_Test_C, width=4, color='skyblue', bottom=0)
        plt.axhline(y=Average_Deal, color='k', linestyle='dashed')
        plt.text(150, 1.7e24, f'{Deviation_Deal_C / (deal_time/5):.4f}')
        
    plt.tight_layout()    
    plt.show()
    plt.close('all')

def compare_graph(plot_graph, time_int1, Deal_Int_C1, Deal_Int_C2, Deal_Int_CC1, Deal_Int_CC2, total_sum1, total_sum2):
    if plot_graph == 4:
        plt.style.use('dark_background')
        fig, axs = plt.subplots(2, 1, figsize=(8, 8), gridspec_kw={'height_ratios': [1, 1]}, dpi=500)
        axs[0].set_title('Integrated (1s) Data w/o color')
        axs[1].set_xlabel('Time [s]')
        axs[0].set_ylabel('Non-Cumulative Damage [AU]')
        axs[1].set_ylabel('Cumulative Damage [AU]')      
        axs[0].bar(time_int1, Deal_Int_C2, width=1.2, color='royalblue') 
        axs[0].bar(time_int1, Deal_Int_C1, width=1.2, color='lightskyblue')   
        axs[1].bar(time_int1, Deal_Int_CC2, width=1, color='royalblue')
        axs[1].bar(time_int1, Deal_Int_CC1, width=1, color='lightskyblue')     
        increase_ratio = (total_sum2 / total_sum1 - 1) * 100
        axs[1].text(15, total_sum2 * 0.95, f'Increased Damage = {increase_ratio:.4f} %', size=15, color='white')
        plt.show()

    elif plot_graph == 5:
        with np.errstate(divide='ignore', invalid='ignore'):
            Deal_Int_CC3 = np.where(Deal_Int_CC1 != 0, (Deal_Int_CC1 - Deal_Int_CC2) / Deal_Int_CC1, 0)
        plt.style.use('dark_background')
        plt.figure(figsize=(6, 4), dpi=500)
        plt.fill_between(time_int1, Deal_Int_CC3, 0, where=(Deal_Int_CC3 >= 0), interpolate=True, color='yellow', alpha=0.6)
        plt.fill_between(time_int1, Deal_Int_CC3, 0, where=(Deal_Int_CC3 < 0), interpolate=True, color='deeppink', alpha=0.6)
        plt.axhline(y=0, linestyle='--', color='white')  
        plt.xlabel('Time [s]')
        plt.ylabel('Damage Difference Ratio') 
        plt.show()

