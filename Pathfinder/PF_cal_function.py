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

def burst_time():
    delays = {
        # 시퀀스 등록 스킬
        'Sequence_Start': 60,
        'Sequence_End': 60-90,
        '배리어': 90,
        '에픽어드벤쳐': 90,
        '메용2': 90,
        '크리인': 90,
        '엔버': 90,
        '시드링': 90,
        '이볼브': 90,

        '템페스트': 540,
        '포세이큰': 6540,
        '얼블': 1350,
        '렐릭에볼루션': 300,
        '언바': 540,
        'Gauge': 5000,
        '평딜시작': 0
    }

    # 6차 극딜
    sequence1 = [
        'Sequence_Start', 
        '에픽어드벤쳐', '메용2', '크리인', '이볼브', '엔버', '시드링', '배리어',
        'Sequence_End',
        '템페스트', '포세이큰', '얼블', '렐릭에볼루션', '언바', '평딜시작'
    ]
    # 5차 극딜
    sequence2 = [
        'Sequence_Start', 
        '에픽어드벤쳐', '메용2', '크리인', '이볼브', '엔버', '시드링', '배리어',
        'Sequence_End',
        '템페스트', '얼블', '렐릭에볼루션', '언바', '평딜시작'
    ]

    idx = {
        '에픽어드벤쳐': 0, '메용2': 1, '크리인': 2, '엔버': 3, '시드링': 4,
        '템페스트': 5, '언바': 6, '배리어': 7, '얼블': 8,
        '렐릭에볼루션': 13, '이볼브': 14, '포세이큰': 16,
        '평딜시작': 10, 'Boss_Slayer': 11, 'Fatal_Strike': 12
    }
    
    def build_array(sequence):
        arr = np.zeros(17)
        current_time = 0
        for i, skill in enumerate(sequence):
            if skill in idx:
                arr[idx[skill]] = current_time
            current_delay = delays[skill]
            if skill == '얼블' and i + 1 < len(sequence) and sequence[i+1] == '렐릭에볼루션':
                current_delay -= 1350
            current_time += current_delay
        arr[idx['Boss_Slayer']] = arr[idx['템페스트']]
        arr[idx['Fatal_Strike']] = arr[idx['템페스트']]
        return arr
    ARRAY1 = build_array(sequence1)
    ARRAY2 = build_array(sequence2)

    return ARRAY1, ARRAY2

def apply_hyper_skills(stats, VI_level):
    SharpEyes_Duration = 30 if stats['HyperSkill'][0] == 1 else 0
    if stats['HyperSkill'][1] == 1:
        stats["Ignore_Guard"] = stats["Ignore_Guard"] + (100 - stats["Ignore_Guard"]) * 0.05
    if stats['HyperSkill'][2] == 1:
        stats['Critical_Prob'] += 5 
    Cardinal_Damage = 20 if stats['HyperSkill'][3] == 1 else 0
    if stats['HyperSkill'][4] == 1:
        Additional_Ratio = 50
        Additional_Ratio_VI = 51 + ((VI_level[5] - 1) // 3)
    else:
        Additional_Ratio = 40
        Additional_Ratio_VI = 41 + ((VI_level[5] - 1) // 3) 
    Cardinal_Attack = 6 if stats['HyperSkill'][5] == 1 else 5
    if stats['HyperSkill'][6] == 1:
        Ancient_Enchant_Boss_Damage = 71 + stats["Ability_Passive"]
    else:
        Ancient_Enchant_Boss_Damage = 51 + stats["Ability_Passive"] 
    Ancient_Enchant_Ignore_Guard = 20 if stats['HyperSkill'][7] == 1 else 0
    Enchant_Damage = 20 if stats['HyperSkill'][8] == 1 else 0
    
    return (stats, SharpEyes_Duration, Cardinal_Damage, Additional_Ratio, 
            Additional_Ratio_VI, Cardinal_Attack, Ancient_Enchant_Boss_Damage, 
            Ancient_Enchant_Ignore_Guard, Enchant_Damage)

def get_forsaken_bonus(forsaken_level):
    return [(0, 0.0), (0, 0.2), (20, 0.2), (50, 0.5)][min(3, forsaken_level // 10)]

def calc_D(pct, base_ign, Boss_Guard, stats, Damage2, Boss_Damage2, Critical_Damage2, DEX2, Attack_Ratio2, add_boss=0, add_ign=0, f_dmg=1.0):
    tot_ign = base_ign + (100 - base_ign) * add_ign / 100
    guard_pen = Boss_Guard * (1 - tot_ign / 100)
    if guard_pen < 0: guard_pen = 0       
    tot_atk = (100 + Attack_Ratio2) * stats['Real_Attack'] + stats['Attack_lumi']
    tot_stat = DEX2 + stats['STR'] / 4
    return pct * (100 + Damage2 + Boss_Damage2 + add_boss) * (135 + Critical_Damage2) * (100 - guard_pen) * tot_atk * tot_stat * f_dmg * stats['FINAL_ATTACK']

def calc_Ascent_D(pct, base_ign, Boss_Guard, ascent_stats, add_boss=0, add_ign=0, f_dmg=1.0):
    tot_ign = base_ign + (100 - base_ign) * add_ign / 100
    guard_pen = Boss_Guard * (1 - tot_ign / 100)
    if guard_pen < 0: guard_pen = 0       
    tot_atk = (100 + ascent_stats['Attack_Ratio']) * ascent_stats['Real_Attack'] + ascent_stats['Attack_lumi']
    tot_stat = ascent_stats['DEX_with_MY'] + ascent_stats['STR'] / 4
    #return pct * (100 + ascent_stats['Damage'] + ascent_stats['Boss_Damage'] + add_boss) * (135 + ascent_stats['Critical_Damage']) * (100 - guard_pen) * tot_atk * tot_stat * f_dmg * ascent_stats['FINAL_ATTACK']
    return 1/0.525 * 0.80 * pct * (100 + ascent_stats['Damage'] + ascent_stats['Boss_Damage'] + add_boss) * (135 + ascent_stats['Critical_Damage']) * (100 - guard_pen) * tot_atk * tot_stat * f_dmg * ascent_stats['FINAL_ATTACK']
    
# 최종 딜량 보정 (4*무기상수*직업보정상수*랩차보정*속성보정*포스보정*숙련도보정%10^12)
#    0.525
# 어센트 보정
#    1  

def log_array():
    skill_names = [
            "Cardinal_Blast", "Cardinal_Discharge", "Cardinal_Transition", 
            "Additional_Blast", "Additional_Discharge", "Resonance", 
            "Triple_Impact", "Raven", "Guided_Arrow", "Ultimate_Blast", 
            "Evolve_Tempest", "Obsidian_Barrier", "Relic_Unbound", "Evolve", 
            "Forsaken_Relic", "Additional_Blast_Curse_Arrow", "Forsaken_Arrow", 
            "Ancient_Fury", "Material", "Resonance2", "Assault", 
            "Hecate", "Styx", "Phlegethon", "Penetration", "CoS", "SiM", "Evolve_Orbit", "test_graph"
        ]
    state = {name: {"times_used": 0, "attacks": 0, "delay": 0, "damage": []} for name in skill_names}
    return state

def write_skill_log(total_sum, Deal_Cumulative, deal_order, state, filename='PF_log.txt'):
    final_deal = {name: Deal_Cumulative[i] for i, name in enumerate(deal_order)}
    log_targets = [
        ('템페스트', ['Evolve_Tempest']),
        ('렐릭 언바운드', ['Relic_Unbound']),
        ('옵시디언 배리어', ['Obsidian_Barrier']),
        ('얼티밋 블래스트', ['Ultimate_Blast']),
        ('포세이큰 렐릭', ['Forsaken_Relic', 'Forsaken_Arrow', 'Ancient_Fury']),
        ('엣지 오브 레조넌스', ['Resonance']),
        ('에인션트 임팩트', ['Resonance2']),
        ('콤보 어썰트', ['Assault']),
        ('카디널 블래스트', ['Cardinal_Blast']),
        ('카디널 디스차지', ['Cardinal_Discharge']),
        ('에디셔널 디스차지', ['Additional_Discharge']),
        ('에디셔널 블래스트', ['Additional_Blast', 'Additional_Blast_Curse_Arrow']),
        ('레이븐', ['Raven']),
        ('이볼브', ['Evolve', 'Evolve_Orbit']),
        ('가이디드 애로우', ['Guided_Arrow']),
        ('렐릭 마테리얼라이즈', ['Material']),
        ('솔 헤카테', ['Hecate']),
        ('스틱스', ['Styx']),
        ('플레게톤', ['Phlegethon']),
        ('렐릭 페네트레이션', ["Penetration"]),
        ('크오솔', ["CoS"]),
        ('스인미', ["SiM"]),
    ]

    ref_targets = [
        ('에디셔널 블래스트 (기본화살)', ['Additional_Blast']),
        ('에디셔널 블래스트 (저주화살)', ['Additional_Blast_Curse_Arrow']),
        ('포세이큰 렐릭 (컷신)', ['Forsaken_Relic']),
        ('포세이큰 렐릭 (마법화살)', ['Forsaken_Arrow']),
        ('포세이큰 렐릭 (고대의 분노)', ['Ancient_Fury']),
        ('이볼브: 칠흑의 궤적', ['Evolve_Orbit'])
    ]

    with open(filename, 'w', encoding='utf-8') as file:
        file.write('패스파인더 스킬 점유율\n')
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

def write_timeline_log(timeline_log, filename='timeline.txt'):
    col_map = {
        "Cardinal_Blast": "블래",
        "Cardinal_Discharge": "디차",
        "Assault": "어썰트",
        "Resonance": "레조",
        "Evolve_Tempest": "템페스트",
        "Ultimate_Blast": "얼블",
        "Relic_Unbound": "언바",
        "Obsidian_Barrier": "배리어",
        "Forsaken_Relic": "포세이큰",
        "Penetration": "어센트",
    }
    
    headers = ["Time(m:s:ms)", "블래", "디차", "어썰트", "레조", "템페스트", "얼블", "언바", "배리어", "포세이큰", "어센트"]
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\t'.join(headers) + '\n')
        for t, active_skills in timeline_log:
            mins = t // 60000
            secs = (t % 60000) // 1000
            ms = t % 1000
            time_str = f"{mins:02d}:{secs:02d}:{ms:03d}"
            
            row = [time_str]
            active_kor = {col_map[sk] for sk in active_skills if sk in col_map}
            for header in headers[1:]:
                if header in active_kor:
                    row.append('1')
                else:
                    row.append('')  
            f.write('\t'.join(row) + '\n')


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
            indices = [0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
            skill_labels = [
                "카디널 블래스트", "카디널 디스차지", "에디셔널 블래스트", "에디셔널 디스차지", "레조넌스", 
                "트리플 임팩트", "레이븐", "가이디드 애로우", "얼티밋 블래스트", 
                "템페스트", "옵시디언 배리어", "렐릭 언바운드", "이볼브", "포세이큰 렐릭",
                "에디셔널 저주화살", "포세이큰 마법화살", 
                "고대의 분노", "마테리얼", "에인션트 임팩트", "콤보 어썰트", 
                "솔 헤카테", "스틱스", "플레게톤", "렐릭 페네트레이션",
                "크오솔", "스인미", "칠흑의 궤적", "test_graph"
            ]
            colors = [
                'magenta',        # 0: 카디널 블래스트 
                'cyan',           # 1: 카디널 디스차지 
                'violet',         # 3: 에디셔널 블래스트 
                'darkturquoise',  # 4: 에디셔널 디스차지 
                'purple',         # 5: 레조넌스 
                'deepskyblue',    # 6: 트리플 임팩트 
                'navy',           # 7: 레이븐 
                'yellowgreen',    # 8: 가이디드 애로우 
                'red',            # 9: 얼티밋 블래스트 
                'plum',           # 10: 템페스트 
                'orchid',         # 11: 옵시디언 배리어 
                'deeppink',       # 12: 렐릭 언바운드 
                'thistle',        # 13: 이볼브 
                'yellow',         # 14: 포세이큰 렐릭 
                'red',            # 15: 에디셔널 저주화살 
                'blue',           # 16: 포세이큰 마법화살 
                'green',          # 17: 고대의 분노 
                'white',          # 18: 마테리얼 
                'pink',           # 19: 에인션트 임팩트 
                'lime',           # 20: 콤보 어썰트 
                'indigo',         # 21: 솔 헤카테
                'gold',           # 22: 스틱스
                'crimson',        # 23: 플레게톤
                'silver',         # 24: 렐릭 페네트레이션
                'orange',         # 25: 크오솔
                'saddlebrown',    # 26: 스인미
                'lightskyblue'    # 27: 칠흑의 궤적
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
    import matplotlib.pyplot as plt
    import numpy as np

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



